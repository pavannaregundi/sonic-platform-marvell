from sonic_platform_base.sonic_thermal_control.thermal_action_base import ThermalPolicyActionBase
from sonic_platform_base.sonic_thermal_control.thermal_json_object import thermal_json_object
from .thermal_infos import ChassisInfo
from .helper import APIHelper
from sonic_py_common import logger
import time


@thermal_json_object('thermal_control.control')
class ControlThermalAlgoAction(ThermalPolicyActionBase):
    """
    Action to control the thermal control algorithm
    """
    # JSON field definition
    JSON_FIELD_STATUS = 'status'

    def __init__(self):
        self.status = True

    def load_from_json(self, json_obj):
        """
        Construct ControlThermalAlgoAction via JSON. JSON example:
            {
                "type": "thermal_control.control"
                "status": "true"
            }
        :param json_obj: A JSON object representing a ControlThermalAlgoAction action.
        :return:
        """
        if ControlThermalAlgoAction.JSON_FIELD_STATUS in json_obj:
            status_str = json_obj[ControlThermalAlgoAction.JSON_FIELD_STATUS].lower()
            if status_str == 'true':
                self.status = True
            elif status_str == 'false':
                self.status = False
            else:
                raise ValueError('Invalid {} field value, please specify true of false'.
                                 format(ControlThermalAlgoAction.JSON_FIELD_STATUS))
        else:
            raise ValueError('ControlThermalAlgoAction '
                             'missing mandatory field {} in JSON policy file'.
                             format(ControlThermalAlgoAction.JSON_FIELD_STATUS))

    def execute(self, thermal_info_dict):
        """
        Disable thermal control algorithm
        :param thermal_info_dict: A dictionary stores all thermal information.
        :return:
        """
        if ChassisInfo.INFO_NAME in thermal_info_dict:
            chassis_info_obj = thermal_info_dict[ChassisInfo.INFO_NAME]
            chassis = chassis_info_obj.get_chassis()
            thermal_manager = chassis.get_thermal_manager()
            thermal_control_disable_path = '/tmp/thermal_control_disable'
            if self.status == False:
                APIHelper().write_txt_file(thermal_control_disable_path,
                                       str(self.status))
            else:
                cmd = 'rm -f ' + thermal_control_disable_path
                APIHelper().run_command(cmd);

            time.sleep(1)


@thermal_json_object('switch.power_cycling')
class SwitchPolicyAction(ThermalPolicyActionBase):
    """
    Base class for thermal action. Once all thermal conditions in a thermal policy are matched,
    all predefined thermal action will be executed.
    """

    def execute(self, thermal_info_dict):
        """
        Take action when thermal condition matches. For example, power cycle the switch.
        :param thermal_info_dict: A dictionary stores all thermal information.
        :return:
        """
        thermal_overload_position_path = '/tmp/thermal_overload_position'
        thermal_overload_position = APIHelper().read_one_line_file(
            thermal_overload_position_path)

        cmd = 'bash /usr/share/sonic/platform/thermal_overload_control.sh {}'.format(
            thermal_overload_position)
        APIHelper().run_command(cmd)

@thermal_json_object('fan.all.set_speed')
class ControlFanSpeedAlgoAction(ThermalPolicyActionBase):
    """
    Action to control the fan speed control algorithm
    """
    # JSON field definition
    JSON_FIELD_SPEED = 'speed'

    def __init__(self):
        self.speed = 60

    def load_from_json(self, json_obj):
        """
        Construct ControlFanSpeedAlgoAction via JSON. JSON example:
            {
                "type": "fan.all.set_speed"
                "speed": "100"
            }
        :param json_obj: A JSON object representing a ControlFanSpeedAlgoAction action.
        :return:
        """
        if ControlFanSpeedAlgoAction.JSON_FIELD_SPEED in json_obj:
            speed = float(json_obj[ControlFanSpeedAlgoAction.JSON_FIELD_SPEED])
            if speed < 0 or speed > 100:
                raise ValueError('ControlFanSpeedAlgoAction invalid speed value {} in JSON policy file, valid value should be [0, 100]'.
                                 format(speed))
            self.speed = float(json_obj[ControlFanSpeedAlgoAction.JSON_FIELD_SPEED])
        else:
            raise ValueError('ControlFanSpeedAlgoAction '
                             'missing mandatory field {} in JSON policy file'.
                             format(ControlFanSpeedAlgoAction.JSON_FIELD_SPEED))

    def execute(self, thermal_info_dict):
        """
        Fan speed control algorithm
        :param thermal_info_dict: A dictionary stores all thermal information.
        :return:
        """
        if ChassisInfo.INFO_NAME in thermal_info_dict:
            chassis_info_obj = thermal_info_dict[ChassisInfo.INFO_NAME]
            chassis = chassis_info_obj.get_chassis()
            fan_list = chassis.get_all_fans()
            for fan in fan_list:
                if True == fan.get_presence():
                    fan.set_speed(self.speed)

@thermal_json_object('thermal.all.log_alarm')
class ThermalOverThresholdLogAction(ThermalPolicyActionBase):
    """
    Action to log alarm for thermal for crossing threshold values
    """
    # JSON field definition
    JSON_FIELD_ALARM_TYPE = 'alarm_type'

    def __init__(self):
        self.alarm_type_prefix = ""

    def load_from_json(self, json_obj):
        """
        Construct ThermalOverThresholdLogAction via JSON. JSON example:
            {
                "type": "thermal.all.log_alarm"
                "alarm_type": "Major"
            }
        :param json_obj: A JSON object representing a ThermalOverThresholdLogAction action.
        :return:
        """
        if ThermalOverThresholdLogAction.JSON_FIELD_ALARM_TYPE in json_obj:
            alarm_type = json_obj[ThermalOverThresholdLogAction.JSON_FIELD_ALARM_TYPE]
            if len(alarm_type) == 0:
                raise ValueError('ThermalOverThresholdLogAction invalid alarm_type value in JSON policy file, valid value should be Major or Minor')
            self.alarm_type_prefix = json_obj[ThermalOverThresholdLogAction.JSON_FIELD_ALARM_TYPE]
        else:
            raise ValueError('ThermalOverThresholdLogAction '
                             'missing mandatory field {} in JSON policy file'.
                             format(ThermalOverThresholdLogAction.JSON_FIELD_ALARM_TYPE))

    def execute(self, thermal_info_dict):
        """
        Over critical threshold logging algorithm
        :param thermal_info_dict: A dictionary stores all thermal information.
        :return:
        """
        SYSLOG_IDENTIFIER = "thermalctld"
        sonic_logger = logger.Logger(SYSLOG_IDENTIFIER)

        from .thermal_infos import ThermalInfo
        if ThermalInfo.INFO_NAME in thermal_info_dict and isinstance(thermal_info_dict[ThermalInfo.INFO_NAME], ThermalInfo):
            thermal_info_obj = thermal_info_dict[ThermalInfo.INFO_NAME]
            if thermal_info_obj:
                thermal_list = thermal_info_obj.get_fault_thermals()
                if len(thermal_list) != 0:
                    for thermal in thermal_list:
                            sonic_logger.log_warning(" {}:{}: temperature value is over critical threshold value".
                                            format(self.alarm_type_prefix, thermal.get_name()))
