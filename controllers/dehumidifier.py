"""
除湿机控制器
"""

from nekro_agent.api.plugin import SandboxMethodType
from nekro_agent.api.schemas import AgentCtx

from ..plugin import plugin
from .base import get_cloud_client


@plugin.mount_sandbox_method(
    SandboxMethodType.TOOL,
    name="控制美的除湿机",
    description="控制美的除湿机的开关、湿度、模式等"
)
async def control_midea_dehumidifier(
    _ctx: AgentCtx,
    device_id: int,
    power: int | None = None,
    target_humidity: int | None = None,
    mode: int | None = None,
    fan_speed: int | None = None
) -> str:
    """控制美的除湿机设备

    可以控制除湿机的电源开关、目标湿度、模式和风速。

    Args:
        device_id (int): 除湿机设备的ID
        power (int | None): 电源状态，1=开机，0=关机
        target_humidity (int | None): 目标湿度，范围35-85%
        mode (int | None): 模式，1=智能 2=连续 3=干衣
        fan_speed (int | None): 风速，1=低速 2=高速

    Returns:
        str: 控制结果描述
    """
    cloud = await get_cloud_client()
    if not cloud:
        return "error:not_logged_in"
    
    control = {}
    
    if power is not None:
        control["Power"] = power
    
    if target_humidity is not None:
        if target_humidity < 35 or target_humidity > 85:
            return "error:invalid_humidity"
        control["TargetHumidity"] = target_humidity
    
    if mode is not None:
        control["Mode"] = mode
    
    if fan_speed is not None:
        control["FanSpeed"] = fan_speed
    
    if not control:
        return "error:no_params"
    
    try:
        success = await cloud.send_device_control(device_id, control)
        return "ok" if success else "error:device_offline"
    except Exception as e:
        return f"error:exception:{e}"
