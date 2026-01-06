"""
灯控制器
"""

from nekro_agent.api.plugin import SandboxMethodType
from nekro_agent.api.schemas import AgentCtx

from ..plugin import plugin
from .base import get_cloud_client, send_device_control_with_retry


@plugin.mount_sandbox_method(
    SandboxMethodType.TOOL,
    name="控制美的灯",
    description="控制美的智能灯的开关、亮度、色温、灯效、颜色等"
)
async def control_midea_light(
    _ctx: AgentCtx,
    device_id: int,
    power: int | None = None,
    brightness: int | None = None,
    color_temp: int | None = None,
    effect: str | None = None,
    rgb_color: str | None = None
) -> str:
    """控制美的智能灯设备

    可以控制灯的电源开关、亮度、色温、灯效模式、RGB颜色等。

    Args:
        device_id (int): 灯设备的ID，可通过 get_midea_devices() 获取
        power (int | None): 电源状态，1=开，0=关
        brightness (int | None): 亮度，范围1-100%
        color_temp (int | None): 色温，范围0-100（0=暖光/2700K，100=冷光/6500K）
        effect (str | None): 灯效模式，"none"=无效果 "colorloop"=彩色循环 "flash"=闪烁
        rgb_color (str | None): RGB颜色，格式为 "R,G,B"，如 "255,0,0" 表示红色

    Returns:
        str: 控制结果，"ok"表示成功，"error:xxx"表示失败

    Example:
        # 打开灯，亮度80%
        result = control_midea_light(device_id=12345678, power=1, brightness=80)
        
        # 设置暖光色温
        result = control_midea_light(device_id=12345678, color_temp=20)
        
        # 设置彩色循环灯效
        result = control_midea_light(device_id=12345678, effect="colorloop")
        
        # 设置红色
        result = control_midea_light(device_id=12345678, rgb_color="255,0,0")
    """
    cloud = await get_cloud_client()
    if not cloud:
        return "error:not_logged_in"
    
    control = {}
    
    if power is not None:
        # power: "on" 或 "off"
        control["power"] = "on" if power else "off"
    
    if brightness is not None:
        if brightness < 1 or brightness > 100:
            return "error:invalid_brightness"
        control["brightness"] = brightness
    
    if color_temp is not None:
        if color_temp < 0 or color_temp > 100:
            return "error:invalid_color_temp"
        control["color_temperature"] = color_temp
    
    if effect is not None:
        effect_map = {
            "none": 0,
            "colorloop": 1,
            "flash": 2
        }
        if effect in effect_map:
            control["effect"] = effect_map[effect]
        else:
            return f"error:invalid_effect:{effect}"
    
    if rgb_color is not None:
        try:
            parts = rgb_color.split(",")
            if len(parts) != 3:
                return "error:invalid_rgb_color_format"
            r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
            if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
                return "error:invalid_rgb_color_range"
            control["r"] = r
            control["g"] = g
            control["b"] = b
        except ValueError:
            return "error:invalid_rgb_color_format"
    
    if not control:
        return "error:no_params"
    
    try:
        success, error = await send_device_control_with_retry(cloud, device_id, control)
        return "ok" if success else error
    except Exception as e:
        return f"error:exception:{e}"
