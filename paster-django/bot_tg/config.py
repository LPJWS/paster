import os


class Settings:
    TG_TOKEN = os.getenv("TG_BOT_TOKEN")
    ADMIN_ID = int(os.getenv("TG_ADMIN_ID", default="333565432"))


settings = Settings()
