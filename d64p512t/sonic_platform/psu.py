#!/usr/bin/env python


try:
    from sonic_platform_pddf_base.pddf_psu import PddfPsu
    from sonic_platform.psu_fru import PsuFru
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")


class Psu(PddfPsu):
    """PDDF Platform-Specific PSU class"""

    def __init__(self, index, pddf_data=None, pddf_plugin_data=None):
        PddfPsu.__init__(self, index, pddf_data, pddf_plugin_data)
        self.psu_fru = PsuFru(self.psu_index)
        self.pddf_data = pddf_data

    # Provide the functions/variables below for which implementation is to be overwritten
    def get_status(self):
        """
        Retrieves the operational status of the device

        Returns:
            A boolean value, True if device is operating properly, False if not
        """
        device = "PSU{}".format(self.psu_index)
        output = self.pddf_obj.get_attr_name_output(device, "psu_power_good")
        if not output:
            return False

        mode = output['mode']
        status = output['status']

        vmap = self.plugin_data['PSU']['psu_power_good'][mode]['valmap']
        if status.rstrip('\n') in vmap:
            voltage_output = self.pddf_obj.get_attr_name_output(device, "psu_v_out")
            if not voltage_output:
                return False
            if float(voltage_output['status']) == 0:
                return False
            else:
                return vmap[status.rstrip('\n')]
        else:
            return False

    def get_psu_status(self):
        """
        Retrieves the status of PSU
        Returns:
            A boolean, True if PSU has stablized its output voltages and passed all
            its internal self-tests, False if not.
        """
        return self.get_powergood_status()

    def get_revision(self):
        """
        Retrieves revision number of PSU
        Returns:
            A revision number,
        """
        device = "PSU{}".format(self.psu_index)
        output = self.pddf_data.get_attr_name_output(device, "psu_revision")
        if not output:
            return None

        revision = output['status']
        if revision == "":
            return "NA"
        else:
            return revision

    def get_capacity(self):
        """
        Retrieves the maximum supplied power by PSU (or PSU capacity)
        Returns:
            A float number, the maximum power output in Watts.
            e.g. 1200.1
        """
        return self.get_maximum_supplied_power()

    def get_maximum_supplied_power(self):
        """
        Retrieves the maximum supplied power by PSU

        Returns:
            A float number, the maximum power output in Watts.
            e.g. 1200.1
        """
        return 3000.0

    def get_voltage_low_threshold(self):
        """
        Returns PSU low threshold in Volts
        """
        low_threshold = 11.4
        return float(low_threshold)

    def get_voltage_high_threshold(self):
        """
        Returns PSU high threshold in Volts
        """
        high_threshold = 12.6
        return float(high_threshold)
