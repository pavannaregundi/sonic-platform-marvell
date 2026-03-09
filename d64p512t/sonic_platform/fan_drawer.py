#!/usr/bin/env python
import os
try:
    from sonic_platform_pddf_base.pddf_fan_drawer import PddfFanDrawer
    from . import utils
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

STATUS_NA = "N/A"
CHASSIS_STATUS_FILE_PATH = "/sys/kernel/d64p512t_fpga/"

class FanDrawer(PddfFanDrawer):
    """PDDF Platform-Specific Fan-Drawer class"""

    def __init__(self, tray_idx, pddf_data=None, pddf_plugin_data=None):
        # idx is 0-based
        PddfFanDrawer.__init__(self, tray_idx, pddf_data, pddf_plugin_data)
        self.fantrayindex = tray_idx
        self.fan_fru_id_list =   [ 1,
                                   2,
                                   3,
                                   4]
    # Provide the functions/variables below for which implementation is to be overwritten
    def get_model(self):
        """
        Retrieves the part number of the FAN
        Returns:
            string: Part number of FAN
        """
        return self._fan_list[0].get_model()

    def get_serial(self):
        """
        Retrieves the serial number of the FAN
        Returns:
            string: Serial number of FAN
        """
        return self._fan_list[0].get_serial()

    def get_maximum_consumed_power(self):
        """
        Retrives the maximum power drawn by Fan Drawer

        Returns:
            A float, with value of the maximum consumable power of the
            component.
        """
        return 2749.5


    def get_status_led(self):
        """
        Gets the state of the Fan status LED

        Returns:
            A string, one of the predefined STATUS_LED_COLOR_* strings.
        """
        if not self.get_presence():
            return STATUS_NA

        file_path = CHASSIS_STATUS_FILE_PATH + 'fandrawer_led_trigger'
        read_data = utils.fread_str(file_path)

        reg_val = int(read_data.split("\n\n")[0], 16)

        # Mask the requested led fandrawer stream
        led_stream_value_mask = 0xf << (4 * self.fantrayindex)
        led_strem_value = (reg_val & led_stream_value_mask) >> (4 * self.fantrayindex)

        if (led_strem_value & 0x1) == 0x1:
            led_color = "Red"
        elif (led_strem_value & 0x2) == 0x2:
            led_color = "Green"
        elif (led_strem_value & 0x3) == 0x0:
            led_color = "Off"

        if (led_strem_value & 0x4) == 0x4:
            led_color += ", Blinking"
        else:
            led_color += ", Solid"

        return led_color

    def set_status_led(self, color):
        """
        Sets the state of the Fan status LED

        Returns:
            A string, one of the predefined STATUS_LED_COLOR_* strings.
        """
        if not self.get_presence():
            return STATUS_NA

        file_path = CHASSIS_STATUS_FILE_PATH + 'fandrawer_led_trigger'
        read_data = utils.fread_str(file_path)

        reg_val = int(read_data.split("\n\n")[0], 16)

        # Mask the requested led fandrawer stream
        led_stream_value_mask = 0xf << (4 * self.fantrayindex)
        led_stream_value = (reg_val & led_stream_value_mask) >> (4 * self.fantrayindex)
        led_stream_value_cache = led_stream_value

        #import pdb; pdb.set_trace()
        if color.lower() == "blink":
            led_stream_value |= (1 << 2)
        elif color.lower() == "solid":
            led_stream_value &= ~(1 << 2)
        elif color.lower() == "red":
            led_stream_value &= ~(1 << 1)
            led_stream_value |= 1
        elif color.lower() == "green":
            led_stream_value &= ~(1 << 0)
            led_stream_value |= (1 << 1)
        elif color.lower() == "off":
            led_stream_value &= ~(3 << 0)
        else:
            print("Invalid operation requested...")
            return False

        if led_stream_value != led_stream_value_cache:
            reg_val &= ~(led_stream_value_mask)
            reg_val |= (led_stream_value << (4 * self.fantrayindex))
            if (0 == utils.fwrite(file_path, reg_val)):
                print("Failed to set fan drawer led stream...")
                return False
            else:
                return True

        print("No change...")
        return True
