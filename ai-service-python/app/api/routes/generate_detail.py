from fastapi import APIRouter, HTTPException
from app.models.schemas import RecipeDetailGenerateRequest, RecipeDetailOutput
from app.services.llm import generate_recipe_detail

router = APIRouter()


@router.post("/generate-detail", response_model=RecipeDetailOutput)
def generate_detail(data: RecipeDetailGenerateRequest):
    try:
        result = generate_recipe_detail(data)
        return RecipeDetailOutput(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))