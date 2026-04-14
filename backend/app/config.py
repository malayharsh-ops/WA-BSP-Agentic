from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Anthropic
    anthropic_api_key: str = ""

    # Meta WhatsApp
    meta_whatsapp_token: str = ""
    meta_phone_number_id: str = ""
    meta_verify_token: str = "jsw_verify"
    meta_app_secret: str = ""

    # Database
    database_url: str = "postgresql://jsw:jsw@db:5432/jswmsme"
    redis_url: str = "redis://redis:6379/0"

    # Salesforce
    salesforce_client_id: str = ""
    salesforce_client_secret: str = ""
    salesforce_instance_url: str = ""
    salesforce_enabled: bool = False

    # App
    secret_key: str = "change-me"
    environment: str = "development"
    cors_origins: str = "http://localhost:3000"

    # Business hours
    business_hours_start: int = 9
    business_hours_end: int = 19
    handoff_sla_minutes: int = 30

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
