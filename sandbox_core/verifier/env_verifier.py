# sandbox_core/verifier/env_verifier.py
import hashlib
from pathlib import Path
from typing import Dict, Optional, List


class EnvVerifier:
    """环境/配置正向与逆向验证"""

    def __init__(self, snapshot_dir: Optional[str] = None):
        self.snapshot_dir = snapshot_dir or "/tmp/sandbox_snapshots"
        self._pre_snapshot: Dict[str, str] = {}

    def forward_verify(self, paths: List[str]) -> bool:
        """正向：检查路径存在且可读"""
        for p in paths:
            if not Path(p).exists():
                return False
        return True

    def take_pre_snapshot(self, paths: List[str]) -> bool:
        """正向：记录启动前快照"""
        self._pre_snapshot = {}
        for p in paths:
            if Path(p).exists():
                content = Path(p).read_bytes()
                self._pre_snapshot[p] = hashlib.sha256(content).hexdigest()
        return True

    def reverse_verify(self, paths: List[str]) -> bool:
        """逆向：对比启动前后，检测篡改"""
        for p in paths:
            if p not in self._pre_snapshot:
                continue
            if not Path(p).exists():
                return False
            content = Path(p).read_bytes()
            h = hashlib.sha256(content).hexdigest()
            if h != self._pre_snapshot[p]:
                return False
        return True
