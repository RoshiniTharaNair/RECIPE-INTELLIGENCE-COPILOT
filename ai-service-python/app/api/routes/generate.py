from fastapi import APIRouter, HTTPException
from app.models.schemas import RecipeGenerateRequest, RecipeListOutput
from app.services.generator import generate_recipes

router = APIRouter()


@router.post("/generate", response_model=RecipeListOutput)
def generate(data: RecipeGenerateRequest):
    try:
        return generate_recipes(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))