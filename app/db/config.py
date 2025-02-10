from pydantic import BaseSettings


class DBSettings(BaseSettings):
    pg_username: str = "postgres"
    pg_password: str = "postgres"
    db_name: str = "invoicing"
    pg_host: str = "localhost"
    pg_port: int = 5432
    DATABASE_URL: str = None  # Default env name for digital ocean url

    class Config:
        env_file = ".env"
        case_sensitive = False


config = DBSettings()
