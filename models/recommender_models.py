from pydantic import BaseModel

class RecommenderInput(BaseModel):
    ciudad: str
    criterios_usuario: dict
