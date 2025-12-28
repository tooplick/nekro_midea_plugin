# 美的智能家居控制插件

一个基于 [Nekro Agent](https://github.com/KroMiose/nekro-agent) 框架的美的智能家居控制插件，允许 AI 助手通过美的云控制智能家居设备。

## 功能特点

- 支持多种美的智能设备（空调、风扇、除湿机、加湿器、灯、热水器等）
- 空调支持丰富的控制参数（温度、模式、风速、摆风、预设模式、电辅热、干燥、防直吹）
- 提供 Web 界面用于账号登录和设备管理
- 使用 KV 存储保持登录状态
- 异步处理所有网络请求

## 账号登录

### 使用 Web 界面
插件提供了一个 Web 界面用于账号登录和设备查看：
- 启动插件后，访问 [http://<服务器ip:NA端口>plugin/GeQian.nekro_midea_plugin/](../plugins/GeQian.nekro_midea_plugin)
- 输入美的账号（手机号或邮箱）和密码
- 点击"登录"按钮完成登录

## API 接口

插件提供以下 API 接口：
- `GET /api/status` - 检查登录状态
- `POST /api/login` - 登录美的账号
- `POST /api/logout` - 退出登录
- `GET /api/homes` - 获取家庭列表
- `GET /api/devices/{home_id}` - 获取设备列表

## AI 沙盒方法

Bot 可以通过调用以下方法来控制设备：

| 方法 | 功能 |
|------|------|
| `get_midea_devices()` | 获取设备列表 |
| `control_midea_ac(...)` | 控制空调（详见下方参数表） |
| `get_midea_ac_status(device_id)` | 获取空调状态 |
| `control_midea_fan(device_id, power, fan_speed, oscillate, mode)` | 控制风扇 |
| `control_midea_dehumidifier(device_id, power, target_humidity, mode, fan_speed)` | 控制除湿机 |
| `control_midea_humidifier(device_id, power, target_humidity, mode)` | 控制加湿器 |
| `control_midea_light(device_id, power, brightness, color_temp)` | 控制智能灯 |
| `control_midea_water_heater(device_id, power, target_temperature)` | 控制热水器 |
| `control_midea_device(device_id, control_params)` | 通用控制 |
| `get_midea_device_status(device_id, query_params)` | 通用状态查询 |

### 空调控制参数

| 参数 | 类型 | 说明 | 取值范围 |
|------|------|------|----------|
| `device_id` | int | 设备ID | 通过 get_midea_devices() 获取 |
| `power` | int | 电源开关 | 0=关, 1=开 |
| `temperature` | int | 设定温度 | 16-30°C |
| `mode` | int | 运行模式 | 1=自动, 2=制冷, 3=除湿, 4=送风, 5=制热 |
| `fan_speed` | int | 风速 | 0=自动, 1-7=手动档位 |
| `swing_ud` | int | 上下摆风 | 0=关, 1=开 |
| `swing_lr` | int | 左右摆风 | 0=关, 1=开 |
| `preset_mode` | str | 预设模式 | "none"=正常, "eco"=节能, "comfort"=舒适, "boost"=强劲 |
| `aux_heat` | int | 电辅热(PTC) | 0=关, 1=开 |
| `dry` | int | 干燥模式 | 0=关, 1=开 |
| `prevent_straight_wind` | int | 防直吹 | 0=关, 1=开 |

### 使用示例

```python
# 获取设备列表
/exec print(get_midea_devices())

# 打开空调，制冷模式，26度
/exec control_midea_ac(device_id=12345678, power=1, temperature=26, mode=2)

# 设置节能模式，开启上下摆风
/exec control_midea_ac(device_id=12345678, preset_mode="eco", swing_ud=1)

# 开启电辅热和防直吹
/exec control_midea_ac(device_id=12345678, aux_heat=1, prevent_straight_wind=1)

# 关闭空调
/exec control_midea_ac(device_id=12345678, power=0)
```

## 支持的设备类型

- 空调 (0xAC)
- 风扇 (0xFA)
- 除湿机 (0xA1)
- 加湿器 (0xFD)
- 智能灯 (0xE2)
- 热水器 (0x40)
- 中央空调 (0xB6)
- 冰箱 (0xDC)
- 洗碗机 (0xDB)
- 烘干机 (0xDA)
- 电水壶 (0xED)

## 版本历史

- v1.1.0：空调控制增强
  - 新增摆风控制（上下/左右）
  - 新增预设模式（节能/舒适/强劲）
  - 新增电辅热控制
  - 新增干燥模式
  - 新增防直吹功能
  - 状态查询增加湿度和新功能状态

- v1.0.0：初始发布版本
  - 支持美的账号登录
  - 提供 Web 管理界面
  - 支持多种设备控制

## 作者信息

- **作者**：搁浅
- **GitHub**：[https://github.com/tooplick](https://github.com/tooplick)

## 技术致谢

本插件的美的云 API 技术基于以下项目：
- [midea_auto_cloud](https://github.com/sususweet/midea_auto_cloud) - Home Assistant 美的智能家居集成组件

感谢原项目作者的开源贡献！
