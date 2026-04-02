"use client";

import { useMemo, useState } from "react";
import axios from "axios";

type RecipeSummaryItem = {
  id: string;
  title: string;
  description: string;
  cuisine: string;
  prep_time_mins?: number;
  total_time_mins?: number;
  servings?: number;
  match_score: number;
  why_chosen: string;
  matched_input_ingredients: string[];
  extra_major_count?: number;
  confidence_score?: number;
  confidence_level?: string;
  confidence_reasons?: string[];
};

type GeneratedRecipeItem = {
  title: string;
  why_chosen: string;
  ingredients: { name: string; quantity: string }[];
  steps: string[];
  substitutions: string[];
  nutrition_summary: {
    calories?: number | null;
    protein_g?: number | null;
    carbs_g?: number | null;
    fats_g?: number | null;
  };
  warnings: string[];
  match_score: number;
  matched_input_ingredients: string[];
  extra_major_ingredients: string[];
  template_name?: string;
  grounding_source?: string;
};

type RetrieveResponse = {
  mode: "retrieval";
  recipes: RecipeSummaryItem[];
  generated_recipes: GeneratedRecipeItem[];
  meta: {
    recipe_count: number;
    source: string;
    fallback_reason?: string | null;
    fallback_suggested?: boolean;
    confidence_score?: number;
    confidence_level?: string;
    confidence_reasons?: string[];
    quality_notes?: string[];
    model_name?: string;
    latency_ms?: number;
  };
};

type GenerateResponse = {
  recipes: GeneratedRecipeItem[];
  meta: {
    recipe_count: number;
    source?: string;
    quality_notes?: string[];
    model_name?: string;
    latency_ms?: number;
  };
};

type RecipeDetailItem = {
  title: string;
  why_chosen: string;
  ingredients: { name: string; quantity: string }[];
  steps: string[];
  substitutions: string[];
  nutrition_summary: {
    calories?: number | null;
    protein_g?: number | null;
    carbs_g?: number | null;
    fats_g?: number | null;
  };
  warnings: string[];
  source_recipe_title: string;
  grounded: boolean;
};

function sourceBadgeClass(source?: string) {
  if (source === "retrieval_grounded") {
    return "bg-green-100 text-green-800 border border-green-300";
  }
  if (source === "template_only") {
    return "bg-slate-100 text-slate-800 border border-slate-300";
  }
  return "bg-gray-100 text-gray-800 border border-gray-300";
}

function templateBadgeClass(templateName?: string) {
  if (templateName === "generic_fallback") {
    return "bg-amber-100 text-amber-900 border border-amber-300";
  }
  return "bg-blue-100 text-blue-900 border border-blue-300";
}

export default function HomePage() {
  const [ingredients, setIngredients] = useState("tomato, onion, rice");
  const [cuisine, setCuisine] = useState("Indian");
  const [prepTime, setPrepTime] = useState(30);
  const [servings, setServings] = useState(2);
  const [skillLevel, setSkillLevel] = useState("beginner");

  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [generateLoading, setGenerateLoading] = useState(false);
  const [error, setError] = useState("");

  const [mode, setMode] = useState<"retrieval" | "generation_deterministic" | "">("");
  const [recipes, setRecipes] = useState<RecipeSummaryItem[]>([]);
  const [generatedRecipes, setGeneratedRecipes] = useState<GeneratedRecipeItem[]>([]);
  const [meta, setMeta] = useState<RetrieveResponse["meta"] | null>(null);

  const [selectedRecipeId, setSelectedRecipeId] = useState<string>("");
  const [selectedRecipeDetail, setSelectedRecipeDetail] = useState<RecipeDetailItem | null>(null);

  const parsedIngredients = useMemo(
    () =>
      ingredients
        .split(",")
        .map((i) => i.trim())
        .filter(Boolean),
    [ingredients]
  );

  const requestPayload = {
    ingredients: parsedIngredients,
    cuisine,
    prep_time: prepTime,
    servings,
    skill_level: skillLevel,
  };

  const handleRetrieve = async () => {
    try {
      setLoading(true);
      setError("");
      setMode("");
      setRecipes([]);
      setGeneratedRecipes([]);
      setMeta(null);
      setSelectedRecipeId("");
      setSelectedRecipeDetail(null);

      const response = await axios.post<RetrieveResponse>(
        "http://127.0.0.1:8001/retrieve",
        requestPayload
      );

      setMode("retrieval");
      setRecipes(response.data.recipes || []);
      setGeneratedRecipes([]);
      setMeta(response.data.meta || null);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || "Failed to retrieve recipes");
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateInstead = async () => {
    try {
      setGenerateLoading(true);
      setError("");
      setGeneratedRecipes([]);
      setSelectedRecipeId("");
      setSelectedRecipeDetail(null);

      const response = await axios.post<GenerateResponse>(
        "http://127.0.0.1:8001/generate",
        requestPayload
      );

      setMode("generation_deterministic");
      setGeneratedRecipes(response.data.recipes || []);
      setRecipes([]);
      setMeta({
        recipe_count: response.data.meta?.recipe_count || 0,
        source: response.data.meta?.source || "deterministic_template_generation",
        fallback_reason: "user_requested_generation",
        fallback_suggested: false,
        quality_notes: response.data.meta?.quality_notes || [],
        model_name: response.data.meta?.model_name,
        latency_ms: response.data.meta?.latency_ms,
      });

      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || "Failed to generate recipes");
    } finally {
      setGenerateLoading(false);
    }
  };

  const handleLoadDetail = async (recipeId: string) => {
    try {
      setDetailLoading(true);
      setError("");
      setSelectedRecipeId(recipeId);
      setSelectedRecipeDetail(null);

      const response = await axios.post<RecipeDetailItem>(
        "http://127.0.0.1:8001/generate-detail",
        {
          recipe_id: recipeId,
          servings,
          skill_level: skillLevel,
          user_ingredients: parsedIngredients,
        }
      );

      setSelectedRecipeDetail(response.data);
      window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || "Failed to load recipe detail");
    } finally {
      setDetailLoading(false);
    }
  };

  const showConfidenceBanner = Boolean(meta?.fallback_suggested && mode === "retrieval");

  return (
    <main className="max-w-6xl mx-auto p-8 space-y-6">
      <h1 className="text-3xl font-bold">Recipe Intelligence Copilot</h1>

      <div className="space-y-4 border rounded-xl p-6">
        <label className="block space-y-1">
          <span className="font-medium">Ingredients</span>
          <input
            aria-label="Ingredients"
            className="w-full border rounded-lg p-3"
            value={ingredients}
            onChange={(e) => setIngredients(e.target.value)}
            placeholder="Ingredients comma separated"
          />
        </label>

        <label className="block space-y-1">
          <span className="font-medium">Cuisine</span>
          <input
            aria-label="Cuisine"
            className="w-full border rounded-lg p-3"
            value={cuisine}
            onChange={(e) => setCuisine(e.target.value)}
            placeholder="Cuisine"
          />
        </label>

        <label className="block space-y-1">
          <span className="font-medium">Prep time</span>
          <input
            aria-label="Prep time"
            className="w-full border rounded-lg p-3"
            type="number"
            value={prepTime}
            onChange={(e) => setPrepTime(Number(e.target.value))}
            placeholder="Prep time"
          />
        </label>

        <label className="block space-y-1">
          <span className="font-medium">Servings</span>
          <input
            aria-label="Servings"
            className="w-full border rounded-lg p-3"
            type="number"
            value={servings}
            onChange={(e) => setServings(Number(e.target.value))}
            placeholder="Servings"
          />
        </label>

        <label className="block space-y-1">
          <span className="font-medium">Skill level</span>
          <input
            aria-label="Skill level"
            className="w-full border rounded-lg p-3"
            value={skillLevel}
            onChange={(e) => setSkillLevel(e.target.value)}
            placeholder="Skill level"
          />
        </label>

        <div className="flex gap-3 flex-wrap">
          <button
            onClick={handleRetrieve}
            className="px-5 py-3 rounded-lg border"
            disabled={loading}
          >
            {loading ? "Finding recipes..." : "Find Recipes"}
          </button>

          <button
            onClick={handleGenerateInstead}
            className="px-5 py-3 rounded-lg border"
            disabled={generateLoading}
          >
            {generateLoading ? "Generating..." : "Generate Instead"}
          </button>
        </div>
      </div>

      {error && <p className="text-red-600">{error}</p>}

      {showConfidenceBanner && (
        <div className="border rounded-xl p-4 bg-yellow-50 space-y-2">
          <p className="font-medium">These results are low-confidence for your request.</p>
          <p className="text-sm">
            The ingredients were matched, but the cuisine or overall fit may be weak. You can
            review these retrieval results or generate recipes instead.
          </p>
          <div className="flex gap-3 flex-wrap">
            <button
              onClick={handleGenerateInstead}
              className="px-4 py-2 rounded-lg border"
              disabled={generateLoading}
            >
              {generateLoading ? "Generating..." : "Generate Instead"}
            </button>
            <span className="text-sm self-center">
              Fallback reason: {meta?.fallback_reason || "retrieval_low_confidence"}
            </span>
          </div>
        </div>
      )}

      {meta && (
        <div className="border rounded-xl p-4 space-y-2">
          <p>
            <strong>Mode:</strong> {mode || "N/A"}
          </p>
          <p>
            <strong>Source:</strong> {meta.source}
          </p>
          <p>
            <strong>Recipe count:</strong> {meta.recipe_count}
          </p>
          {meta.fallback_reason && (
            <p>
              <strong>Fallback reason:</strong> {meta.fallback_reason}
            </p>
          )}
          <p>
            <strong>Fallback suggested:</strong> {meta.fallback_suggested ? "Yes" : "No"}
          </p>
          {meta.model_name && (
            <p>
              <strong>Model:</strong> {meta.model_name}
            </p>
          )}
          {typeof meta.latency_ms === "number" && (
            <p>
              <strong>Latency:</strong> {meta.latency_ms} ms
            </p>
          )}
          {meta.quality_notes && meta.quality_notes.length > 0 && (
            <div>
              <strong>Quality notes:</strong>
              <ul className="list-disc pl-6 mt-1">
                {meta.quality_notes.map((note, idx) => (
                  <li key={idx}>{note}</li>
                ))}
              </ul>
            </div>
          )}
          {meta.confidence_level && (
            <p>
              <strong>Confidence:</strong> {meta.confidence_level}
              {typeof meta.confidence_score === "number" ? ` (${meta.confidence_score})` : ""}
            </p>
          )}
          {meta.confidence_reasons && meta.confidence_reasons.length > 0 && (
            <div>
              <strong>Confidence reasons:</strong>
              <ul className="list-disc pl-6 mt-1">
                {meta.confidence_reasons.map((reason, idx) => (
                  <li key={idx}>{reason}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {mode === "retrieval" && recipes.length > 0 && (
        <div className="space-y-6">
          <h2 className="text-2xl font-semibold">Retrieved Recipe Suggestions</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {recipes.map((recipe, recipeIndex) => (
              <div
                key={recipe.id}
                className={`border rounded-xl p-6 space-y-3 ${
                  selectedRecipeId === recipe.id ? "border-black" : ""
                }`}
              >
                <h3 className="text-xl font-semibold">
                  {recipeIndex + 1}. {recipe.title}
                </h3>

                <p>{recipe.description || "No description available."}</p>

                <p>
                  <strong>Cuisine:</strong> {recipe.cuisine || "N/A"}
                </p>

                <p>
                  <strong>Prep time:</strong> {recipe.prep_time_mins ?? "N/A"} mins
                </p>

                <p>
                  <strong>Total time:</strong> {recipe.total_time_mins ?? "N/A"} mins
                </p>

                <p>
                  <strong>Servings:</strong> {recipe.servings ?? "N/A"}
                </p>

                <p>
                  <strong>Match score:</strong> {recipe.match_score}
                </p>

                <p>
                  <strong>Extra major count:</strong> {recipe.extra_major_count ?? 0}
                </p>

                <p>
                  <strong>Why chosen:</strong> {recipe.why_chosen}
                </p>

                <div>
                  <strong>Matched ingredients:</strong>
                  {recipe.matched_input_ingredients.length > 0 ? (
                    <ul className="list-disc pl-6 mt-2">
                      {recipe.matched_input_ingredients.map((item, idx) => (
                        <li key={idx}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="mt-2">No direct ingredient matches recorded.</p>
                  )}
                </div>

                {recipe.confidence_level && (
                  <p>
                    <strong>Confidence:</strong> {recipe.confidence_level}
                    {typeof recipe.confidence_score === "number"
                      ? ` (${recipe.confidence_score})`
                      : ""}
                  </p>
                )}

                {recipe.confidence_reasons && recipe.confidence_reasons.length > 0 && (
                  <div>
                    <strong>Confidence reasons:</strong>
                    <ul className="list-disc pl-6 mt-2">
                      {recipe.confidence_reasons.map((reason, idx) => (
                        <li key={idx}>{reason}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <button
                  onClick={() => handleLoadDetail(recipe.id)}
                  className="px-4 py-2 rounded-lg border"
                  disabled={detailLoading && selectedRecipeId === recipe.id}
                >
                  {detailLoading && selectedRecipeId === recipe.id
                    ? "Loading detail..."
                    : "View Full Recipe"}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {mode === "generation_deterministic" && generatedRecipes.length > 0 && (
        <div className="space-y-6">
          <h2 className="text-2xl font-semibold">Generated Recipe Suggestions</h2>
          <p className="text-sm">
            Retrieval looked weak, so you chose to generate recipes directly.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {generatedRecipes.map((recipe, recipeIndex) => {
              const isGenericFallback = recipe.template_name === "generic_fallback";

              return (
                <div
                  key={`${recipe.title}-${recipeIndex}`}
                  className="border rounded-xl p-6 space-y-3"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-xl font-semibold">
                      {recipeIndex + 1}. {recipe.title}
                    </h3>

                    <span
                      className={`px-2 py-1 rounded-full text-xs font-medium ${templateBadgeClass(
                        recipe.template_name
                      )}`}
                    >
                      {recipe.template_name || "unknown_template"}
                    </span>

                    <span
                      className={`px-2 py-1 rounded-full text-xs font-medium ${sourceBadgeClass(
                        recipe.grounding_source
                      )}`}
                    >
                      {recipe.grounding_source || "unknown_source"}
                    </span>
                  </div>

                  {isGenericFallback && (
                    <div className="border rounded-lg p-3 bg-amber-50 text-amber-900 space-y-1">
                      <p className="font-medium">Low-confidence fallback</p>
                      <p className="text-sm">
                        No known recipe template matched this ingredient combination, so this is a
                        basic placeholder recipe.
                      </p>
                    </div>
                  )}

                  <p>
                    <strong>Why chosen:</strong> {recipe.why_chosen}
                  </p>

                  <p>
                    <strong>Match score:</strong> {recipe.match_score}
                  </p>

                  <div>
                    <strong>Ingredients:</strong>
                    <ul className="list-disc pl-6 mt-2">
                      {recipe.ingredients.map((item, idx) => (
                        <li key={idx}>
                          {item.quantity ? `${item.quantity} ` : ""}
                          {item.name}
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <strong>Steps:</strong>
                    <ol className="list-decimal pl-6 mt-2">
                      {recipe.steps.map((step, idx) => (
                        <li key={idx}>{step}</li>
                      ))}
                    </ol>
                  </div>

                  {recipe.substitutions.length > 0 && (
                    <div>
                      <strong>Substitutions:</strong>
                      <ul className="list-disc pl-6 mt-2">
                        {recipe.substitutions.map((sub, idx) => (
                          <li key={idx}>{sub}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {recipe.warnings.length > 0 && (
                    <div>
                      <strong>Warnings:</strong>
                      <ul className="list-disc pl-6 mt-2">
                        {recipe.warnings.map((warning, idx) => (
                          <li key={idx}>{warning}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <p>
                    <strong>Template:</strong> {recipe.template_name || "N/A"}
                  </p>
                  <p>
                    <strong>Grounding source:</strong> {recipe.grounding_source || "N/A"}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {selectedRecipeDetail && (
        <div className="border rounded-xl p-6 space-y-4">
          <h2 className="text-2xl font-semibold">{selectedRecipeDetail.title}</h2>

          <p>
            <strong>Why chosen:</strong> {selectedRecipeDetail.why_chosen}
          </p>

          <p>
            <strong>Source recipe title:</strong> {selectedRecipeDetail.source_recipe_title}
          </p>

          <p>
            <strong>Grounded:</strong> {selectedRecipeDetail.grounded ? "Yes" : "No"}
          </p>

          <div>
            <h3 className="font-semibold">Ingredients</h3>
            <ul className="list-disc pl-6">
              {selectedRecipeDetail.ingredients.map((item, idx) => (
                <li key={idx}>
                  {item.quantity ? `${item.quantity} ` : ""}
                  {item.name}
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="font-semibold">Steps</h3>
            <ol className="list-decimal pl-6">
              {selectedRecipeDetail.steps.map((step, idx) => (
                <li key={idx}>{step}</li>
              ))}
            </ol>
          </div>

          <div>
            <h3 className="font-semibold">Substitutions</h3>
            {selectedRecipeDetail.substitutions.length > 0 ? (
              <ul className="list-disc pl-6">
                {selectedRecipeDetail.substitutions.map((sub, idx) => (
                  <li key={idx}>{sub}</li>
                ))}
              </ul>
            ) : (
              <p>No substitutions suggested.</p>
            )}
          </div>

          <div>
            <h3 className="font-semibold">Nutrition</h3>
            <p>Calories: {selectedRecipeDetail.nutrition_summary?.calories ?? "N/A"}</p>
            <p>Protein: {selectedRecipeDetail.nutrition_summary?.protein_g ?? "N/A"} g</p>
            <p>Carbs: {selectedRecipeDetail.nutrition_summary?.carbs_g ?? "N/A"} g</p>
            <p>Fats: {selectedRecipeDetail.nutrition_summary?.fats_g ?? "N/A"} g</p>
          </div>

          {selectedRecipeDetail.warnings?.length > 0 && (
            <div>
              <h3 className="font-semibold">Warnings</h3>
              <ul className="list-disc pl-6">
                {selectedRecipeDetail.warnings.map((warning, idx) => (
                  <li key={idx}>{warning}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </main>
  );
}