import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "Api HabitAI"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    API_VERSION: str = "v1"

    # Ejemplo de variable de entorno
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")

settings = Settings()
