"""
热水器控制器
"""

from nekro_agent.api.plugin import SandboxMethodType
from nekro_agent.api.schemas import AgentCtx

from ..plugin import plugin
from .base import get_cloud_client


@plugin.mount_sandbox_method(
    SandboxMethodType.TOOL,
    name="控制美的热水器",
    description="控制美的热水器的开关、温度、运行模式等"
)
async def control_midea_water_heater(
    _ctx: AgentCtx,
    device_id: int,
    power: int | None = None,
    target_temperature: int | None = None,
    operation_mode: str | None = None
) -> str:
    """控制美的热水器设备

    可以控制热水器的电源开关、目标温度和运行模式。

    Args:
        device_id (int): 热水器设备的ID，可通过 get_midea_devices() 获取
        power (int | None): 电源状态，1=开机，0=关机
        target_temperature (int | None): 目标温度，范围35-75°C
        operation_mode (str | None): 运行模式，"normal"=正常 "eco"=节能 "boost"=速热 "vacation"=假期

    Returns:
        str: 控制结果，"ok"表示成功，"error:xxx"表示失败

    Example:
        # 打开热水器，设置温度50度
        result = control_midea_water_heater(device_id=12345678, power=1, target_temperature=50)
        
        # 设置节能模式
        result = control_midea_water_heater(device_id=12345678, operation_mode="eco")
        
        # 设置速热模式，快速加热
        result = control_midea_water_heater(device_id=12345678, operation_mode="boost")
    """
    cloud = await get_cloud_client()
    if not cloud:
        return "error:not_logged_in"
    
    control = {}
    
    if power is not None:
        # power: "on" 或 "off"
        control["power"] = "on" if power else "off"
    
    if target_temperature is not None:
        if target_temperature < 35 or target_temperature > 75:
            return "error:invalid_temperature"
        control["temperature"] = target_temperature
    
    if operation_mode is not None:
        mode_map = {
            "normal": "normal",
            "eco": "eco",
            "boost": "boost",
            "vacation": "vacation"
        }
        if operation_mode in mode_map:
            control["mode"] = mode_map[operation_mode]
        else:
            return f"error:invalid_operation_mode:{operation_mode}"
    
    if not control:
        return "error:no_params"
    
    try:
        success = await cloud.send_device_control(device_id, control)
        return "ok" if success else "error:device_offline"
    except Exception as e:
        return f"error:exception:{e}"
