"""Конфигурация приложения (переменные окружения)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Приложение
    app_name: str = "Colt Super Express API"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"

    # CORS — перечисление origin через запятую (строка, разбивается в свойстве)
    cors_origins: str = "http://localhost:5173"

    # Инфраструктура
    database_url: str = "postgresql+asyncpg://colt:colt@localhost:5432/colt_super_express"
    redis_url: str = "redis://localhost:6379/0"

    # Игра
    planning_timeout_seconds: float = 320.0
    step_delay_seconds: float = 2.0

    @property
    def cors_origins_list(self) -> list[str]:
        """Список разрешённых origin (разбиение строки по запятой)."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Возвращает кэшированный экземпляр настроек."""
    return Settings()