"""应用配置：路径与 AI 接口参数（.env）。"""

from pathlib import Path

from pydantic_settings import BaseSettings

# 项目根目录（app/ 的上一级）
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # SQLite 数据库文件，默认在项目根 data/ 下
    db_path: Path = BASE_DIR / "data" / "law_study.db"

    # OpenAI 兼容接口（智谱/方舟等任何网关）
    ai_base_url: str = ""
    ai_api_key: str = ""
    ai_model: str = ""

    model_config = {"env_file": BASE_DIR / ".env", "env_file_encoding": "utf-8"}


settings = Settings()
