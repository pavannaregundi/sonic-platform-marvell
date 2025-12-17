"""
Module contains an implementation of SONiC Platform Base API and
provides access to hardware watchdog
"""

import os
import fcntl
import array
import time

from sonic_platform_base.watchdog_base import WatchdogBase
from sonic_py_common import logger
from . import utils

""" timestamp storage """
WD_TIMESTAMP_FILE_PATH = "/tmp/wd_timestamp"

WD_COMMON_ERROR = -1

"""
watchdog control register value and timeout in seconds map
"""
watchdog_regval_timeout_map = {
                                0 : 10,
                                1 : 30,
                                2 : 60,
                                3 : 120,
                                4 : 180,
                                5 : 240,
                                6 : 360,
                                7 : 480
                              }

sonic_logger = logger.Logger()

class WatchdogImplBase(WatchdogBase):
    """
    Base class that implements common logic for interacting
    with watchdog using ioctl commands
    """

    def __init__(self, wd_device_path):
        """
        Open a watchdog handle
        @param wd_device_path Path to watchdog device
        """
        super(WatchdogImplBase, self).__init__()

        self.watchdog_path = wd_device_path
        self.timeout = self._gettimeout()

    def update_timestamp(self, timestamp):
        bytes_written = utils.fwrite(WD_TIMESTAMP_FILE_PATH, timestamp)
        if bytes_written == 0:
            raise IOError("Failed to update timestamp")

    def disarm(self):
        """
        Disarm the hardware watchdog

        Returns:
            A boolean, True if watchdog is disarmed successfully, False
            if not
        """
        sonic_logger.log_info(" Debug disarm watchdog ")

        try:
            self._disablewatchdog()
        except IOError:
            return False

        return True

    def _disablewatchdog(self):
        """
        Turn off the watchdog timer
        """
        file_path = self.watchdog_path + 'watchdog_enable'
        bytes_written = utils.fwrite(file_path, 0)
        if bytes_written == 0:
            raise IOError("Failed to disable watchdog")

    def _settimeout(self, seconds):
        """
        Set watchdog timer timeout
        @param seconds - timeout in seconds
        @return is the actual set timeout
        """
        reg_val = -1
        for value, timeout_s in watchdog_regval_timeout_map.items():
            if timeout_s >= seconds:
                reg_val = value
                break

        if reg_val == -1:
           reg_val = list(watchdog_regval_timeout_map.values())[-1]

        file_path = self.watchdog_path + 'watchdog_timeout'
        bytes_written = utils.fwrite(file_path, reg_val)
        if bytes_written == 0:
            raise IOError("Failed to set watchdog timeout")

        return int(timeout_s)

    def _gettimeout(self):
        """
        Get watchdog timeout
        @return watchdog timeout
        """
        file_path = self.watchdog_path + 'watchdog_timeout'
        reg_val = utils.fread_int(file_path)
        return watchdog_regval_timeout_map[reg_val]

    def _gettimeleft(self):
        """
        Get time left before watchdog timer expires
        @return time left in seconds
        """
        return (int(self.timeout - (time.time() - int(float(utils.fread_str(WD_TIMESTAMP_FILE_PATH))))))

    def arm(self, seconds):
        """
        Implements arm WatchdogBase API
        """
        sonic_logger.log_info(" Debug arm watchdog ")
        ret = WD_COMMON_ERROR
        if seconds <= 0:
            return ret
        if seconds > list(watchdog_regval_timeout_map.values())[-1]:
            return ret

        try:
            if self.timeout != seconds:
                self.timeout = self._settimeout(seconds)
            if self.is_armed():
                self._keepalive()
            else:
                self._enablewatchdog()
            ret = self.timeout
        except IOError:
            pass

        return ret

    def _enablewatchdog(self):
        """
        Turn on the watchdog timer
        """
        file_path = self.watchdog_path + 'watchdog_enable'
        bytes_written = utils.fwrite(file_path, "1")
        if bytes_written == 0:
            raise IOError("Failed to enable watchdog")

        self.update_timestamp(time.time())

    def _keepalive(self):
        """
        Keep alive watchdog timer
        """
        file_path = self.watchdog_path + 'watchdog_clear'
        bytes_written = utils.fwrite(file_path, "1")
        if bytes_written == 0:
            raise IOError("Failed to clear watchdog counter")

        self.update_timestamp(time.time())

    def is_armed(self):
        """
        Implements is_armed WatchdogBase API
        """
        file_path = self.watchdog_path + 'watchdog_enable'
        return bool(utils.fread_int(file_path))

    def get_remaining_time(self):
        """
        Implements get_remaining_time WatchdogBase API
        """
        if self.is_armed():
            return self._gettimeleft()
        else:
            return -1
