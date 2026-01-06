"""
除湿机控制器
"""

from nekro_agent.api.plugin import SandboxMethodType
from nekro_agent.api.schemas import AgentCtx

from ..plugin import plugin
from .base import get_cloud_client, send_device_control_with_retry


@plugin.mount_sandbox_method(
    SandboxMethodType.TOOL,
    name="控制美的除湿机",
    description="控制美的除湿机的开关、湿度、模式、风速、负离子、童锁、摆风等"
)
async def control_midea_dehumidifier(
    _ctx: AgentCtx,
    device_id: int,
    power: int | None = None,
    target_humidity: int | None = None,
    mode: str | None = None,
    fan_speed: str | None = None,
    anion: int | None = None,
    child_lock: int | None = None,
    swing_ud: int | None = None
) -> str:
    """控制美的除湿机设备

    可以控制除湿机的电源开关、目标湿度、模式、风速、负离子、童锁、上下摆风等。

    Args:
        device_id (int): 除湿机设备的ID，可通过 get_midea_devices() 获取
        power (int | None): 电源状态，1=开机，0=关机
        target_humidity (int | None): 目标湿度，范围35-85%
        mode (str | None): 模式，"continuity"=连续 "auto"=智能 "fan"=送风 "dry_shoes"=干鞋 "dry_clothes"=干衣
        fan_speed (str | None): 风速，"low"=低速 "high"=高速
        anion (int | None): 负离子，1=开启，0=关闭
        child_lock (int | None): 童锁，1=开启，0=关闭
        swing_ud (int | None): 上下摆风，1=开启，0=关闭

    Returns:
        str: 控制结果，"ok"表示成功，"error:xxx"表示失败

    Example:
        # 打开除湿机，设置目标湿度50%，智能模式
        result = control_midea_dehumidifier(device_id=12345678, power=1, target_humidity=50, mode="auto")
        
        # 开启负离子功能
        result = control_midea_dehumidifier(device_id=12345678, anion=1)
        
        # 开启干衣模式
        result = control_midea_dehumidifier(device_id=12345678, mode="dry_clothes")
    """
    cloud = await get_cloud_client()
    if not cloud:
        return "error:not_logged_in"
    
    control = {}
    
    if power is not None:
        # power: "on" 或 "off"
        control["power"] = "on" if power else "off"
    
    if target_humidity is not None:
        if target_humidity < 35 or target_humidity > 85:
            return "error:invalid_humidity"
        control["humidity"] = target_humidity
    
    if mode is not None:
        mode_map = {
            "continuity": "continuity",
            "auto": "auto",
            "fan": "fan",
            "dry_shoes": "dry_shoes",
            "dry_clothes": "dry_clothes"
        }
        if mode in mode_map:
            control["mode"] = mode_map[mode]
        else:
            return f"error:invalid_mode:{mode}"
    
    if fan_speed is not None:
        speed_map = {
            "low": "30",
            "high": "80"
        }
        if fan_speed in speed_map:
            control["wind_speed"] = speed_map[fan_speed]
        else:
            return f"error:invalid_fan_speed:{fan_speed}"
    
    if anion is not None:
        if anion not in (0, 1):
            return "error:invalid_anion"
        # anion: "on" 或 "off"
        control["anion"] = "on" if anion else "off"
    
    if child_lock is not None:
        if child_lock not in (0, 1):
            return "error:invalid_child_lock"
        # child_lock: "on" 或 "off"
        control["child_lock"] = "on" if child_lock else "off"
    
    if swing_ud is not None:
        if swing_ud not in (0, 1):
            return "error:invalid_swing_ud"
        # wind_swing_ud: "on" 或 "off"
        control["wind_swing_ud"] = "on" if swing_ud else "off"
    
    if not control:
        return "error:no_params"
    
    try:
        success, error = await send_device_control_with_retry(cloud, device_id, control)
        return "ok" if success else error
    except Exception as e:
        return f"error:exception:{e}"
