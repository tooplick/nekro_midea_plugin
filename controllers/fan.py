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
    description="控制美的风扇的开关、风速、摇头、模式、负离子、显示等"
)
async def control_midea_fan(
    _ctx: AgentCtx,
    device_id: int,
    power: int | None = None,
    fan_speed: int | None = None,
    oscillate: int | None = None,
    mode: str | None = None,
    anion: int | None = None,
    display: int | None = None,
    swing_direction: str | None = None
) -> str:
    """控制美的风扇设备

    可以控制风扇的电源开关、风速、摇头、模式、负离子、显示、摆风方向等。

    Args:
        device_id (int): 风扇设备的ID，可通过 get_midea_devices() 获取
        power (int | None): 电源状态，1=开机，0=关机
        fan_speed (int | None): 风速，1-100档（不同型号档位范围不同）
        oscillate (int | None): 摇头，1=开启，0=关闭
        mode (str | None): 模式，"normal"=正常 "sleep"=睡眠 "baby"=宝宝风 "natural"=自然风
        anion (int | None): 负离子，1=开启，0=关闭
        display (int | None): 显示屏，1=开启，0=关闭
        swing_direction (str | None): 摆风方向，"off"=关闭 "horizontal"=水平 "vertical"=垂直 "both"=全方向

    Returns:
        str: 控制结果，"ok"表示成功，"error:xxx"表示失败

    Example:
        # 打开风扇，3档风速，开启摇头
        result = control_midea_fan(device_id=12345678, power=1, fan_speed=3, oscillate=1)
        
        # 设置睡眠模式
        result = control_midea_fan(device_id=12345678, mode="sleep")
        
        # 开启负离子功能
        result = control_midea_fan(device_id=12345678, anion=1)
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
        mode_map = {
            "normal": "normal",
            "sleep": "sleep",
            "baby": "baby",
            "natural": "natural_wind",
            "sleeping_wind": "sleeping_wind",
            "purified_wind": "purified_wind"
        }
        if mode in mode_map:
            control["Mode"] = mode_map[mode]
        else:
            return f"error:invalid_mode:{mode}"
    
    if anion is not None:
        if anion not in (0, 1):
            return "error:invalid_anion"
        control["Anion"] = anion
    
    if display is not None:
        if display not in (0, 1):
            return "error:invalid_display"
        # display_on_off 使用反向逻辑：on=关闭显示，off=开启显示
        control["DisplayOnOff"] = "off" if display else "on"
    
    if swing_direction is not None:
        swing_map = {
            "off": "off",
            "horizontal": "horizontal",
            "vertical": "vertical",
            "both": "both"
        }
        if swing_direction in swing_map:
            control["SwingDirection"] = swing_map[swing_direction]
        else:
            return f"error:invalid_swing_direction:{swing_direction}"
    
    if not control:
        return "error:no_params"
    
    try:
        success = await cloud.send_device_control(device_id, control)
        return "ok" if success else "error:device_offline"
    except Exception as e:
        return f"error:exception:{e}"
