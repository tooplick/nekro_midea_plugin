from .plugin import plugin
from fastapi import APIRouter

__all__ = ["plugin"]

@plugin.mount_router()
def create_router() -> APIRouter:
    """创建并配置插件路由"""
    from .router import router
    return router
