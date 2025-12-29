"""
热水器控制器
"""

from nekro_agent.api.plugin import SandboxMethodType
from nekro_agent.api.schemas import AgentCtx

from ..plugin import plugin
from .base import get_cloud_client


@plugin.mount_sandbox_method(
    SandboxMethodType.TOOL,
    name="控制美的热水器",
    description="控制美的热水器的开关、温度等"
)
async def control_midea_water_heater(
    _ctx: AgentCtx,
    device_id: int,
    power: int | None = None,
    target_temperature: int | None = None
) -> str:
    """控制美的热水器设备

    可以控制热水器的电源开关和目标温度。

    Args:
        device_id (int): 热水器设备的ID
        power (int | None): 电源状态，1=开机，0=关机
        target_temperature (int | None): 目标温度，范围35-75°C

    Returns:
        str: 控制结果描述
    """
    cloud = await get_cloud_client()
    if not cloud:
        return "error:not_logged_in"
    
    control = {}
    
    if power is not None:
        control["Power"] = power
    
    if target_temperature is not None:
        if target_temperature < 35 or target_temperature > 75:
            return "error:invalid_temperature"
        control["TargetTemperature"] = target_temperature
    
    if not control:
        return "error:no_params"
    
    try:
        success = await cloud.send_device_control(device_id, control)
        return "ok" if success else "error:device_offline"
    except Exception as e:
        return f"error:exception:{e}"
