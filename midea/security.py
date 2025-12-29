"""
美的美居云安全类 - 处理加密、签名等
"""

from hashlib import md5, sha256
import hmac

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad


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
