"""
设备控制器模块
"""

from .base import (
    get_cloud_client,
    get_midea_devices,
    control_midea_device,
    get_midea_device_status,
)
from .ac import (
    control_midea_ac,
    get_midea_ac_status,
    inject_ac_params_hint,
)
from .fan import control_midea_fan
from .dehumidifier import control_midea_dehumidifier
from .humidifier import control_midea_humidifier
from .light import control_midea_light
from .water_heater import control_midea_water_heater

__all__ = [
    "get_cloud_client",
    "get_midea_devices",
    "control_midea_device",
    "get_midea_device_status",
    "control_midea_ac",
    "get_midea_ac_status",
    "inject_ac_params_hint",
    "control_midea_fan",
    "control_midea_dehumidifier",
    "control_midea_humidifier",
    "control_midea_light",
    "control_midea_water_heater",
]
