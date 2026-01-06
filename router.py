"""
美的插件 API 路由
"""

import os
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from nekro_agent.api.core import logger

from .plugin import plugin
from .constants import STORE_KEY_CREDENTIALS, get_device_type_name
from .midea import MeijuCloud

router = APIRouter()


class LoginRequest(BaseModel):
    """登录请求模型"""
    account: str
    password: str


# ==================== 静态文件 ====================

@router.get("/")
async def webui_index():
    """返回主页 HTML"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(current_dir, "web", "index.html")
    return FileResponse(html_path, media_type="text/html")


@router.get("/style.css")
async def webui_style():
    """返回样式文件"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_path = os.path.join(current_dir, "web", "style.css")
    return FileResponse(css_path, media_type="text/css")


@router.get("/script.js")
async def webui_script():
    """返回脚本文件"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    js_path = os.path.join(current_dir, "web", "script.js")
    return FileResponse(js_path, media_type="application/javascript")


# ==================== API 端点 ====================

@router.get("/api/status")
async def check_status():
    """检查登录状态"""
    try:
        creds_json = await plugin.store.get(store_key=STORE_KEY_CREDENTIALS)
        if not creds_json:
            return {"logged_in": False}
        
        creds = json.loads(creds_json)
        if not creds.get("access_token"):
            return {"logged_in": False}
        
        return {
            "logged_in": True,
            "account": creds.get("account", "")
        }
    except Exception as e:
        logger.error(f"检查登录状态失败: {e}")
        return {"logged_in": False}


@router.post("/api/login")
async def login(req: LoginRequest):
    """登录美的账号"""
    try:
        cloud = MeijuCloud(account=req.account, password=req.password)
        success, message = await cloud.login()
        
        if success:
            # 保存凭证到 KV 存储
            creds = cloud.get_credentials()
            await plugin.store.set(
                store_key=STORE_KEY_CREDENTIALS,
                value=json.dumps(creds)
            )
            logger.info(f"美的账号 {req.account} 登录成功")
            return {"success": True, "message": "登录成功"}
        else:
            return {"success": False, "message": message}
    except Exception as e:
        logger.error(f"登录失败: {e}")
        raise HTTPException(status_code=500, detail=f"登录失败: {str(e)}")


@router.post("/api/logout")
async def logout():
    """退出登录"""
    try:
        await plugin.store.delete(store_key=STORE_KEY_CREDENTIALS)
        logger.info("美的账号已退出登录")
        return {"success": True, "message": "已退出登录"}
    except Exception as e:
        logger.error(f"退出登录失败: {e}")
        raise HTTPException(status_code=500, detail=f"退出登录失败: {str(e)}")


async def _get_cloud_client() -> MeijuCloud | None:
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
    # 检查是否启用自动刷新
    if not plugin.config.auto_refresh_enabled:
        logger.debug("自动刷新凭证已禁用")
        return False
    
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


@router.get("/api/homes")
async def get_homes():
    """获取家庭列表"""
    cloud = await _get_cloud_client()
    if not cloud:
        raise HTTPException(status_code=401, detail="未登录")
    
    try:
        result = await cloud.list_home()
        
        # 如果是 token 错误，尝试刷新凭证后重试
        if result.is_token_error:
            if await _refresh_credentials(cloud):
                result = await cloud.list_home()
        
        if not result.success or not result.data:
            raise HTTPException(status_code=500, detail="获取家庭列表失败")
        
        # 转换为列表格式
        home_list = [{"id": k, "name": v} for k, v in result.data.items()]
        return {"homes": home_list}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取家庭列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取家庭列表失败: {str(e)}")


@router.get("/api/devices/{home_id}")
async def get_devices(home_id: int):
    """获取设备列表"""
    cloud = await _get_cloud_client()
    if not cloud:
        raise HTTPException(status_code=401, detail="未登录")
    
    try:
        result = await cloud.list_appliances(home_id)
        
        # 如果是 token 错误，尝试刷新凭证后重试
        if result.is_token_error:
            if await _refresh_credentials(cloud):
                result = await cloud.list_appliances(home_id)
        
        if not result.success or not result.data:
            raise HTTPException(status_code=500, detail="获取设备列表失败")
        
        # 转换为列表格式，添加设备类型名称
        device_list = []
        for device_id, info in result.data.items():
            device_list.append({
                "id": device_id,
                "name": info["name"],
                "type": info["type"],
                "type_hex": info["type_hex"],
                "type_name": get_device_type_name(info["type"]),
                "model": info["model"],
                "online": info["online"],
                "room": info["room"],
            })
        
        return {"devices": device_list}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取设备列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取设备列表失败: {str(e)}")
