import axios from "axios";
import type { RecipeGenerateRequest } from "../types/recipe.js";

const AI_BASE_URL = process.env.AI_BASE_URL || "http://127.0.0.1:8001";

export const callGenerateRecipe = async (payload: RecipeGenerateRequest) => {
  const response = await axios.post(`${AI_BASE_URL}/generate`, payload, {
    timeout: 120000,
  });

  return response.data;
};