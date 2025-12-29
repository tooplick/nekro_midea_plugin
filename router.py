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


@router.get("/api/homes")
async def get_homes():
    """获取家庭列表"""
    cloud = await _get_cloud_client()
    if not cloud:
        raise HTTPException(status_code=401, detail="未登录")
    
    try:
        homes = await cloud.list_home()
        if homes is None:
            raise HTTPException(status_code=500, detail="获取家庭列表失败")
        
        # 转换为列表格式
        home_list = [{"id": k, "name": v} for k, v in homes.items()]
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
        appliances = await cloud.list_appliances(home_id)
        if appliances is None:
            raise HTTPException(status_code=500, detail="获取设备列表失败")
        
        # 转换为列表格式，添加设备类型名称
        device_list = []
        for device_id, info in appliances.items():
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
