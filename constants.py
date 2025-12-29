"""
常量定义
"""

# KV 存储键名
STORE_KEY_CREDENTIALS = "midea_credentials"

# 云服务配置
CLOUD_CONFIG = {
    "app_key": "46579c15",
    "login_key": "ad0ee21d48a64bf49f4fb583ab76e799",
    "iot_key": bytes.fromhex(format(9795516279659324117647275084689641883661667, 'x')).decode(),
    "hmac_key": bytes.fromhex(format(117390035944627627450677220413733956185864939010425, 'x')).decode(),
    "api_url": "https://mp-prod.smartmidea.net/mas/v5/app/proxy?alias=",
}

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
