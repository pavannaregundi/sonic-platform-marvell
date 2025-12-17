#!/usr/bin/env python

import os

try:
    from sonic_platform_pddf_base.pddf_fan import PddfFan
    from sonic_platform.psu_fru import PsuFru
    from sonic_py_common.general import getstatusoutput_noshell, getstatusoutput_noshell_pipe
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

IPMI_RAW_ID = 0x38
IPMI_RAW_WRITE = 0x3
FANS_PER_FANTRAY = 2

FAN_DIRECTION_INTAKE = "intake"
FAN_DIRECTION_EXHAUST = "exhaust"
FAN_DIRECTION_NOT_APPLICABLE = "N/A"
STATUS_NA = "N/A"

class Fan(PddfFan):
    """PDDF Platform-Specific Fan class"""

    def isDockerEnv(self):
        num_docker = 0
        with open('/proc/self/cgroup', 'r') as f:
            num_docker = f.read().count(":/docker")
        if num_docker > 0:
            return True
        else:
            return False

    def __init__(self, tray_idx, fan_idx=0, pddf_data=None, pddf_plugin_data=None, is_psu_fan=False, psu_index=0):
        # idx is 0-based
        PddfFan.__init__(self, tray_idx, fan_idx, pddf_data, pddf_plugin_data, is_psu_fan, psu_index)

        self.tray_idx = tray_idx
        self.fan_psu_index = psu_index
        # FAN ID: 1 ~ 4, FAN DEVICE ADDRESS - FAN1: 0x4c, FAN2: 0x4c, FAN3: 0x2d, FAN4: 0x2d
        self.fan_dev_addr_list = [ 0x4c,
                                   0x4c,
                                   0x2d,
                                   0x2d]

        # FAN ID: 1 ~ 4, FAN I2C BUS - FAN1: 0x2, FAN2: 0x2, FAN3: 0x2, FAN4: 0x2
        self.fan_i2c_bus_list = [ 2,
                                  2,
                                  2,
                                  2]

        # FAN ID: 1 ~ 4
        # FAN PWM OFFSET - FanTray1-Fan1: 0x30
        #                  FanTray1-Fan2: 0x40
        #                  FanTray2-Fan1: 0x50
        #                  FanTray2-Fan2: 0x60
        #                  FanTray3-Fan1: 0x30
        #                  FanTray3-Fan2: 0x40
        #                  FanTray4-Fan1: 0x50
        #                  FanTray4-Fan2: 0x60
        self.fan_pwm_offset_list = [ 0x30,
                                     0x40,
                                     0x50,
                                     0x60,
                                     0x30,
                                     0x40,
                                     0x50,
                                     0x60]


    # Provide the functions/variables below for which implementation is to be overwritten
    # Since psu_fan airflow direction cant be read from sysfs, it is fixed as 'F2B' or 'intake'
    def get_model(self):
        """
        Retrieves the model number (or part number) of the Fan

        Returns:
            string: Model/part number of Fan
        """
        if self.is_psu_fan:
            return STATUS_NA

        command = ""
        if self.isDockerEnv():
            command = ("ipmitool fru print {} | grep 'Product Part Number' | awk -F' ' '{{print $5}}'").format(self.tray_idx+1)
        else:
            command = ("sudo ipmitool fru print {} | grep 'Product Part Number' | awk -F' ' '{{print $5}}'").format(self.tray_idx+1)

        try:
            p = os.popen(command)
            model_str = p.read().rstrip()
            p.close()
        except IOError:
            raise SyntaxError

        if model_str != '':
            return model_str

        return STATUS_NA

    def get_serial(self):
        """
        Retrieves the serial number of the Fan

        Returns:
            string: Serial number of Fan
        """
        if self.is_psu_fan:
            return STATUS_NA

        command = ""
        if self.isDockerEnv():
            command = ("ipmitool fru print {} | grep 'Product Serial' | awk -F' ' '{{print $4}}'").format(self.tray_idx+1)
        else:
            command = ("sudo ipmitool fru print {} | grep 'Product Serial' | awk -F' ' '{{print $4}}'").format(self.tray_idx+1)

        try:
            p = os.popen(command)
            serial_str = p.read().rstrip()
            p.close()
        except IOError:
            raise SyntaxError

        if serial_str != '':
            return serial_str

        return STATUS_NA

    def get_direction(self):
        """
        Retrieves the fan airflow direction
        Returns:
            A string, either FAN_DIRECTION_INTAKE or FAN_DIRECTION_EXHAUST
            depending on fan direction

        Notes:
            - Forward/Exhaust : Air flows from Port side to Fan side.
            - Reverse/Intake  : Air flows from Fan side to Port side.
        """
        if self.is_psu_fan:
            # Two types of PSU modules are supported by D64P512T.
            # TBD : Fix ipmitool cli
            return FAN_DIRECTION_NOT_APPLICABLE
        else:
            # The fan module is only capable of exhaust direction on D64P512T.
            return FAN_DIRECTION_EXHAUST

    def get_speed_tolerance(self):
        """
        Retrieves the speed tolerance of the fan

        Returns:
        An integer, the percentage of variance from target speed which is
        considered tolerable
        """
        return int(self.plugin_data['FAN']['FAN_SPEED_TOLERANCE_PERCENTAGE'])

    def get_max_speed(self):
        """
        Retrieves the max speed

        Returns:
            An Integer, the max speed
        """
        if self.is_psu_fan:
            psu_fru = PsuFru(self.fan_psu_index-1)
            max_speed = int(self.plugin_data['PSU']['valmap']['PSU_FAN_MAX_SPEED_RPM'])
        else:
            if self.fan_index % 2 != 0:
                max_speed = int(self.plugin_data['FAN']['FAN_FRONT_MAX_SPEED_RPM']) + int(int(self.plugin_data['FAN']['FAN_FRONT_MAX_SPEED_RPM']) * self.get_speed_tolerance() / 100)
            else:
                max_speed = int(self.plugin_data['FAN']['FAN_REAR_MAX_SPEED_RPM']) + int(int(self.plugin_data['FAN']['FAN_REAR_MAX_SPEED_RPM']) * self.get_speed_tolerance() / 100)

        return max_speed

    def get_speed(self):
        """
        Retrieves the speed of fan as a percentage of full speed
        Returns:
            An integer, the percentage of full fan speed
        """

        if not self.get_presence():
            return int(0)

        if self.is_psu_fan: # psu fan speed
            FAN_MAX_SPEED_RPM = int(self.plugin_data['PSU']['PSU_FAN_MAX_SPEED_RPM'])
            try:
                attr_name = "psu_fan1_speed_rpm"
                fru_name = "PSU" + str(self.fan_psu_index)
                output = self.pddf_obj.get_attr_name_output(fru_name, attr_name)
                if not output:
                    return int(0)

                speed = int(float(output['status']))
                percentage = int((speed * 100) / FAN_MAX_SPEED_RPM)

                return int(percentage)
            except IOError:
                raise SyntaxError
        else: # fantray speed
            fan_id = (self.tray_idx  * FANS_PER_FANTRAY) + self.fan_index
            attr_name = "fan" + str(fan_id) + "_input"
            output = self.pddf_obj.get_attr_name_output("FAN-CTRL", attr_name)
            if not output:
                return int(0)

            speed = int(float(output['status']))
            percentage = int((speed * 100) / int(self.get_max_speed()))

            return int(percentage)

    def get_target_speed(self):
        """
        Retrieves the target (expected) speed of the fan
        Returns:
            An integer, the percentage of full fan speed, in the range 0 (off)
                 to 100 (full speed)
        """

        return self.get_speed()

    def get_status(self):
        """
        Retrieves the fan state
        Returns:
            A boolean, the state of fan, when not present should return True.
            when present, read fan state using ipmitool and take action
        """
        if self.is_psu_fan:
            return True
        else:
            if self.get_presence():
                fan_id = (self.tray_idx  * FANS_PER_FANTRAY) + self.fan_index
                attr_name = "fan" + str(fan_id) + "_fault"
                output = self.pddf_obj.get_attr_name_output("FAN-CTRL", attr_name)
                if not output:
                    return False

                mode = output['mode']
                state_val = output['status'].rstrip()

                vmap = self.plugin_data['FAN']['state'][mode]['valmap']

                if state_val in vmap:
                    status = vmap[state_val]
                else:
                    status = False
                return status
            else:
                return True

    def set_speed(self, speed):
        """
        Set fan speed to expected value
        Args:
            speed: An integer, the percentage of full fan speed to set fan to,
                   in the range 0 (off) to 100 (full speed)
        Returns:
            bool: True if set success, False if fail.
        """
        # Users may find Fan speed being constantly modified by BMC
        if self.is_psu_fan:
            return False
        else:
            fan_speed_pwm = int(speed / 100 * 255)
            fan_id = (self.tray_idx  * FANS_PER_FANTRAY) + self.fan_index

            raw_id = hex(IPMI_RAW_ID)
            raw_act = hex(IPMI_RAW_WRITE)
            dev_bus = hex(self.fan_i2c_bus_list[self.tray_idx])
            dev_addr = hex(self.fan_dev_addr_list[self.tray_idx])
            reg_offset = hex(self.fan_pwm_offset_list[self.fan_index])
            reg_data = hex(fan_speed_pwm)

            # IPMI Command Format : ipmitool raw [raw_id] [raw_act] [dev_bus] [dev_addr] [reg_offset] [reg_data]
            command = ""
            if self.isDockerEnv():
                command = "ipmitool raw {} {} {} {} {} {}".format(raw_id, raw_act, dev_bus, dev_addr, reg_offset, reg_data)
            else:
                command = "sudo ipmitool raw {} {} {} {} {} {}".format(raw_id, raw_act, dev_bus, dev_addr, reg_offset, reg_data)

            try:
                p = os.popen(command)
                model_str = p.read().rstrip()
                p.close()
                return True
            except IOError:
                raise SyntaxError
        return False
