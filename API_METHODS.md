# 美的智能家居控制 - AI 沙盒方法文档

本文档详细说明了插件提供给 AI 调用的所有沙盒方法。

## 设备查询方法

### get_midea_devices()

获取所有已绑定的美的智能设备列表。

```python
# 示例
result = get_midea_devices()
```

**返回值**：格式化的设备列表文本，包含家庭、设备名称、设备ID、类型、状态等信息。

---

## 空调控制方法

### control_midea_ac()

控制美的空调设备。

| 参数 | 类型 | 说明 | 取值范围 |
|------|------|------|----------|
| `device_id` | int | 设备ID | 必填 |
| `power` | int | 电源开关 | 0=关, 1=开 |
| `temperature` | int | 设定温度 | 16-30°C |
| `mode` | int | 运行模式 | 1=自动, 2=制冷, 3=除湿, 4=送风, 5=制热 |
| `fan_speed` | int | 风速 | 0=自动, 1-7=手动档位 |
| `swing_ud` | int | 上下摆风 | 0=关, 1=开 |
| `swing_lr` | int | 左右摆风 | 0=关, 1=开 |
| `preset_mode` | str | 预设模式 | "none", "eco", "comfort", "boost" |
| `aux_heat` | int | 电辅热(PTC) | 0=关, 1=开 |
| `dry` | int | 干燥模式 | 0=关, 1=开 |
| `prevent_straight_wind` | int | 防直吹 | 0=关, 1=开 |

```python
# 示例：制冷模式，26度，自动风速
control_midea_ac(device_id=12345678, power=1, temperature=26, mode=2, fan_speed=0)

# 示例：节能模式
control_midea_ac(device_id=12345678, preset_mode="eco")
```

### get_midea_ac_status()

获取空调当前状态。

| 参数 | 类型 | 说明 |
|------|------|------|
| `device_id` | int | 设备ID |

```python
# 示例
status = get_midea_ac_status(device_id=12345678)
```

---

## 风扇控制方法

### control_midea_fan()

控制美的风扇设备。

| 参数 | 类型 | 说明 | 取值范围 |
|------|------|------|----------|
| `device_id` | int | 设备ID | 必填 |
| `power` | int | 电源开关 | 0=关, 1=开 |
| `fan_speed` | int | 风速 | 1-100（型号不同范围不同） |
| `oscillate` | int | 摇头 | 0=关, 1=开 |
| `mode` | str | 模式 | "normal", "sleep", "baby", "natural" |
| `anion` | int | 负离子 | 0=关, 1=开 |
| `display` | int | 显示屏 | 0=关, 1=开 |
| `swing_direction` | str | 摆风方向 | "off", "horizontal", "vertical", "both" |

```python
# 示例：开启风扇，3档，开启摇头
control_midea_fan(device_id=12345678, power=1, fan_speed=3, oscillate=1)

# 示例：睡眠模式，开启负离子
control_midea_fan(device_id=12345678, mode="sleep", anion=1)
```

---

## 除湿机控制方法

### control_midea_dehumidifier()

控制美的除湿机设备。

| 参数 | 类型 | 说明 | 取值范围 |
|------|------|------|----------|
| `device_id` | int | 设备ID | 必填 |
| `power` | int | 电源开关 | 0=关, 1=开 |
| `target_humidity` | int | 目标湿度 | 35-85% |
| `mode` | str | 模式 | "continuity", "auto", "fan", "dry_shoes", "dry_clothes" |
| `fan_speed` | str | 风速 | "low", "high" |
| `anion` | int | 负离子 | 0=关, 1=开 |
| `child_lock` | int | 童锁 | 0=关, 1=开 |
| `swing_ud` | int | 上下摆风 | 0=关, 1=开 |

```python
# 示例：智能模式，目标湿度50%
control_midea_dehumidifier(device_id=12345678, power=1, target_humidity=50, mode="auto")

# 示例：干衣模式
control_midea_dehumidifier(device_id=12345678, mode="dry_clothes")
```

---

## 加湿器控制方法

### control_midea_humidifier()

控制美的加湿器设备。

| 参数 | 类型 | 说明 | 取值范围 |
|------|------|------|----------|
| `device_id` | int | 设备ID | 必填 |
| `power` | int | 电源开关 | 0=关, 1=开 |
| `target_humidity` | int | 目标湿度 | 30-80% |
| `mode` | str | 模式 | "manual", "moist_skin", "sleep" |
| `wind_gear` | str | 风档 | "low", "medium", "high", "auto" |
| `net_ions` | int | 净离子 | 0=关, 1=开 |
| `air_dry` | int | 风干功能 | 0=关, 1=开 |
| `buzzer` | int | 蜂鸣器 | 0=关, 1=开 |

```python
# 示例：手动模式，目标湿度60%，低档风
control_midea_humidifier(device_id=12345678, power=1, target_humidity=60, mode="manual", wind_gear="low")

# 示例：睡眠模式，开启净离子
control_midea_humidifier(device_id=12345678, mode="sleep", net_ions=1)
```

---

## 智能灯控制方法

### control_midea_light()

控制美的智能灯设备。

| 参数 | 类型 | 说明 | 取值范围 |
|------|------|------|----------|
| `device_id` | int | 设备ID | 必填 |
| `power` | int | 电源开关 | 0=关, 1=开 |
| `brightness` | int | 亮度 | 1-100% |
| `color_temp` | int | 色温 | 0=暖光(2700K), 100=冷光(6500K) |
| `effect` | str | 灯效 | "none", "colorloop", "flash" |
| `rgb_color` | str | RGB颜色 | "R,G,B" 格式，如 "255,0,0" |

```python
# 示例：开灯，亮度80%，暖色温
control_midea_light(device_id=12345678, power=1, brightness=80, color_temp=20)

# 示例：设置红色
control_midea_light(device_id=12345678, rgb_color="255,0,0")
```

---

## 热水器控制方法

### control_midea_water_heater()

控制美的热水器设备。

| 参数 | 类型 | 说明 | 取值范围 |
|------|------|------|----------|
| `device_id` | int | 设备ID | 必填 |
| `power` | int | 电源开关 | 0=关, 1=开 |
| `target_temperature` | int | 目标温度 | 35-75°C |
| `operation_mode` | str | 运行模式 | "normal", "eco", "boost", "vacation" |

```python
# 示例：开启热水器，50度
control_midea_water_heater(device_id=12345678, power=1, target_temperature=50)

# 示例：节能模式
control_midea_water_heater(device_id=12345678, operation_mode="eco")
```

---

## 通用控制方法

### control_midea_device()

通用设备控制，可发送任意控制参数。

| 参数 | 类型 | 说明 |
|------|------|------|
| `device_id` | int | 设备ID |
| `control_params` | str | JSON格式的控制参数 |

```python
# 示例
control_midea_device(device_id=12345678, control_params='{"Power": 1, "Mode": 2}')
```

### get_midea_device_status()

通用设备状态查询。

| 参数 | 类型 | 说明 |
|------|------|------|
| `device_id` | int | 设备ID |
| `query_params` | str | JSON格式的查询参数 |

```python
# 示例
status = get_midea_device_status(device_id=12345678, query_params='{}')
```

---

## 返回值说明

所有控制方法的返回值格式：

| 返回值 | 说明 |
|--------|------|
| `"ok"` | 控制成功 |
| `"error:not_logged_in"` | 未登录美的账号 |
| `"error:device_offline"` | 设备离线 |
| `"error:invalid_xxx"` | 参数无效 |
| `"error:no_params"` | 未提供任何控制参数 |
| `"error:exception:..."` | 发生异常 |
