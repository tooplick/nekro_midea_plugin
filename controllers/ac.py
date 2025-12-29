"""
空调控制器
"""

from nekro_agent.api.plugin import SandboxMethodType
from nekro_agent.api.schemas import AgentCtx

from ..plugin import plugin
from .base import get_cloud_client


@plugin.mount_sandbox_method(
    SandboxMethodType.TOOL,
    name="控制美的空调",
    description="控制美的空调的开关、温度、模式、风速、摆风、预设模式等"
)
async def control_midea_ac(
    _ctx: AgentCtx,
    device_id: int,
    power: int | None = None,
    temperature: int | None = None,
    mode: int | None = None,
    fan_speed: int | None = None,
    swing_ud: int | None = None,
    swing_lr: int | None = None,
    preset_mode: str | None = None,
    aux_heat: int | None = None,
    dry: int | None = None,
    prevent_straight_wind: int | None = None
) -> str:
    """控制美的空调设备

    可以控制空调的电源开关、设定温度、运行模式、风速、摆风、预设模式、电辅热、干燥、防直吹等。
    必须先通过 get_midea_devices() 获取设备ID。

    Args:
        device_id (int): 空调设备的ID，可通过 get_midea_devices() 获取
        power (int | None): 电源状态，1=开机，0=关机，None=不改变
        temperature (int | None): 设定温度，范围16-30度，None=不改变
        mode (int | None): 运行模式，1=自动 2=制冷 3=除湿 4=送风 5=制热，None=不改变
        fan_speed (int | None): 风速，0=自动 1-7=手动风速，None=不改变
        swing_ud (int | None): 上下摆风，1=开启，0=关闭，None=不改变
        swing_lr (int | None): 左右摆风，1=开启，0=关闭，None=不改变
        preset_mode (str | None): 预设模式，"none"=正常 "eco"=节能 "comfort"=舒适节能 "boost"=强劲风，None=不改变
        aux_heat (int | None): 电辅热(PTC)，1=开启，0=关闭，None=不改变
        dry (int | None): 干燥模式，1=开启，0=关闭，None=不改变
        prevent_straight_wind (int | None): 防直吹，1=开启，0=关闭，None=不改变

    Returns:
        str: 控制结果，"ok"表示成功，"error:xxx"表示失败
    """
    cloud = await get_cloud_client()
    if not cloud:
        return "error:not_logged_in"
    
    # 构建控制命令
    control = {}
    
    if power is not None:
        control["Power"] = power
    
    if temperature is not None:
        if temperature < 16 or temperature > 30:
            return "error:invalid_temperature"
        control["SetTemperature"] = temperature
    
    if mode is not None:
        mode_names = {1: "自动", 2: "制冷", 3: "除湿", 4: "送风", 5: "制热"}
        if mode not in mode_names:
            return "error:invalid_mode"
        control["Mode"] = mode
    
    if fan_speed is not None:
        if fan_speed < 0 or fan_speed > 7:
            return "error:invalid_fan_speed"
        control["FanSpeed"] = fan_speed
    
    if swing_ud is not None:
        if swing_ud not in (0, 1):
            return "error:invalid_swing_ud"
        control["SwingUD"] = swing_ud
    
    if swing_lr is not None:
        if swing_lr not in (0, 1):
            return "error:invalid_swing_lr"
        control["SwingLR"] = swing_lr
    
    if preset_mode is not None:
        preset_modes = {
            "none": {"Eco": 0, "ComfortPowerSave": 0, "StrongWind": 0},
            "eco": {"Eco": 1},
            "comfort": {"ComfortPowerSave": 1},
            "boost": {"StrongWind": 1}
        }
        if preset_mode not in preset_modes:
            return "error:invalid_preset_mode"
        control.update(preset_modes[preset_mode])
    
    if aux_heat is not None:
        if aux_heat not in (0, 1):
            return "error:invalid_aux_heat"
        control["Ptc"] = aux_heat
    
    if dry is not None:
        if dry not in (0, 1):
            return "error:invalid_dry"
        control["Dry"] = dry
    
    if prevent_straight_wind is not None:
        if prevent_straight_wind not in (0, 1):
            return "error:invalid_prevent_straight_wind"
        control["PreventStraightWind"] = prevent_straight_wind
    
    if not control:
        return "error:no_params"
    
    try:
        success = await cloud.send_device_control(device_id, control)
        if success:
            return "ok"
        else:
            return "error:device_offline"
    except Exception as e:
        return f"error:exception:{e}"


@plugin.mount_prompt_inject_method(
    name="ac_control_params_hint",
    description="空调控制参数说明"
)
async def inject_ac_params_hint(_ctx: AgentCtx) -> str:
    """注入空调控制参数说明"""
    return """【空调控制参数说明】
- power: 电源 (0=关, 1=开)
- temperature: 温度 (16-30°C)
- mode: 模式 (1=自动 2=制冷 3=除湿 4=送风 5=制热)
- fan_speed: 风速 (0=自动, 1-7=手动)
- swing_ud/swing_lr: 上下/左右摆风 (0=关, 1=开)
- preset_mode: 预设模式 ("none"=正常 "eco"=节能 "comfort"=舒适 "boost"=强劲)
- aux_heat: 电辅热 (0=关, 1=开)
- dry: 干燥模式 (0=关, 1=开)
- prevent_straight_wind: 防直吹 (0=关, 1=开)"""


@plugin.mount_sandbox_method(
    SandboxMethodType.AGENT,
    name="获取美的空调状态",
    description="获取美的空调的当前运行状态，包括温度、模式、摆风、预设模式等"
)
async def get_midea_ac_status(_ctx: AgentCtx, device_id: int) -> str:
    """获取美的空调的当前运行状态

    查询指定空调设备的当前状态，包括电源、温度、模式、风速、摆风、预设模式、电辅热、干燥、防直吹等信息。

    Args:
        device_id (int): 空调设备的ID，可通过 get_midea_devices() 获取

    Returns:
        str: 空调状态的文本描述
    """
    cloud = await get_cloud_client()
    if not cloud:
        return "错误：美的账号未登录，请先在插件管理页面登录美的账号"
    
    try:
        # 查询空调状态
        query = {
            "Power": {},
            "SetTemperature": {},
            "IndoorTemperature": {},
            "OutdoorTemperature": {},
            "Mode": {},
            "FanSpeed": {},
            "SwingUD": {},
            "SwingLR": {},
            "IndoorHumidity": {},
            "Eco": {},
            "StrongWind": {},
            "ComfortPowerSave": {},
            "Ptc": {},
            "Dry": {},
            "PreventStraightWind": {},
        }
        
        status = await cloud.get_device_status(device_id, query)
        if not status:
            return f"获取设备 {device_id} 状态失败，设备可能离线"
        
        # 解析状态
        mode_names = {1: "自动", 2: "制冷", 3: "除湿", 4: "送风", 5: "制热"}
        
        power = status.get("Power", 0)
        set_temp = status.get("SetTemperature", "--")
        indoor_temp = status.get("IndoorTemperature", "--")
        outdoor_temp = status.get("OutdoorTemperature", "--")
        mode = status.get("Mode", 0)
        fan_speed = status.get("FanSpeed", 0)
        swing_ud = status.get("SwingUD", 0)
        swing_lr = status.get("SwingLR", 0)
        indoor_humidity = status.get("IndoorHumidity")
        eco = status.get("Eco", 0)
        strong_wind = status.get("StrongWind", 0)
        comfort_power_save = status.get("ComfortPowerSave", 0)
        ptc = status.get("Ptc", 0)
        dry = status.get("Dry", 0)
        prevent_straight_wind = status.get("PreventStraightWind", 0)
        
        # 确定预设模式
        if eco:
            preset_mode = "节能(eco)"
        elif strong_wind:
            preset_mode = "强劲风(boost)"
        elif comfort_power_save:
            preset_mode = "舒适节能(comfort)"
        else:
            preset_mode = "正常(none)"
        
        result_lines = [
            f"空调状态 (设备ID: {device_id})",
            f"",
            f"电源: {'开启' if power else '关闭'}",
            f"设定温度: {set_temp}°C",
            f"室内温度: {indoor_temp}°C",
            f"室外温度: {outdoor_temp}°C",
            f"运行模式: {mode_names.get(mode, f'未知({mode})')}",
            f"风速: {'自动' if fan_speed == 0 else fan_speed}",
            f"上下摆风: {'开启' if swing_ud else '关闭'}",
            f"左右摆风: {'开启' if swing_lr else '关闭'}",
            f"预设模式: {preset_mode}",
            f"电辅热: {'开启' if ptc else '关闭'}",
            f"干燥模式: {'开启' if dry else '关闭'}",
            f"防直吹: {'开启' if prevent_straight_wind else '关闭'}",
        ]
        
        if indoor_humidity is not None:
            result_lines.insert(5, f"室内湿度: {indoor_humidity}%")
        
        return "\n".join(result_lines)
    except Exception as e:
        return f"获取空调状态失败: {e}"
