"""
Nekro Agent 美的控制插件
"""

import json
from nekro_agent.api.plugin import NekroPlugin, SandboxMethodType
from nekro_agent.api.schemas import AgentCtx

from .midea_client import MeijuCloud, get_device_type_name

plugin = NekroPlugin(
    name="美的智能家居控制",
    module_name="nekro_midea_plugin",
    description="给予AI助手通过美的云控制智能家居设备的能力",
    version="1.0.0",
    author="GeQian",
    url="https://github.com/tooplick/nekro_midea_plugin",
)

# KV 存储键名
STORE_KEY_CREDENTIALS = "midea_credentials"


async def _get_cloud_client() -> MeijuCloud | None:
    """获取已登录的云客户端"""
    creds_json = await plugin.store.get(store_key=STORE_KEY_CREDENTIALS)
    if not creds_json:
        return None
    
    creds = json.loads(creds_json)
    if not creds.get("access_token"):
        return None
    
    cloud = MeijuCloud(account=creds.get("account", ""), password="")
    cloud.load_credentials(creds)
    return cloud


@plugin.mount_prompt_inject_method(
    name="midea_usage_hint",
    description="美的设备控制使用提示"
)
async def inject_midea_hint(_ctx: AgentCtx) -> str:
    """注入美的设备控制的使用提示"""
    return """【美的智能家居控制提示】
调用美的设备控制方法后，根据返回值用自然语言回复用户：
- ok: 操作成功
- error:device_offline: 设备离线
- error:not_logged_in: 未登录美的账号
- error:invalid_xxx: 参数错误
不要直接发送返回值给用户。"""


@plugin.mount_sandbox_method(
    SandboxMethodType.AGENT,
    name="获取美的设备列表",
    description="获取美的智能家居的所有设备列表"
)
async def get_midea_devices(_ctx: AgentCtx) -> str:
    """获取美的智能家居的所有设备列表

    返回所有家庭中的设备信息，包括设备ID、名称、类型、在线状态等。
    必须先通过网页登录美的账号才能使用此功能。

    Returns:
        str: 设备列表的文本描述，包含每个设备的详细信息

    Example:
        devices = get_midea_devices()
        print(devices)
    """
    cloud = await _get_cloud_client()
    if not cloud:
        return "错误：美的账号未登录，请先在插件管理页面登录美的账号"
    
    try:
        # 获取家庭列表
        homes = await cloud.list_home()
        if not homes:
            return "获取家庭列表失败"
        
        result_lines = ["📱 美的智能家居设备列表：", ""]
        
        for home_id, home_name in homes.items():
            result_lines.append(f"🏠 {home_name}:")
            
            appliances = await cloud.list_appliances(home_id)
            if not appliances:
                result_lines.append("  （无设备）")
                continue
            
            for device_id, info in appliances.items():
                status = "🟢在线" if info["online"] else "🔴离线"
                type_name = get_device_type_name(info["type"])
                result_lines.append(f"  • {info['name']} ({type_name})")
                result_lines.append(f"    设备ID: {device_id}")
                result_lines.append(f"    房间: {info['room']}")
                result_lines.append(f"    状态: {status}")
                result_lines.append("")
        
        return "\n".join(result_lines)
    except Exception as e:
        return f"获取设备列表失败: {e}"


@plugin.mount_sandbox_method(
    SandboxMethodType.TOOL,
    name="控制美的空调",
    description="控制美的空调的开关、温度、模式等"
)
async def control_midea_ac(
    _ctx: AgentCtx,
    device_id: int,
    power: int | None = None,
    temperature: int | None = None,
    mode: int | None = None,
    fan_speed: int | None = None
) -> str:
    """控制美的空调设备

    可以控制空调的电源开关、设定温度、运行模式和风速。
    必须先通过 get_midea_devices() 获取设备ID。

    Args:
        device_id (int): 空调设备的ID，可通过 get_midea_devices() 获取
        power (int | None): 电源状态，1=开机，0=关机，None=不改变
        temperature (int | None): 设定温度，范围16-30度，None=不改变
        mode (int | None): 运行模式，1=自动 2=制冷 3=除湿 4=送风 5=制热，None=不改变
        fan_speed (int | None): 风速，0=自动 1-7=手动风速，None=不改变

    Returns:
        str: 控制结果描述

    Example:
        # 打开空调并设置为制冷模式26度
        result = control_midea_ac(device_id=12345678, power=1, temperature=26, mode=2)

        # 关闭空调
        result = control_midea_ac(device_id=12345678, power=0)

        # 只调整温度
        result = control_midea_ac(device_id=12345678, temperature=24)
    """
    cloud = await _get_cloud_client()
    if not cloud:
        return "error:not_logged_in"
    
    # 构建控制命令
    control = {}
    control_desc = []
    
    if power is not None:
        control["Power"] = power
        control_desc.append(f"电源={'开' if power else '关'}")
    
    if temperature is not None:
        if temperature < 16 or temperature > 30:
            return "error:invalid_temperature"
        control["SetTemperature"] = temperature
        control_desc.append(f"温度={temperature}°C")
    
    if mode is not None:
        mode_names = {1: "自动", 2: "制冷", 3: "除湿", 4: "送风", 5: "制热"}
        if mode not in mode_names:
            return "error:invalid_mode"
        control["Mode"] = mode
        control_desc.append(f"模式={mode_names[mode]}")
    
    if fan_speed is not None:
        if fan_speed < 0 or fan_speed > 7:
            return "error:invalid_fan_speed"
        control["FanSpeed"] = fan_speed
        control_desc.append(f"风速={'自动' if fan_speed == 0 else fan_speed}")
    
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


@plugin.mount_sandbox_method(
    SandboxMethodType.AGENT,
    name="获取美的空调状态",
    description="获取美的空调的当前运行状态"
)
async def get_midea_ac_status(_ctx: AgentCtx, device_id: int) -> str:
    """获取美的空调的当前运行状态

    查询指定空调设备的当前状态，包括电源、温度、模式、风速等信息。

    Args:
        device_id (int): 空调设备的ID，可通过 get_midea_devices() 获取

    Returns:
        str: 空调状态的文本描述

    Example:
        status = get_midea_ac_status(device_id=12345678)
        print(status)
    """
    cloud = await _get_cloud_client()
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
        
        result_lines = [
            f"空调状态 (设备ID: {device_id})",
            f"",
            f"电源: {'开启' if power else '关闭'}",
            f"设定温度: {set_temp}°C",
            f"室内温度: {indoor_temp}°C",
            f"室外温度: {outdoor_temp}°C",
            f"运行模式: {mode_names.get(mode, f'未知({mode})')}",
            f"风速: {'自动' if fan_speed == 0 else fan_speed}",
        ]
        
        return "\n".join(result_lines)
    except Exception as e:
        return f"获取空调状态失败: {e}"


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

    Example:
        # 打开风扇，3档风速，开启摇头
        result = control_midea_fan(device_id=12345678, power=1, fan_speed=3, oscillate=1)
    """
    cloud = await _get_cloud_client()
    if not cloud:
        return "error:not_logged_in"
    
    control = {}
    control_desc = []
    
    if power is not None:
        control["Power"] = power
        control_desc.append(f"电源={'开' if power else '关'}")
    
    if fan_speed is not None:
        control["FanSpeed"] = fan_speed
        control_desc.append(f"风速={fan_speed}档")
    
    if oscillate is not None:
        control["Oscillate"] = oscillate
        control_desc.append(f"摇头={'开' if oscillate else '关'}")
    
    if mode is not None:
        mode_names = {1: "正常", 2: "自然风", 3: "睡眠"}
        control["Mode"] = mode
        control_desc.append(f"模式={mode_names.get(mode, mode)}")
    
    if not control:
        return "error:no_params"
    
    try:
        success = await cloud.send_device_control(device_id, control)
        return "ok" if success else "error:device_offline"
    except Exception as e:
        return f"error:exception:{e}"


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

    Example:
        # 打开除湿机，设置目标湿度50%
        result = control_midea_dehumidifier(device_id=12345678, power=1, target_humidity=50)
    """
    cloud = await _get_cloud_client()
    if not cloud:
        return "error:not_logged_in"
    
    control = {}
    control_desc = []
    
    if power is not None:
        control["Power"] = power
        control_desc.append(f"电源={'开' if power else '关'}")
    
    if target_humidity is not None:
        if target_humidity < 35 or target_humidity > 85:
            return "error:invalid_humidity"
        control["TargetHumidity"] = target_humidity
        control_desc.append(f"目标湿度={target_humidity}%")
    
    if mode is not None:
        mode_names = {1: "智能", 2: "连续", 3: "干衣"}
        control["Mode"] = mode
        control_desc.append(f"模式={mode_names.get(mode, mode)}")
    
    if fan_speed is not None:
        control["FanSpeed"] = fan_speed
        control_desc.append(f"风速={'低速' if fan_speed == 1 else '高速'}")
    
    if not control:
        return "error:no_params"
    
    try:
        success = await cloud.send_device_control(device_id, control)
        return "ok" if success else "error:device_offline"
    except Exception as e:
        return f"error:exception:{e}"


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

    Example:
        # 打开加湿器，设置目标湿度60%
        result = control_midea_humidifier(device_id=12345678, power=1, target_humidity=60)
    """
    cloud = await _get_cloud_client()
    if not cloud:
        return "error:not_logged_in"
    
    control = {}
    control_desc = []
    
    if power is not None:
        control["Power"] = power
        control_desc.append(f"电源={'开' if power else '关'}")
    
    if target_humidity is not None:
        if target_humidity < 40 or target_humidity > 80:
            return "error:invalid_humidity"
        control["TargetHumidity"] = target_humidity
        control_desc.append(f"目标湿度={target_humidity}%")
    
    if mode is not None:
        mode_names = {1: "自动", 2: "连续", 3: "睡眠"}
        control["Mode"] = mode
        control_desc.append(f"模式={mode_names.get(mode, mode)}")
    
    if not control:
        return "error:no_params"
    
    try:
        success = await cloud.send_device_control(device_id, control)
        return "ok" if success else "error:device_offline"
    except Exception as e:
        return f"error:exception:{e}"


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

    Example:
        # 打开灯，亮度80%
        result = control_midea_light(device_id=12345678, power=1, brightness=80)
    """
    cloud = await _get_cloud_client()
    if not cloud:
        return "error:not_logged_in"
    
    control = {}
    control_desc = []
    
    if power is not None:
        control["Power"] = power
        control_desc.append(f"电源={'开' if power else '关'}")
    
    if brightness is not None:
        if brightness < 1 or brightness > 100:
            return "error:invalid_brightness"
        control["Brightness"] = brightness
        control_desc.append(f"亮度={brightness}%")
    
    if color_temp is not None:
        if color_temp < 0 or color_temp > 100:
            return "error:invalid_color_temp"
        control["ColorTemperature"] = color_temp
        control_desc.append(f"色温={color_temp}")
    
    if not control:
        return "error:no_params"
    
    try:
        success = await cloud.send_device_control(device_id, control)
        return "ok" if success else "error:device_offline"
    except Exception as e:
        return f"error:exception:{e}"


@plugin.mount_sandbox_method(
    SandboxMethodType.TOOL,
    name="控制美的热水器",
    description="控制美的热水器的开关、温度等"
)
async def control_midea_water_heater(
    _ctx: AgentCtx,
    device_id: int,
    power: int | None = None,
    target_temperature: int | None = None
) -> str:
    """控制美的热水器设备

    可以控制热水器的电源开关和目标温度。

    Args:
        device_id (int): 热水器设备的ID
        power (int | None): 电源状态，1=开机，0=关机
        target_temperature (int | None): 目标温度，范围35-75°C

    Returns:
        str: 控制结果描述

    Example:
        # 打开热水器，设置温度50度
        result = control_midea_water_heater(device_id=12345678, power=1, target_temperature=50)
    """
    cloud = await _get_cloud_client()
    if not cloud:
        return "error:not_logged_in"
    
    control = {}
    control_desc = []
    
    if power is not None:
        control["Power"] = power
        control_desc.append(f"电源={'开' if power else '关'}")
    
    if target_temperature is not None:
        if target_temperature < 35 or target_temperature > 75:
            return "error:invalid_temperature"
        control["TargetTemperature"] = target_temperature
        control_desc.append(f"目标温度={target_temperature}°C")
    
    if not control:
        return "error:no_params"
    
    try:
        success = await cloud.send_device_control(device_id, control)
        return "ok" if success else "error:device_offline"
    except Exception as e:
        return f"error:exception:{e}"


@plugin.mount_sandbox_method(
    SandboxMethodType.TOOL,
    name="控制美的设备(通用)",
    description="通用的美的设备控制方法，可以发送任意控制参数"
)
async def control_midea_device(
    _ctx: AgentCtx,
    device_id: int,
    control_params: str
) -> str:
    """通用的美的设备控制方法

    可以发送任意控制参数到设备，适用于所有类型的美的智能设备。
    控制参数以JSON格式传入。

    Args:
        device_id (int): 设备的ID
        control_params (str): JSON格式的控制参数，如 '{"Power": 1, "Mode": 2}'

    Returns:
        str: 控制结果描述

    Example:
        # 发送自定义控制命令
        result = control_midea_device(device_id=12345678, control_params='{"Power": 1}')
    """
    cloud = await _get_cloud_client()
    if not cloud:
        return "error:not_logged_in"
    
    try:
        control = json.loads(control_params)
    except json.JSONDecodeError as e:
        return f"error:invalid_json:{e}"
    
    if not control or not isinstance(control, dict):
        return "error:invalid_params"
    
    try:
        success = await cloud.send_device_control(device_id, control)
        return "ok" if success else "error:device_offline"
    except Exception as e:
        return f"error:exception:{e}"


@plugin.mount_sandbox_method(
    SandboxMethodType.AGENT,
    name="获取美的设备状态(通用)",
    description="获取任意美的设备的状态"
)
async def get_midea_device_status(
    _ctx: AgentCtx,
    device_id: int,
    query_params: str
) -> str:
    """获取任意美的设备的状态

    通过指定查询参数获取设备状态，适用于所有类型的美的智能设备。
    查询参数以JSON格式传入。

    Args:
        device_id (int): 设备的ID
        query_params (str): JSON格式的查询参数，如 '{"Power": {}, "Mode": {}}'

    Returns:
        str: 设备状态的JSON字符串

    Example:
        # 查询设备电源和模式状态
        result = get_midea_device_status(device_id=12345678, query_params='{"Power": {}, "Mode": {}}')
    """
    cloud = await _get_cloud_client()
    if not cloud:
        return "错误：美的账号未登录"
    
    try:
        query = json.loads(query_params)
    except json.JSONDecodeError as e:
        return f"错误：查询参数JSON格式错误: {e}"
    
    if not query or not isinstance(query, dict):
        return "错误：查询参数必须是非空的JSON对象"
    
    try:
        status = await cloud.get_device_status(device_id, query)
        if status:
            return json.dumps(status, ensure_ascii=False, indent=2)
        else:
            return f"获取设备 {device_id} 状态失败，设备可能离线"
    except Exception as e:
        return f"获取设备状态失败: {e}"


@plugin.mount_cleanup_method()
async def clean_up():
    """清理插件资源"""
    print("美的插件资源已清理")
