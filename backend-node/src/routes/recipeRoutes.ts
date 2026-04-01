import { Router } from "express";
import { generateRecipe } from "../controllers/recipeController.js";

const router = Router();

router.post("/generate", generateRecipe);

export default router;