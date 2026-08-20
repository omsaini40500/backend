from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra='ignore', env_file='.env')

    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://localhost:8443,https://task-management-system-eight-vert.vercel.app"
    secret_key: str = "supersecretkey"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 8
    database_url: str = "mysql+pymysql://root:root@localhost:3306/flash_agency"

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@flashcommunications.com"
    smtp_from_name: str = "Flash Communications"
    super_admin_email: str = "omsaini40500@gmail.com"

def get_settings():
    return Settings()
