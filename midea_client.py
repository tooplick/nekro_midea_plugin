"""
美的云 API 客户端
"""

import time
import datetime
import json
import traceback
from secrets import token_hex
from hashlib import md5, sha256
import hmac

import httpx
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# 云服务配置
CLOUD_CONFIG = {
    "app_key": "46579c15",
    "login_key": "ad0ee21d48a64bf49f4fb583ab76e799",
    "iot_key": bytes.fromhex(format(9795516279659324117647275084689641883661667, 'x')).decode(),
    "hmac_key": bytes.fromhex(format(117390035944627627450677220413733956185864939010425, 'x')).decode(),
    "api_url": "https://mp-prod.smartmidea.net/mas/v5/app/proxy?alias=",
}


class MeijuCloudSecurity:
    """美的美居云安全类 - 处理加密、签名等"""
    
    FIXED_KEY = format(10864842703515613082, 'x').encode("ascii")
    
    def __init__(self, login_key: str, iot_key: str, hmac_key: str):
        self._login_key = login_key
        self._iot_key = iot_key
        self._hmac_key = hmac_key
        self._aes_key = None
        self._aes_iv = None

    def sign(self, data: str, random: str) -> str:
        """生成 API 请求签名"""
        msg = self._iot_key + data + random
        return hmac.new(self._hmac_key.encode("ascii"), msg.encode("ascii"), sha256).hexdigest()

    def encrypt_password(self, login_id: str, password: str) -> str:
        """加密密码"""
        m = sha256()
        m.update(password.encode("ascii"))
        login_hash = login_id + m.hexdigest() + self._login_key
        m2 = sha256()
        m2.update(login_hash.encode("ascii"))
        return m2.hexdigest()

    def encrypt_iam_password(self, login_id: str, password: str) -> str:
        """加密 IAM 密码"""
        md = md5()
        md.update(password.encode("ascii"))
        md_second = md5()
        md_second.update(md.hexdigest().encode("ascii"))
        return md_second.hexdigest()

    @staticmethod
    def get_deviceid(username: str) -> str:
        """根据用户名生成设备 ID"""
        return md5(f"Hello, {username}!".encode("ascii")).digest().hex()[:16]

    def set_aes_keys(self, key, iv=None):
        """设置 AES 密钥"""
        if isinstance(key, str):
            key = key.encode("ascii")
        if isinstance(iv, str):
            iv = iv.encode("ascii")
        self._aes_key = key
        self._aes_iv = iv

    def aes_decrypt_with_fixed_key(self, data: str) -> str:
        """使用固定密钥解密"""
        if isinstance(data, str):
            data = bytes.fromhex(data)
        return unpad(AES.new(self.FIXED_KEY, AES.MODE_ECB).decrypt(data), len(self.FIXED_KEY)).decode()

    def aes_decrypt(self, data, key=None, iv=None) -> str:
        """AES 解密"""
        aes_key = key if key is not None else self._aes_key
        aes_iv = iv if iv is not None else self._aes_iv
        
        if aes_key is None:
            raise ValueError("Decrypt needs a key")
        if isinstance(data, str):
            data = bytes.fromhex(data)
        if aes_iv is None:
            return unpad(AES.new(aes_key, AES.MODE_ECB).decrypt(data), len(aes_key)).decode()
        else:
            return unpad(AES.new(aes_key, AES.MODE_CBC, iv=aes_iv).decrypt(data), len(aes_key)).decode()


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
        }

    def load_credentials(self, creds: dict) -> bool:
        """从存储加载凭证"""
        if not creds:
            return False
        self._access_token = creds.get("access_token")
        self._aes_key = creds.get("aes_key")
        if self._aes_key:
            self._security.set_aes_keys(self._aes_key, None)
        return bool(self._access_token)

    async def _api_request(self, endpoint: str, data: dict, header=None, method="POST") -> dict | None:
        """发送 API 请求"""
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
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.request(method, url, headers=header, content=dump_data)
                response = r.json()
        except Exception as e:
            traceback.print_exc()
            return None

        if int(response.get("code", -1)) == 0:
            return response.get("data", {"message": "ok"})
        return None

    async def _get_login_id(self) -> str | None:
        """获取登录 ID"""
        data = {
            "loginAccount": self._account,
            "type": "1",
        }
        response = await self._api_request("/v1/user/login/id/get", data)
        return response.get("loginId") if response else None

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
        
        response = await self._api_request("/mj/user/login", data)
        if response:
            try:
                self._access_token = response["mdata"]["accessToken"]
                self._aes_key = self._security.aes_decrypt_with_fixed_key(response["key"])
                self._security.set_aes_keys(self._aes_key, None)
                return True, "登录成功"
            except KeyError as e:
                return False, f"解析登录响应失败: {e}"
        return False, "登录失败，请检查账号密码"

    async def list_home(self) -> dict | None:
        """获取家庭列表"""
        response = await self._api_request("/v1/homegroup/list/get", {})
        if response:
            homes = {}
            for home in response.get("homeList", []):
                homes[int(home["homegroupId"])] = home["name"]
            return homes
        return None

    async def list_appliances(self, home_id: int) -> dict | None:
        """获取设备列表"""
        self._homegroup_id = str(home_id)
        response = await self._api_request("/v1/appliance/home/list/get", {"homegroupId": home_id})
        
        if response:
            appliances = {}
            for home in response.get("homeList") or []:
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
            return appliances
        return None

    async def get_device_status(self, appliance_code: int, query: dict) -> dict | None:
        """
        获取设备状态
        
        Args:
            appliance_code: 设备 ID
            query: 查询参数字典，如 {"Power": {}, "SetTemperature": {}}
            
        Returns:
            设备状态字典，失败返回 None
        """
        data = {
            "applianceCode": str(appliance_code),
            "command": {
                "query": query
            }
        }
        response = await self._api_request("/mjl/v1/device/status/lua/get", data)
        return response

    async def send_device_control(self, appliance_code: int, control: dict, status: dict | None = None) -> bool:
        """
        发送设备控制命令
        
        Args:
            appliance_code: 设备 ID
            control: 控制命令字典，如 {"Power": 1, "SetTemperature": 26}
            status: 当前状态字典（可选）
            
        Returns:
            发送成功返回 True，失败返回 False
        """
        data = {
            "applianceCode": str(appliance_code),
            "command": {
                "control": control
            }
        }
        if status and isinstance(status, dict):
            data["command"]["status"] = status
        response = await self._api_request("/mjl/v1/device/lua/control", data)
        return response is not None


# 设备类型名称映射
DEVICE_TYPE_NAMES = {
    0xAC: "空调",
    0xA1: "除湿机",
    0xCC: "中央空调网关",
    0xFA: "风扇",
    0xFD: "加湿器",
    0xB6: "中央空调",
    0x21: "智能网关",
    0xE2: "灯",
    0x40: "热水器",
    0xED: "电水壶",
    0xDA: "烘干机",
    0xDB: "洗碗机",
    0xDC: "冰箱",
}


def get_device_type_name(device_type: int) -> str:
    """获取设备类型名称"""
    return DEVICE_TYPE_NAMES.get(device_type, f"未知设备(0x{device_type:02X})")
