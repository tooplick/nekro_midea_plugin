"""
加湿器控制器
"""

from nekro_agent.api.plugin import SandboxMethodType
from nekro_agent.api.schemas import AgentCtx

from ..plugin import plugin
from .base import get_cloud_client


@plugin.mount_sandbox_method(
    SandboxMethodType.TOOL,
    name="控制美的加湿器",
    description="控制美的加湿器的开关、湿度等"
)
async def control_midea_humidifier(
    _ctx: AgentCtx,
    device_id: int,
    power: int | None = None,
    target_humidity: int | None = None,
    mode: int | None = None
) -> str:
    """控制美的加湿器设备

    可以控制加湿器的电源开关、目标湿度和模式。

    Args:
        device_id (int): 加湿器设备的ID
        power (int | None): 电源状态，1=开机，0=关机
        target_humidity (int | None): 目标湿度，范围40-80%
        mode (int | None): 模式，1=自动 2=连续 3=睡眠

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
        if target_humidity < 40 or target_humidity > 80:
            return "error:invalid_humidity"
        control["TargetHumidity"] = target_humidity
    
    if mode is not None:
        control["Mode"] = mode
    
    if not control:
        return "error:no_params"
    
    try:
        success = await cloud.send_device_control(device_id, control)
        return "ok" if success else "error:device_offline"
    except Exception as e:
        return f"error:exception:{e}"
