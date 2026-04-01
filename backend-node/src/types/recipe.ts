export interface RecipeGenerateRequest {
  ingredients: string[];
  cuisine?: string;
  prep_time?: number;
  servings?: number;
  skill_level?: string;
}