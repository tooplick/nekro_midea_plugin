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
    temperature: float | None = None,
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
        temperature (float | None): 设定温度，范围16-30度，支持0.5度步进，None=不改变
        mode (int | None): 运行模式，1=自动 2=制冷 3=除湿 4=送风 5=制热，None=不改变
        fan_speed (int | None): 风速，0=自动 1=静音 2=低 3=中 4=高 5=全速，None=不改变
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
    
    # 构建控制命令（使用小写参数名和字符串值，与 midea_auto_cloud 一致）
    control = {}
    
    if power is not None:
        # power: "on" 或 "off"
        control["power"] = "on" if power else "off"
    
    if temperature is not None:
        if temperature < 16 or temperature > 30:
            return "error:invalid_temperature"
        # 温度拆分为整数和小数部分
        control["temperature"] = int(temperature)
        # small_temperature: 0 表示整数，5 表示 0.5
        control["small_temperature"] = 5 if (temperature % 1) >= 0.5 else 0
    
    if mode is not None:
        # 模式映射: 数字 -> 字符串
        mode_map = {1: "auto", 2: "cool", 3: "dry", 4: "fan", 5: "heat"}
        if mode not in mode_map:
            return "error:invalid_mode"
        control["mode"] = mode_map[mode]
    
    if fan_speed is not None:
        # 风速映射: 0=自动(102) 1=静音(20) 2=低(40) 3=中(60) 4=高(80) 5=全速(100)
        fan_speed_map = {0: 102, 1: 20, 2: 40, 3: 60, 4: 80, 5: 100}
        if fan_speed not in fan_speed_map:
            return "error:invalid_fan_speed"
        control["wind_speed"] = fan_speed_map[fan_speed]
    
    if swing_ud is not None:
        if swing_ud not in (0, 1):
            return "error:invalid_swing_ud"
        control["wind_swing_ud"] = "on" if swing_ud else "off"
    
    if swing_lr is not None:
        if swing_lr not in (0, 1):
            return "error:invalid_swing_lr"
        control["wind_swing_lr"] = "on" if swing_lr else "off"
    
    if preset_mode is not None:
        # 预设模式
        preset_modes = {
            "none": {"eco": "off", "comfort_power_save": "off", "strong_wind": "off"},
            "eco": {"eco": "on"},
            "comfort": {"comfort_power_save": "on"},
            "boost": {"strong_wind": "on"}
        }
        if preset_mode not in preset_modes:
            return "error:invalid_preset_mode"
        control.update(preset_modes[preset_mode])
    
    if aux_heat is not None:
        if aux_heat not in (0, 1):
            return "error:invalid_aux_heat"
        control["ptc"] = "on" if aux_heat else "off"
    
    if dry is not None:
        if dry not in (0, 1):
            return "error:invalid_dry"
        control["dry"] = "on" if dry else "off"
    
    if prevent_straight_wind is not None:
        if prevent_straight_wind not in (0, 1):
            return "error:invalid_prevent_straight_wind"
        # prevent_straight_wind: 0=关闭, 1或2=开启(不同程度)
        control["prevent_straight_wind"] = prevent_straight_wind if prevent_straight_wind else 0
    
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
- temperature: 温度 (16-30°C, 支持0.5度步进)
- mode: 模式 (1=自动 2=制冷 3=除湿 4=送风 5=制热)
- fan_speed: 风速 (0=自动 1=静音 2=低 3=中 4=高 5=全速)
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
        # 使用空查询获取所有状态
        query = {}
        
        response = await cloud.get_device_status(device_id, query)
        if not response:
            return f"获取设备 {device_id} 状态失败，设备可能离线"
        
        # 从响应中提取状态（API返回的是小写参数名）
        status = response.get("status", response)
        
        # 模式映射
        mode_names = {"auto": "自动", "cool": "制冷", "dry": "除湿", "fan": "送风", "heat": "制热"}
        
        # 解析状态（兼容 "on"/"off" 字符串和数字）
        def is_on(v):
            return v == "on" or v == 1 or v is True
        
        power = status.get("power", "off")
        temperature = status.get("temperature", "--")
        small_temp = status.get("small_temperature", 0)
        if temperature != "--" and small_temp:
            temperature = float(temperature) + 0.5
        indoor_temp = status.get("indoor_temperature", "--")
        outdoor_temp = status.get("outdoor_temperature", "--")
        mode = status.get("mode", "auto")
        wind_speed = status.get("wind_speed", 102)
        wind_swing_ud = status.get("wind_swing_ud", "off")
        wind_swing_lr = status.get("wind_swing_lr", "off")
        indoor_humidity = status.get("indoor_humidity")
        eco = status.get("eco", "off")
        strong_wind = status.get("strong_wind", "off")
        comfort_power_save = status.get("comfort_power_save", "off")
        ptc = status.get("ptc", "off")
        dry = status.get("dry", "off")
        prevent_straight_wind = status.get("prevent_straight_wind", 0)
        
        # 风速映射
        wind_speed_names = {102: "自动", 20: "静音", 40: "低", 60: "中", 80: "高", 100: "全速"}
        wind_speed_str = wind_speed_names.get(wind_speed, f"{wind_speed}%")
        
        # 确定预设模式
        if is_on(eco):
            preset_mode = "节能(eco)"
        elif is_on(strong_wind):
            preset_mode = "强劲风(boost)"
        elif is_on(comfort_power_save):
            preset_mode = "舒适节能(comfort)"
        else:
            preset_mode = "正常(none)"
        
        result_lines = [
            f"空调状态 (设备ID: {device_id})",
            f"",
            f"电源: {'开启' if is_on(power) else '关闭'}",
            f"设定温度: {temperature}°C",
            f"室内温度: {indoor_temp}°C",
            f"室外温度: {outdoor_temp}°C",
            f"运行模式: {mode_names.get(mode, f'{mode}')}",
            f"风速: {wind_speed_str}",
            f"上下摆风: {'开启' if is_on(wind_swing_ud) else '关闭'}",
            f"左右摆风: {'开启' if is_on(wind_swing_lr) else '关闭'}",
            f"预设模式: {preset_mode}",
            f"电辅热: {'开启' if is_on(ptc) else '关闭'}",
            f"干燥模式: {'开启' if is_on(dry) else '关闭'}",
            f"防直吹: {'开启' if prevent_straight_wind else '关闭'}",
        ]
        
        if indoor_humidity is not None:
            result_lines.insert(5, f"室内湿度: {indoor_humidity}%")
        
        return "\n".join(result_lines)
    except Exception as e:
        return f"获取空调状态失败: {e}"
