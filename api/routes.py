from fastapi import APIRouter
from models.recommender_models import RecommenderInput
from services.recommender_score_feedback_service import RecommenderScoreFeedbackService

router = APIRouter()

service = RecommenderScoreFeedbackService()

@router.get("/health")
def check_health():
    return {"message": "pong!"}

@router.post("/zonas")
async def search_zonas(data: RecommenderInput):
    return service.recomendar(
        ciudad=data.ciudad,
        criterios_usuario=data.criterios_usuario
    )
