import type { Request, Response } from "express";
import { callGenerateRecipe } from "../clients/aiClient.js";

export const generateRecipe = async (req: Request, res: Response) => {
  try {
    const result = await callGenerateRecipe(req.body);
    res.json({
      success: true,
      data: result,
    });
  } catch (error: any) {
    res.status(500).json({
      success: false,
      message: error?.response?.data || error.message || "Recipe generation failed",
    });
  }
};