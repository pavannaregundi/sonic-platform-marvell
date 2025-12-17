#!/usr/bin/env python3

########################################################################
# D64P512T
#
# Module contains an implementation of SONiC Platform Base API and
# provides the Modules' information which are available in the platform
#
########################################################################


try:
    import os
    from sonic_platform_base.module_base import ModuleBase
    from sonic_platform.eeprom import Eeprom
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

class Module(ModuleBase):
    """ Platform-specific Module class"""

    def __init__(self, module_index):
        ModuleBase.__init__(self)
        # Modules are 1-based in this platforms
        self.index = module_index + 1

        # Initialize EEPROM
        self._eeprom = Eeprom()

    def get_name(self):
        """
        Retrieves the name of the device

        Returns:
            string: The name of the device
        """
        return "D64P512T: Module Test"

    def get_presence(self):
        """
        Retrieves the presence of the Module

        Returns:
            bool: True if Module is present, False if not
        """
        return True

    def get_model(self):
        """
        Retrieves the part number of the module

        Returns:
            string: part number of module
        """
        return self._eeprom.part_number_str()

    def get_serial(self):
        """
        Retrieves the serial number of the module

        Returns:
            string: Serial number of module
        """
        return self._eeprom.serial_str()

    def get_status(self):
        """
        Retrieves the operational status of the Module

        Returns:
            bool: True if Module is operating properly, False if not
        """
        return True

    def get_position_in_parent(self):
        """
        Retrieves 1-based relative physical position in parent device.
        Returns:
            integer: The 1-based relative physical position in parent
            device or -1 if cannot determine the position
        """
        return self.index

    def is_replaceable(self):
        """
        Indicate whether Module is replaceable.
        Returns:
            bool: True if it is replaceable.
        """
        return True

    def get_base_mac(self):
        """
        Retrieves the base MAC address for the module

        Returns:
            A string containing the MAC address in the format
            'XX:XX:XX:XX:XX:XX'
        """
        # In this platform, individual modules doesn't have MAC address
        return '00:00:00:00:00:00'

    def get_system_eeprom_info(self):
        """
        Retrieves the full content of system EEPROM information for the module

        Returns:
            A dictionary where keys are the type code defined in
            OCP ONIE TlvInfo EEPROM format and values are their corresponding
            values.
            Ex. { ‘0x21’:’AG9064’, ‘0x22’:’V1.0’, ‘0x23’:’AG9064-0109867821’,
                  ‘0x24’:’001c0f000fcd0a’, ‘0x25’:’02/03/2018 16:22:00’,
                  ‘0x26’:’01’, ‘0x27’:’REV01’, ‘0x28’:’AG9064-C2358-16G’}
        """
        return self._eeprom.system_eeprom_info()

    def get_description(self):
        return "D64P512T"

    def get_slot(self):
        return 1

    def get_type(self):
        return self.MODULE_TYPE_SUPERVISOR

    def get_oper_status(self):
        # TODO: Implement the following modes
        #  - MODULE_STATUS_POWERED_DOWN
        #  - MODULE_STATUS_PRESENT
        #  - MODULE_STATUS_FAULT
        return self.MODULE_STATUS_ONLINE

    def get_maximum_consumed_power(self):
        # TODO: add power consumption to various skus
        return 3000.0

    def is_midplane_reachable(self):
        return True

    def get_midplane_ip(self):
        # TODO: will this work from the linecard side? comment is not that clear
        return "127.100.1.1"

    def reboot(self, reboot_type):
        # TODO: implement reboot mechanism
        return True
