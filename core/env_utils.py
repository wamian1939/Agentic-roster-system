"""
轻量 .env 加载器（避免额外依赖）
"""
import os
from pathlib import Path


def load_project_env(project_root: Path) -> None:
    env_path = project_root / ".env"
    if not env_path.exists():
        return

    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        # 项目 .env 优先，避免终端残留旧值导致读取错误 key
        os.environ[key] = value
