# 美的智能家居控制插件

一个基于 [Nekro Agent](https://github.com/KroMiose/nekro-agent) 框架的美的智能家居控制插件，允许 AI 助手通过美的云控制智能家居设备。

## 功能特点

- 支持多种美的智能设备（空调、风扇、除湿机、加湿器、灯、热水器等）
- 空调支持丰富的控制参数（温度、模式、风速、摆风、预设模式、电辅热、干燥、防直吹）
- 各设备支持完整控制参数（负离子、童锁、灯效、运行模式等）
- 提供 Web 界面用于账号登录和设备管理
- 使用 KV 存储保持登录状态
- 模块化项目结构，易于维护

## 账号登录

### 使用 Web 界面
插件提供了一个 Web 界面用于账号登录和设备查看：
- 启动插件后，访问 [http://<服务器ip:NA端口>plugin/GeQian.nekro_midea_plugin/](../plugins/GeQian.nekro_midea_plugin)
- 输入美的账号（手机号和密码）
- 点击"登录"按钮完成登录

## API 接口

插件提供以下 API 接口：
- `GET /api/status` - 检查登录状态
- `POST /api/login` - 登录美的账号
- `POST /api/logout` - 退出登录
- `GET /api/homes` - 获取家庭列表
- `GET /api/devices/{home_id}` - 获取设备列表

## AI 沙盒方法

> 详细方法参数请参阅 [API_METHODS.md](https://github.com/tooplick/nekro_midea_plugin/blob/main/API_METHODS.md)

Bot 可以通过调用以下方法来控制设备：

| 方法 | 功能 | 主要参数 |
|------|------|----------|
| `get_midea_devices()` | 获取设备列表 | - |
| `control_midea_ac(...)` | 控制空调 | power, temperature, mode, fan_speed, swing_ud/lr, preset_mode, aux_heat |
| `get_midea_ac_status(...)` | 获取空调状态 | device_id |
| `control_midea_fan(...)` | 控制风扇 | power, fan_speed, oscillate, mode, **anion**, **display**, **swing_direction** |
| `control_midea_dehumidifier(...)` | 控制除湿机 | power, target_humidity, mode, fan_speed, **anion**, **child_lock**, **swing_ud** |
| `control_midea_humidifier(...)` | 控制加湿器 | power, target_humidity, mode, **wind_gear**, **net_ions**, **air_dry**, **buzzer** |
| `control_midea_light(...)` | 控制智能灯 | power, brightness, color_temp, **effect**, **rgb_color** |
| `control_midea_water_heater(...)` | 控制热水器 | power, target_temperature, **operation_mode** |
| `control_midea_device(...)` | 通用控制 | device_id, control_params (JSON) |
| `get_midea_device_status(...)` | 通用状态查询 | device_id, query_params (JSON) |

> **加粗** 参数为 v1.2.0 新增

### 使用示例

```python
# 获取设备列表
/exec print(get_midea_devices())

# 空调：制冷模式，26度，节能
/exec control_midea_ac(device_id=12345678, power=1, temperature=26, mode=2, preset_mode="eco")

# 风扇：睡眠模式，开启负离子
/exec control_midea_fan(device_id=12345678, power=1, mode="sleep", anion=1)

# 除湿机：智能模式，目标湿度50%
/exec control_midea_dehumidifier(device_id=12345678, power=1, target_humidity=50, mode="auto")

# 加湿器：手动模式，低档风
/exec control_midea_humidifier(device_id=12345678, power=1, mode="manual", wind_gear="low")

# 灯：亮度80%，暖色温
/exec control_midea_light(device_id=12345678, power=1, brightness=80, color_temp=20)

# 热水器：50度，节能模式
/exec control_midea_water_heater(device_id=12345678, power=1, target_temperature=50, operation_mode="eco")
```

## 支持的设备类型

| 类型代码 | 设备 | 控制支持 |
|----------|------|----------|
| 0xAC | 空调 | ✅ 完整 |
| 0xFA | 风扇 | ✅ 完整 |
| 0xA1 | 除湿机 | ✅ 完整 |
| 0xFD | 加湿器 | ✅ 完整 |
| 0xE2 | 智能灯 | ✅ 完整 |
| 0x40 | 热水器 | ✅ 完整 |
| 0xB6 | 中央空调 | 通用控制 |
| 0xDC | 冰箱 | 通用控制 |

## 项目结构

```
nekro_midea_plugin/
├── __init__.py
├── plugin.py           # 插件定义
├── constants.py        # 常量定义
├── router.py           # API路由
├── midea/              # 云API模块
│   ├── client.py       # 美的云客户端
│   └── security.py     # 加密安全
├── controllers/        # 设备控制器
│   ├── base.py         # 基础方法
│   ├── ac.py           # 空调
│   ├── fan.py          # 风扇
│   ├── dehumidifier.py # 除湿机
│   ├── humidifier.py   # 加湿器
│   ├── light.py        # 灯
│   └── water_heater.py # 热水器
└── web/                # Web界面
```

## 版本历史

### v1.2.0
- 重构项目结构，模块化设计
- 风扇新增：负离子、显示开关、摆风方向
- 除湿机新增：负离子、童锁、摆风
- 加湿器新增：风档、净离子、风干、蜂鸣器
- 灯新增：灯效、RGB颜色
- 热水器新增：运行模式

### v1.1.0
- 空调控制增强（摆风、预设模式、电辅热、干燥、防直吹）

### v1.0.0
- 初始发布版本

## 作者信息

- **作者**：搁浅
- **GitHub**：[https://github.com/tooplick](https://github.com/tooplick)

## 技术致谢

本插件的美的云 API 技术基于 [midea_auto_cloud](https://github.com/sususweet/midea_auto_cloud) 项目。
