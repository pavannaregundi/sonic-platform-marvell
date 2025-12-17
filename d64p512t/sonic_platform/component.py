#############################################################################
#
# Component contains an implementation of SONiC Platform Base API and
# provides the components firmware management function
#
#############################################################################

try:
    import subprocess
    import os
    import fcntl
    import array
    import re
    from sonic_platform_base.component_base import ComponentBase
    from sonic_py_common import logger
    from . import utils
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

BIOS_VERSION_PATH = "/sys/class/dmi/id/bios_version"
SYSSTATUS_FILE_PATH = "/sys/kernel/pddf/devices/sysstatus/sysstatus_data/"
CHASSIS_STATUS_FILE_PATH = "/sys/kernel/d64p512t_fpga/"

COMPONENT_LIST= [
   ("BIOS", "Performs initialization of hardware components during booting"),
   ("CPU CPLD", "Used for managing the CPU power sequence and CPU states"),
   ("SSD", "Solid State Drive that stores data persistently"),
   ("SysFPGA", "Used to control and collect signals from peripheral device to notice CPU/BMC chip"),
   ("BMC", "Platform management controller for on-board temperature monitoring,in-chassis power, Fan and LED control"),
   ("Port CPLD-A", "Used to control and collect signals of front panel ports (1 - 32)"),
   ("Port CPLD-B", "Used to control and collect signals of front panel ports (33 - 64)")
]

class Component(ComponentBase):
    """Platform-specific Component class"""
    DEVICE_TYPE = "component"

    def isDockerEnv(self):
        num_docker = 0
        with open('/proc/self/cgroup', 'r') as f:
            num_docker = f.read().count(":/docker")
        if num_docker > 0:
            return True
        else:
            return False

    def __init__(self, component_index=0):
        self.index = component_index
        self.name = self.get_name()

    def _get_bios_version(self):
        # Retrieves the BIOS firmware version
        return subprocess.check_output(
             ['dmidecode', '-s', 'bios-version']).decode('utf-8').strip()

    def _get_fpga_version(self):
        # FPGA Module CODE Revision Register
        file_path = CHASSIS_STATUS_FILE_PATH + 'sys-fpga-revision'
        read_data = utils.fread_str(file_path)

        reg_val = int(read_data.split("\n\n")[0], 16)
        fpga_version = reg_val & 255

        return hex(fpga_version)

    def _get_bmc_version(self):
        # BMC component firmware version
        if self.isDockerEnv():
            return subprocess.check_output(['ipmitool', 'raw', '0x32', '0x8f', '0x08', '0x01']).decode('utf-8').strip()
        else:
            return subprocess.check_output(['sudo', 'ipmitool', 'raw', '0x32', '0x8f', '0x08', '0x01']).decode('utf-8').strip()

    def _get_cpu_cpld_version(self):
        file_path = SYSSTATUS_FILE_PATH + 'cpu_cpld_version'
        reg_val = utils.fread_int(file_path)
        return hex(reg_val)

    def _get_port_cpld_a_version(self):
        file_path = SYSSTATUS_FILE_PATH + 'cpld_a_version'
        reg_val = utils.fread_int(file_path)
        return hex(reg_val)

    def _get_port_cpld_b_version(self):
        file_path = SYSSTATUS_FILE_PATH + 'cpld_b_version'
        reg_val = utils.fread_int(file_path)
        return hex(reg_val)

    def _get_ssd_version(self):
        val = 'NA'
        try:
            ssd_ver = subprocess.check_output(['ssdutil', '-v'],
                                              stderr=subprocess.STDOUT, text=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass
        else:
            version = re.search(r'Firmware\s*:(.*)',ssd_ver)
            if version:
                val = version.group(1).strip()

        return val

    def get_name(self):
        """
        Retrieves the name of the component
         Returns:
            A string containing the name of the component
        """
        return COMPONENT_LIST[self.index][0]

    def get_description(self):
        """
        Retrieves the description of the component
            Returns:
            A string containing the description of the component
        """
        return COMPONENT_LIST[self.index][1]

    def get_firmware_version(self):
        """
        Retrieves the firmware version of module
        Returns:
            string: The firmware versions of the module
        """
        fw_version = None

        if self.name == "BIOS":
            fw_version = self._get_bios_version()
        elif "SysFPGA" in self.name:
            fw_version = self._get_fpga_version()
        elif "BMC" in self.name:
            fw_version = self._get_bmc_version()
        elif "SSD" in self.name:
            fw_version = self._get_ssd_version()
        elif "CPU CPLD" in self.name:
            fw_version = self._get_cpu_cpld_version()
        elif "Port CPLD-A" in self.name:
            fw_version = self._get_port_cpld_a_version()
        elif "Port CPLD-B" in self.name:
            fw_version = self._get_port_cpld_b_version()
        else:
            sonic_logger.log_info("Invalid Component !!!")

        return fw_version

    def install_firmware(self, image_path):
        """
        Installs firmware to the component

        Args:
            image_path: A string, path to firmware image

        Returns:
            A boolean, True if install was successful, False if not
        """
        return False

    def update_firmware(self, image_path):
        """
        Updates firmware of the component

        This API performs firmware update: it assumes firmware installation and loading in a single call.
        In case platform component requires some extra steps (apart from calling Low Level Utility)
        to load the installed firmware (e.g, reboot, power cycle, etc.) - this will be done automatically by API

        Args:
            image_path: A string, path to firmware image

        Raises:
            RuntimeError: update failed
        """
        return True

    def get_presence(self):
        """
        Retrieves the presence of the component
        Returns:
            bool: True if  present, False if not
        """
        return True

    def get_model(self):
        """
        Retrieves the part number of the component
        Returns:
            string: Part number of component
        """
        return 'NA'

    def get_serial(self):
        """
        Retrieves the serial number of the component
        Returns:
            string: Serial number of component
        """
        return 'NA'

    def get_status(self):
        """
        Retrieves the operational status of the component
        Returns:
            bool: True if component is operating properly, False if not
        """
        return True

    def get_position_in_parent(self):
        """
        Retrieves 1-based relative physical position in parent device.
        Returns:
            integer: The 1-based relative physical position in parent
            device or -1 if cannot determine the position
        """
        return -1

    def is_replaceable(self):
        """
        Indicate whether component is replaceable.
        Returns:
            bool: True if it is replaceable.
        """
        return False

    def get_available_firmware_version(self, image_path):
        """
        Retrieves the available firmware version of the component

        Note: the firmware version will be read from image

        Args:
            image_path: A string, path to firmware image

        Returns:
            A string containing the available firmware version of the component
        """
        avail_ver = None
        return avail_ver if avail_ver else "NA"
