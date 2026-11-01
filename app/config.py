from decimal import Decimal
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    database_url: str | None = None
    supabase_db_url: str | None = None
    free_needs_percent: Decimal = Decimal('50')
    free_investment_percent: Decimal = Decimal('30')
    free_savings_percent: Decimal = Decimal('20')
    ai_provider: str = 'disabled'
    ai_model: str = ''
    ai_api_key: str = ''
    payment_provider: str = 'disabled'
    payment_webhook_secret: str = ''
    supabase_url: str = ''
    supabase_anon_key: str = ''
    supabase_service_role_key: str = ''
    allow_dev_admin_header: bool = False

    @property
    def resolved_database_url(self) -> str:
        return self.supabase_db_url or self.database_url or 'sqlite:///./techspot.db'

    def allocation(self) -> dict[str, Decimal]:
        values = {'needs': self.free_needs_percent, 'investment': self.free_investment_percent, 'savings': self.free_savings_percent}
        if sum(values.values()) != Decimal('100'):
            raise ValueError('allocation percentages must total 100%')
        return values

settings = Settings()
