"""WebDAV 同步（stub）

首版：简单 LWW（Last-Write-Wins），基于 updated_at 时间戳。
⚠️ 多设备同时修改同一事件会丢数据，后续升级字段级合并。
"""


class SyncService:
    """WebDAV 同步服务 — 首版 stub，不执行实际同步。"""

    def __init__(self, url: str = "", username: str = "", password: str = ""):
        self.url = url
        self.username = username
        self.password = password
        self._enabled = False

    def configure(self, url: str, username: str, password: str):
        self.url = url
        self.username = username
        self.password = password
        self._enabled = bool(url)

    @property
    def enabled(self) -> bool:
        return self._enabled

    def push(self) -> dict:
        """上传本地变更到 WebDAV — stub"""
        return {"status": "stub", "message": "同步功能开发中"}

    def pull(self) -> dict:
        """从 WebDAV 拉取远端变更 — stub"""
        return {"status": "stub", "message": "同步功能开发中"}

    def sync(self) -> dict:
        """双向同步 — stub"""
        return {"status": "stub", "message": "同步功能开发中"}
