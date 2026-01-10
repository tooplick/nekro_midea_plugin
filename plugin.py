"""
Nekro Agent 美的控制插件
"""

from nekro_agent.api.plugin import NekroPlugin, ConfigBase, ExtraField
from nekro_agent.api.schemas import AgentCtx
from pydantic import Field


plugin = NekroPlugin(
    name="美的智能家居控制",
    module_name="nekro_midea_plugin",
    description="给予AI助手通过美的云控制智能家居设备的能力",
    version="1.3.2",
    author="GeQian",
    url="https://github.com/tooplick/nekro_midea_plugin",
)


@plugin.mount_config()
class MideaPluginConfig(ConfigBase):
    """美的智能家居插件配置"""

    allowed_users: str = Field(
        default="",
        title="允许使用的用户QQ号列表",
        description="逗号分隔的 QQ 号（如：12345678,87654321），留空表示允许所有人使用",
        json_schema_extra=ExtraField(
            placeholder="例如: 12345678,87654321"
        ).model_dump()
    )


# 获取配置实例
config: MideaPluginConfig = plugin.get_config(MideaPluginConfig)


@plugin.mount_prompt_inject_method(
    name="midea_usage_hint",
    description="美的设备控制使用提示"
)
async def inject_midea_hint(_ctx: AgentCtx) -> str:
    """注入美的设备控制的使用提示"""
    return """【美的智能家居控制提示】
调用美的设备控制方法后，根据返回值用自然语言回复用户：
- ok: 操作成功
- error:device_offline: 设备离线
- error:not_logged_in: 未登录美的账号
- error:invalid_xxx: 参数错误
"""


@plugin.mount_cleanup_method()
async def clean_up():
    """清理插件资源"""
    print("美的插件资源已清理")


# 导入控制器模块以注册沙箱方法
# 必须在 plugin 定义之后导入，否则会导致循环导入
from . import controllers  # noqa: E402, F401
