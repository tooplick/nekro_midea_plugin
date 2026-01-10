"""
加湿器控制器
"""

from nekro_agent.api.plugin import SandboxMethodType
from nekro_agent.api.schemas import AgentCtx

from ..plugin import plugin
from .base import get_cloud_client, send_device_control_with_retry, check_permission


@plugin.mount_sandbox_method(
    SandboxMethodType.TOOL,
    name="控制美的加湿器",
    description="控制美的加湿器的开关、湿度、模式、风档、净离子、风干等"
)
async def control_midea_humidifier(
    _ctx: AgentCtx,
    device_id: int,
    power: int | None = None,
    target_humidity: int | None = None,
    mode: str | None = None,
    wind_gear: str | None = None,
    net_ions: int | None = None,
    air_dry: int | None = None,
    buzzer: int | None = None
) -> str:
    """控制美的加湿器设备

    可以控制加湿器的电源开关、目标湿度、模式、风档、净离子、风干、蜂鸣器等。

    Args:
        device_id (int): 加湿器设备的ID，可通过 get_midea_devices() 获取
        power (int | None): 电源状态，1=开机，0=关机
        target_humidity (int | None): 目标湿度，范围30-80%
        mode (str | None): 模式，"manual"=手动 "moist_skin"=润肤 "sleep"=睡眠
        wind_gear (str | None): 风档，"low"=低档 "medium"=中档 "high"=高档 "auto"=自动
        net_ions (int | None): 净离子，1=开启，0=关闭
        air_dry (int | None): 风干功能，1=开启，0=关闭
        buzzer (int | None): 蜂鸣器，1=开启，0=关闭

    Returns:
        str: 控制结果，"ok"表示成功，"error:xxx"表示失败

    Example:
        # 打开加湿器，设置目标湿度60%，手动模式
        result = control_midea_humidifier(device_id=12345678, power=1, target_humidity=60, mode="manual")
        
        # 设置睡眠模式，低档风
        result = control_midea_humidifier(device_id=12345678, mode="sleep", wind_gear="low")
        
        # 开启净离子功能
        result = control_midea_humidifier(device_id=12345678, net_ions=1)
    """
    # 权限检查
    has_perm, perm_error = await check_permission(_ctx)
    if not has_perm:
        return perm_error
    
    cloud = await get_cloud_client()
    if not cloud:
        return "error:not_logged_in"
    
    control = {}
    
    if power is not None:
        # power: "on" 或 "off"
        control["power"] = "on" if power else "off"
    
    if target_humidity is not None:
        if target_humidity < 30 or target_humidity > 80:
            return "error:invalid_humidity"
        control["humidity"] = target_humidity
    
    if mode is not None:
        mode_map = {
            "manual": "manual",
            "moist_skin": "moist_skin",
            "sleep": "sleep"
        }
        if mode in mode_map:
            control["humidity_mode"] = mode_map[mode]
        else:
            return f"error:invalid_mode:{mode}"
    
    if wind_gear is not None:
        gear_map = {
            "low": "low",
            "medium": "medium",
            "high": "high",
            "auto": "auto"
        }
        if wind_gear in gear_map:
            control["wind_gear"] = gear_map[wind_gear]
        else:
            return f"error:invalid_wind_gear:{wind_gear}"
    
    if net_ions is not None:
        if net_ions not in (0, 1):
            return "error:invalid_net_ions"
        # netIons_on_off: "on" 或 "off"
        control["netIons_on_off"] = "on" if net_ions else "off"
    
    if air_dry is not None:
        if air_dry not in (0, 1):
            return "error:invalid_air_dry"
        # airDry_on_off: "on" 或 "off"
        control["airDry_on_off"] = "on" if air_dry else "off"
    
    if buzzer is not None:
        if buzzer not in (0, 1):
            return "error:invalid_buzzer"
        # buzzer: "on" 或 "off"
        control["buzzer"] = "on" if buzzer else "off"
    
    if not control:
        return "error:no_params"
    
    try:
        success, error = await send_device_control_with_retry(cloud, device_id, control)
        return "ok" if success else error
    except Exception as e:
        return f"error:exception:{e}"
