import os
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class AstraConfig:

    app_name: str = "ASTRA"
    version: str = "4.0.0-dev"
    environment: str = "development"

    max_agent_iterations: int = 10
    max_tool_calls: int = 20
    max_plan_steps: int = 12

    max_document_size_mb: int = 20
    max_document_pages: int = 100

    enable_audit_logging: bool = True
    enable_performance_monitoring: bool = True

    data_dir: Path = BASE_DIR / "data"
    logs_dir: Path = BASE_DIR / "logs"
    documents_dir: Path = BASE_DIR / "data" / "documents"
    vector_dir: Path = BASE_DIR / "data" / "vectors"

    @property
    def gemini_api_key(self):
        return os.getenv("GEMINI_API_KEY", "")

    @property
    def openai_api_key(self):
        return os.getenv("OPENAI_API_KEY", "")

    @property
    def anthropic_api_key(self):
        return os.getenv("ANTHROPIC_API_KEY", "")


config = AstraConfig()


def initialize_directories():

    directories = [
        config.data_dir,
        config.logs_dir,
        config.documents_dir,
        config.vector_dir
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    initialize_directories()
    print(f"{config.app_name} {config.version}")
