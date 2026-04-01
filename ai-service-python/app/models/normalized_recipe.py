from pydantic import BaseModel, Field
from typing import List, Optional


class NormalizedRecipe(BaseModel):
    id: str
    title: str
    description: str = ""
    cuisine: str = ""
    dietary_info: List[str] = Field(default_factory=list)
    spice_level: str = ""
    prep_time_mins: Optional[int] = None
    cook_time_mins: Optional[int] = None
    total_time_mins: Optional[int] = None
    servings: Optional[int] = None
    ingredients: List[str] = Field(default_factory=list)
    instructions: List[str] = Field(default_factory=list)
    rating: Optional[float] = None
    review_count: Optional[int] = None
    popularity: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    source: str