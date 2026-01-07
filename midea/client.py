"""
美的美居云 API 客户端
"""

import time
import datetime
import json
import traceback
from dataclasses import dataclass
from secrets import token_hex

import httpx

from ..constants import CLOUD_CONFIG
from .security import MeijuCloudSecurity


# 美的 API 错误码
ERROR_CODE_OK = 0
ERROR_CODE_TOKEN_EXPIRED = 40004  # token 过期
ERROR_CODE_TOKEN_INVALID = 40001  # token 无效
ERROR_CODE_TOKEN_NOT_EXIST = 40002  # token 不存在
ERROR_CODES_TOKEN_ISSUES = {ERROR_CODE_TOKEN_EXPIRED, ERROR_CODE_TOKEN_INVALID, ERROR_CODE_TOKEN_NOT_EXIST}


@dataclass
class ApiResult:
    """API 请求结果"""
    success: bool
    data: dict | None = None
    error_code: int = 0
    error_message: str = ""
    
    @property
    def is_token_error(self) -> bool:
        """是否为 token 相关错误（需要刷新凭证）"""
        return self.error_code in ERROR_CODES_TOKEN_ISSUES


class MeijuCloud:
    """美的美居云 API 客户端"""
    
    APP_ID = "900"
    APP_VERSION = "8.20.0.2"

    def __init__(self, account: str, password: str):
        """
        初始化美的美居云客户端
        
        Args:
            account: 美的账号（手机号或邮箱）
            password: 密码
        """
        self._security = MeijuCloudSecurity(
            login_key=CLOUD_CONFIG["login_key"],
            iot_key=CLOUD_CONFIG["iot_key"],
            hmac_key=CLOUD_CONFIG["hmac_key"],
        )
        self._app_key = CLOUD_CONFIG["app_key"]
        self._account = account
        self._password = password
        self._api_url = CLOUD_CONFIG["api_url"]
        
        self._device_id = self._security.get_deviceid(account)
        self._access_token = None
        self._login_id = None
        self._homegroup_id = None
        self._aes_key = None  # 保存用于序列化

    def get_credentials(self) -> dict | None:
        """获取当前凭证用于存储"""
        if not self._access_token:
            return None
        return {
            "access_token": self._access_token,
            "aes_key": self._aes_key,
            "account": self._account,
            "password": self._password,  # 保存密码用于自动刷新
        }

    def load_credentials(self, creds: dict) -> bool:
        """从存储加载凭证"""
        if not creds:
            return False
        self._access_token = creds.get("access_token")
        self._aes_key = creds.get("aes_key")
        if creds.get("password"):
            self._password = creds.get("password")
        if self._aes_key:
            self._security.set_aes_keys(self._aes_key, None)
        return bool(self._access_token)

    async def _api_request(self, endpoint: str, data: dict, header=None, method="POST") -> ApiResult:
        """发送 API 请求
        
        Returns:
            ApiResult: 包含成功状态、数据、错误码等信息
        """
        header = header or {}
        if not data.get("reqId"):
            data["reqId"] = token_hex(16)
        if not data.get("stamp"):
            data["stamp"] = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        
        random = str(int(time.time()))
        url = self._api_url + endpoint
        dump_data = json.dumps(data)
        sign = self._security.sign(dump_data, random)
        
        header.update({
            "content-type": "application/json; charset=utf-8",
            "secretVersion": "1",
            "sign": sign,
            "random": random,
        })
        if self._access_token:
            header["accesstoken"] = self._access_token

        try:
            import logging
            logging.debug(f"正在请求 {url}")
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.request(method, url, headers=header, content=dump_data)
                logging.debug(f"API 响应状态码: {r.status_code}")
                try:
                    response = r.json()
                except Exception as json_err:
                    return ApiResult(
                        success=False, 
                        error_code=-2, 
                        error_message=f"JSON解析失败 (status={r.status_code}): {json_err}"
                    )
        except Exception as e:
            traceback.print_exc()
            return ApiResult(success=False, error_code=-1, error_message=str(e))

        code = int(response.get("code", -1))
        if code == ERROR_CODE_OK:
            return ApiResult(success=True, data=response.get("data", {"message": "ok"}))
        else:
            return ApiResult(
                success=False, 
                error_code=code, 
                error_message=response.get("msg", "Unknown error")
            )

    async def _get_login_id(self) -> str | None:
        """获取登录 ID"""
        data = {
            "loginAccount": self._account,
            "type": "1",
        }
        result = await self._api_request("/v1/user/login/id/get", data)
        return result.data.get("loginId") if result.success and result.data else None

    async def login(self) -> tuple[bool, str]:
        """
        登录美的云
        
        Returns:
            (成功标志, 消息)
        """
        login_id = await self._get_login_id()
        if not login_id:
            return False, "获取登录ID失败"
        
        self._login_id = login_id
        stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        
        data = {
            "iotData": {
                "clientType": 1,
                "deviceId": self._device_id,
                "iampwd": self._security.encrypt_iam_password(self._login_id, self._password),
                "iotAppId": self.APP_ID,
                "loginAccount": self._account,
                "password": self._security.encrypt_password(self._login_id, self._password),
                "reqId": token_hex(16),
                "stamp": stamp
            },
            "data": {
                "appKey": self._app_key,
                "deviceId": self._device_id,
                "platform": 2
            },
            "timestamp": stamp,
            "stamp": stamp
        }
        
        result = await self._api_request("/mj/user/login", data)
        if result.success and result.data:
            try:
                self._access_token = result.data["mdata"]["accessToken"]
                self._aes_key = self._security.aes_decrypt_with_fixed_key(result.data["key"])
                self._security.set_aes_keys(self._aes_key, None)
                return True, "登录成功"
            except KeyError as e:
                return False, f"解析登录响应失败: {e}"
        return False, f"登录失败: {result.error_message or '请检查账号密码'}"

    async def list_home(self) -> ApiResult:
        """获取家庭列表
        
        Returns:
            ApiResult: 成功时 data 包含 {home_id: home_name} 字典
        """
        result = await self._api_request("/v1/homegroup/list/get", {})
        if result.success and result.data:
            homes = {}
            for home in result.data.get("homeList", []):
                homes[int(home["homegroupId"])] = home["name"]
            return ApiResult(success=True, data=homes)
        return result

    async def list_appliances(self, home_id: int) -> ApiResult:
        """获取设备列表
        
        Returns:
            ApiResult: 成功时 data 包含设备字典 {device_id: device_info}
        """
        self._homegroup_id = str(home_id)
        result = await self._api_request("/v1/appliance/home/list/get", {"homegroupId": home_id})
        
        if result.success and result.data:
            appliances = {}
            for home in result.data.get("homeList") or []:
                for room in home.get("roomList") or []:
                    for appliance in room.get("applianceList") or []:
                        try:
                            sn = ""
                            if appliance.get("sn"):
                                sn = self._security.aes_decrypt(appliance.get("sn"))
                        except:
                            sn = ""
                        
                        device_info = {
                            "name": appliance.get("name"),
                            "type": int(appliance.get("type"), 16),
                            "type_hex": appliance.get("type"),
                            "sn": sn,
                            "sn8": appliance.get("sn8", "00000000") or "00000000",
                            "model": appliance.get("productModel") or appliance.get("sn8", ""),
                            "online": appliance.get("onlineStatus") == "1",
                            "room": room.get("name", "未知房间"),
                        }
                        appliances[int(appliance["applianceCode"])] = device_info
            return ApiResult(success=True, data=appliances)
        return result

    async def get_device_status(self, appliance_code: int, query: dict) -> ApiResult:
        """
        获取设备状态
        
        Args:
            appliance_code: 设备 ID
            query: 查询参数字典，如 {"Power": {}, "SetTemperature": {}}
            
        Returns:
            ApiResult: 成功时 data 包含设备状态字典
        """
        data = {
            "applianceCode": str(appliance_code),
            "command": {
                "query": query
            }
        }
        return await self._api_request("/mjl/v1/device/status/lua/get", data)

    async def send_device_control(self, appliance_code: int, control: dict, status: dict | None = None) -> ApiResult:
        """
        发送设备控制命令
        
        Args:
            appliance_code: 设备 ID
            control: 控制命令字典，如 {"Power": 1, "SetTemperature": 26}
            status: 当前状态字典（可选）
            
        Returns:
            ApiResult: 包含操作结果
        """
        data = {
            "applianceCode": str(appliance_code),
            "command": {
                "control": control
            }
        }
        if status and isinstance(status, dict):
            data["command"]["status"] = status
        return await self._api_request("/mjl/v1/device/lua/control", data)
