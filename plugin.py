"""
Nekro Agent 美的控制插件
"""

from nekro_agent.api.plugin import NekroPlugin, ConfigBase
from nekro_agent.api.schemas import AgentCtx
from pydantic import Field


plugin = NekroPlugin(
    name="美的智能家居控制",
    module_name="nekro_midea_plugin",
    description="给予AI助手通过美的云控制智能家居设备的能力",
    version="1.3.0",
    author="GeQian",
    url="https://github.com/tooplick/nekro_midea_plugin",
)


@plugin.mount_config()
class MideaPluginConfig(ConfigBase):
    """美的插件配置"""
    
    auto_refresh_enabled: bool = Field(
        default=True,
        title="凭证自动刷新",
        description="当登录状态失效时，自动使用保存的账号密码重新登录"
    )


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
