"""
灯控制器
"""

from nekro_agent.api.plugin import SandboxMethodType
from nekro_agent.api.schemas import AgentCtx

from ..plugin import plugin
from .base import get_cloud_client


@plugin.mount_sandbox_method(
    SandboxMethodType.TOOL,
    name="控制美的灯",
    description="控制美的智能灯的开关、亮度、色温等"
)
async def control_midea_light(
    _ctx: AgentCtx,
    device_id: int,
    power: int | None = None,
    brightness: int | None = None,
    color_temp: int | None = None
) -> str:
    """控制美的智能灯设备

    可以控制灯的电源开关、亮度和色温。

    Args:
        device_id (int): 灯设备的ID
        power (int | None): 电源状态，1=开，0=关
        brightness (int | None): 亮度，范围1-100%
        color_temp (int | None): 色温，范围0-100（0=暖光，100=冷光）

    Returns:
        str: 控制结果描述
    """
    cloud = await get_cloud_client()
    if not cloud:
        return "error:not_logged_in"
    
    control = {}
    
    if power is not None:
        control["Power"] = power
    
    if brightness is not None:
        if brightness < 1 or brightness > 100:
            return "error:invalid_brightness"
        control["Brightness"] = brightness
    
    if color_temp is not None:
        if color_temp < 0 or color_temp > 100:
            return "error:invalid_color_temp"
        control["ColorTemperature"] = color_temp
    
    if not control:
        return "error:no_params"
    
    try:
        success = await cloud.send_device_control(device_id, control)
        return "ok" if success else "error:device_offline"
    except Exception as e:
        return f"error:exception:{e}"
