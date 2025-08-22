from fastapi import FastAPI
import uvicorn
from api.routes import router as api_router
from config.app import settings

def startup():
    app = FastAPI()
    app.title = settings.PROJECT_NAME
    app.version = settings.VERSION
    app.include_router(api_router, prefix=settings.API_PREFIX)
    return app

app = startup()

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API de Recomendación de Zonas HabitAI"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
