"""
基础控制器 - 通用方法
"""

import json
from nekro_agent.api.plugin import SandboxMethodType
from nekro_agent.api.schemas import AgentCtx
from nekro_agent.api.core import logger

from ..constants import STORE_KEY_CREDENTIALS, get_device_type_name
from ..midea import MeijuCloud, ApiResult
from ..plugin import plugin


async def get_cloud_client() -> MeijuCloud | None:
    """获取已登录的云客户端，支持加载密码用于自动刷新"""
    creds_json = await plugin.store.get(store_key=STORE_KEY_CREDENTIALS)
    if not creds_json:
        return None
    
    creds = json.loads(creds_json)
    if not creds.get("access_token"):
        return None
    
    cloud = MeijuCloud(
        account=creds.get("account", ""), 
        password=creds.get("password", "")  # 加载密码用于自动刷新
    )
    cloud.load_credentials(creds)
    return cloud


async def _refresh_credentials(cloud: MeijuCloud) -> bool:
    """刷新凭证
    
    当检测到登录状态失效时，使用保存的账号密码重新登录
    
    Returns:
        刷新成功返回 True，失败返回 False
    """
    # 检查是否有密码
    if not cloud._password:
        logger.warning("无法自动刷新凭证：未保存密码")
        return False
    
    logger.info(f"正在自动刷新美的账号 {cloud._account} 的凭证...")
    success, message = await cloud.login()
    
    if success:
        # 保存新凭证
        creds = cloud.get_credentials()
        await plugin.store.set(
            store_key=STORE_KEY_CREDENTIALS,
            value=json.dumps(creds)
        )
        logger.info("凭证刷新成功")
        return True
    else:
        logger.error(f"凭证刷新失败: {message}")
        return False


async def send_device_control_with_retry(
    cloud: MeijuCloud, 
    device_id: int, 
    control: dict
) -> tuple[bool, str]:
    """带自动刷新的设备控制
    
    当检测到 token 过期时，自动刷新凭证并重试
    
    Args:
        cloud: 美的云客户端
        device_id: 设备 ID
        control: 控制命令字典
        
    Returns:
        (成功标志, 错误消息或 "ok")
    """
    result = await cloud.send_device_control(device_id, control)
    
    # 如果是 token 错误，尝试刷新并重试
    if result.is_token_error:
        logger.debug(f"检测到 token 错误 (code={result.error_code})，尝试刷新凭证...")
        if await _refresh_credentials(cloud):
            result = await cloud.send_device_control(device_id, control)
    
    if result.success:
        return True, "ok"
    else:
        # 区分不同类型的错误
        if result.is_token_error:
            return False, "error:token_expired"
        elif result.error_code == -1:
            return False, f"error:network:{result.error_message}"
        else:
            return False, "error:device_offline"


async def get_device_status_with_retry(
    cloud: MeijuCloud,
    device_id: int,
    query: dict
) -> ApiResult:
    """带自动刷新的设备状态获取
    
    当检测到 token 过期时，自动刷新凭证并重试
    
    Args:
        cloud: 美的云客户端
        device_id: 设备 ID
        query: 查询参数字典
        
    Returns:
        ApiResult 对象
    """
    result = await cloud.get_device_status(device_id, query)
    
    # 如果是 token 错误，尝试刷新并重试
    if result.is_token_error:
        logger.debug(f"检测到 token 错误 (code={result.error_code})，尝试刷新凭证...")
        if await _refresh_credentials(cloud):
            result = await cloud.get_device_status(device_id, query)
    
    return result


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
    cloud = await get_cloud_client()
    if not cloud:
        return "错误：美的账号未登录，请先在插件管理页面登录美的账号"
    
    try:
        # 获取家庭列表
        result = await cloud.list_home()
        
        # 如果是 token 错误，尝试刷新并重试
        if result.is_token_error:
            if await _refresh_credentials(cloud):
                result = await cloud.list_home()
        
        if not result.success or not result.data:
            return "获取家庭列表失败"
        
        homes = result.data
        result_lines = ["📱 美的智能家居设备列表：", ""]
        
        for home_id, home_name in homes.items():
            result_lines.append(f"🏠 {home_name}:")
            
            app_result = await cloud.list_appliances(home_id)
            
            # 如果是 token 错误，尝试刷新并重试
            if app_result.is_token_error:
                if await _refresh_credentials(cloud):
                    app_result = await cloud.list_appliances(home_id)
            
            if not app_result.success or not app_result.data:
                result_lines.append("  （无设备或获取失败）")
                continue
            
            for device_id, info in app_result.data.items():
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
    cloud = await get_cloud_client()
    if not cloud:
        return "error:not_logged_in"
    
    try:
        control = json.loads(control_params)
    except json.JSONDecodeError as e:
        return f"error:invalid_json:{e}"
    
    if not control or not isinstance(control, dict):
        return "error:invalid_params"
    
    try:
        success, error = await send_device_control_with_retry(cloud, device_id, control)
        return "ok" if success else error
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
    cloud = await get_cloud_client()
    if not cloud:
        return "错误：美的账号未登录"
    
    try:
        query = json.loads(query_params)
    except json.JSONDecodeError as e:
        return f"错误：查询参数JSON格式错误: {e}"
    
    if not query or not isinstance(query, dict):
        return "错误：查询参数必须是非空的JSON对象"
    
    try:
        result = await get_device_status_with_retry(cloud, device_id, query)
        if result.success and result.data:
            return json.dumps(result.data, ensure_ascii=False, indent=2)
        else:
            return f"获取设备 {device_id} 状态失败，设备可能离线"
    except Exception as e:
        return f"获取设备状态失败: {e}"
