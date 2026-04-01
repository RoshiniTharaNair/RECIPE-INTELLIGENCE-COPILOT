from fastapi import APIRouter, HTTPException

from app.models.schemas import RecipeGenerateRequest, RecipeSearchResponse
from app.services.retriever import retrieve_with_fallback_signal

router = APIRouter()


@router.post("/retrieve", response_model=RecipeSearchResponse)
def retrieve(data: RecipeGenerateRequest):
    try:
        retrieval_result = retrieve_with_fallback_signal(data, top_k=10)

        return {
            "mode": "retrieval",
            "recipes": retrieval_result["recipes"],
            "generated_recipes": [],
            "meta": {
                "recipe_count": len(retrieval_result["recipes"]),
                "source": "local_dataset_retrieval_summary_only",
                "fallback_reason": retrieval_result["fallback_reason"],
                "fallback_suggested": retrieval_result["fallback_needed"],
                "confidence_score": retrieval_result["confidence_score"],
                "confidence_level": retrieval_result["confidence_level"],
                "confidence_reasons": retrieval_result["confidence_reasons"],
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))