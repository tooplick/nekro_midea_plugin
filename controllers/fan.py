"""
风扇控制器
"""

from nekro_agent.api.plugin import SandboxMethodType
from nekro_agent.api.schemas import AgentCtx

from ..plugin import plugin
from .base import get_cloud_client


@plugin.mount_sandbox_method(
    SandboxMethodType.TOOL,
    name="控制美的风扇",
    description="控制美的风扇的开关、风速、摇头等"
)
async def control_midea_fan(
    _ctx: AgentCtx,
    device_id: int,
    power: int | None = None,
    fan_speed: int | None = None,
    oscillate: int | None = None,
    mode: int | None = None
) -> str:
    """控制美的风扇设备

    可以控制风扇的电源开关、风速、摇头和模式。

    Args:
        device_id (int): 风扇设备的ID
        power (int | None): 电源状态，1=开机，0=关机
        fan_speed (int | None): 风速，1-12档
        oscillate (int | None): 摇头，1=开启，0=关闭
        mode (int | None): 模式，1=正常 2=自然风 3=睡眠

    Returns:
        str: 控制结果描述
    """
    cloud = await get_cloud_client()
    if not cloud:
        return "error:not_logged_in"
    
    control = {}
    
    if power is not None:
        control["Power"] = power
    
    if fan_speed is not None:
        control["FanSpeed"] = fan_speed
    
    if oscillate is not None:
        control["Oscillate"] = oscillate
    
    if mode is not None:
        control["Mode"] = mode
    
    if not control:
        return "error:no_params"
    
    try:
        success = await cloud.send_device_control(device_id, control)
        return "ok" if success else "error:device_offline"
    except Exception as e:
        return f"error:exception:{e}"
