from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class RecipeGenerateRequest(BaseModel):
    ingredients: List[str]
    cuisine: Optional[str] = None
    prep_time: Optional[int] = None
    servings: Optional[int] = None
    skill_level: Optional[str] = None


class IngredientItem(BaseModel):
    name: str
    quantity: str


class NutritionSummary(BaseModel):
    calories: Optional[int] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fats_g: Optional[float] = None


class RecipeOutput(BaseModel):
    title: str
    why_chosen: str
    ingredients: List[IngredientItem] = Field(default_factory=list)
    steps: List[str] = Field(default_factory=list)
    substitutions: List[str] = Field(default_factory=list)
    nutrition_summary: NutritionSummary = Field(default_factory=NutritionSummary)
    warnings: List[str] = Field(default_factory=list)
    match_score: float = 0.0
    matched_input_ingredients: List[str] = Field(default_factory=list)
    extra_major_ingredients: List[str] = Field(default_factory=list)
    template_name: str = ""
    grounding_source: str = ""


class ResponseMeta(BaseModel):
    latency_ms: int
    model_name: str
    recipe_count: int
    input_ingredients: List[str] = Field(default_factory=list)
    quality_notes: List[str] = Field(default_factory=list)


class RecipeListOutput(BaseModel):
    recipes: List[RecipeOutput] = Field(default_factory=list)
    meta: ResponseMeta


class RecipeDetailGenerateRequest(BaseModel):
    recipe_id: str
    servings: Optional[int] = None
    skill_level: Optional[str] = None
    user_ingredients: List[str] = Field(default_factory=list)


class RecipeDetailOutput(BaseModel):
    title: str
    why_chosen: str
    ingredients: List[IngredientItem] = Field(default_factory=list)
    steps: List[str] = Field(default_factory=list)
    substitutions: List[str] = Field(default_factory=list)
    nutrition_summary: NutritionSummary = Field(default_factory=NutritionSummary)
    warnings: List[str] = Field(default_factory=list)
    source_recipe_title: str = ""
    grounded: bool = True


class RecipeSummaryOutput(BaseModel):
    id: str
    title: str
    description: str = ""
    cuisine: str = ""
    prep_time_mins: Optional[int] = None
    total_time_mins: Optional[int] = None
    servings: Optional[int] = None
    match_score: float = 0.0
    why_chosen: str = ""
    matched_input_ingredients: List[str] = Field(default_factory=list)
    extra_major_count: int = 0

    confidence_score: float = 0.0
    confidence_level: str = "low"
    confidence_reasons: List[str] = Field(default_factory=list)


class RetrieveMeta(BaseModel):
    recipe_count: int
    source: str
    fallback_reason: Optional[str] = None
    fallback_suggested: bool = False
    confidence_score: float = 0.0
    confidence_level: str = "low"
    confidence_reasons: List[str] = Field(default_factory=list)


class RecipeRetrieveResponse(BaseModel):
    recipes: List[RecipeSummaryOutput] = Field(default_factory=list)
    meta: RetrieveMeta


class RecipeSearchResponse(BaseModel):
    mode: str
    recipes: List[RecipeSummaryOutput] = Field(default_factory=list)
    generated_recipes: List[RecipeOutput] = Field(default_factory=list)
    meta: RetrieveMeta