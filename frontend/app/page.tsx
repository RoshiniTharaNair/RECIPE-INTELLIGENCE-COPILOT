"use client";

import { useMemo, useState } from "react";
import axios from "axios";

const API_BASE_URL =
  (process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8001").replace(/\/$/, "");

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
  constraint_notes?: string[];
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
  constraint_notes?: string[];
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

const dietaryPresetOptions = [
  { value: "vegetarian", label: "Vegetarian" },
  { value: "egg-free", label: "Egg-free" },
  { value: "dairy-free", label: "Dairy-free" },
] as const;

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
  const [detailError, setDetailError] = useState("");

  const [mode, setMode] = useState<"retrieval" | "generation_deterministic" | "">("");
  const [recipes, setRecipes] = useState<RecipeSummaryItem[]>([]);
  const [generatedRecipes, setGeneratedRecipes] = useState<GeneratedRecipeItem[]>([]);
  const [meta, setMeta] = useState<RetrieveResponse["meta"] | null>(null);

  const [selectedRecipeId, setSelectedRecipeId] = useState<string>("");
  const [selectedRecipeDetail, setSelectedRecipeDetail] = useState<RecipeDetailItem | null>(null);

  const [avoidIngredients, setAvoidIngredients] = useState("");

  const [dietaryPreferences, setDietaryPreferences] = useState<string[]>([]);

  const [detailActionMessage, setDetailActionMessage] = useState("");

  const [showRecipeCardPreview, setShowRecipeCardPreview] = useState(false);

  const parsedAvoidIngredients = useMemo(
  () => avoidIngredients.split(",").map((i) => i.trim()).filter(Boolean),
  [avoidIngredients]
);

  const parsedIngredients = useMemo(
    () =>
      ingredients
        .split(",")
        .map((i) => i.trim())
        .filter(Boolean),
    [ingredients]
  );

const toggleDietaryPreference = (value: string) => {
  setDietaryPreferences((prev) =>
    prev.includes(value)
      ? prev.filter((item) => item !== value)
      : [...prev, value]
  );
};

const requestPayload = {
  ingredients: parsedIngredients,
  avoid_ingredients: parsedAvoidIngredients,
  dietary_preferences: dietaryPreferences,
  cuisine,
  prep_time: prepTime,
  servings,
  skill_level: skillLevel,
};
  const handleRetrieve = async () => {
    try {
      setLoading(true);
      setError("");
      setDetailError("");
      setMode("");
      setRecipes([]);
      setGeneratedRecipes([]);
      setMeta(null);
      setSelectedRecipeId("");
      setSelectedRecipeDetail(null);

const response = await axios.post<RetrieveResponse>(
  `${API_BASE_URL}/retrieve`,
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
      setDetailError("");
      setGeneratedRecipes([]);
      setSelectedRecipeId("");
      setSelectedRecipeDetail(null);

const response = await axios.post<GenerateResponse>(
  `${API_BASE_URL}/generate`,
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
      setDetailError("");
      setError("");
      setSelectedRecipeId(recipeId);
      setSelectedRecipeDetail(null);

const response = await axios.post<RecipeDetailItem>(
  `${API_BASE_URL}/generate-detail`,
  {
    recipe_id: recipeId,
    servings,
    skill_level: skillLevel,
    user_ingredients: parsedIngredients,
    avoid_ingredients: parsedAvoidIngredients,
    dietary_preferences: dietaryPreferences,
  }
);

      setSelectedRecipeDetail(response.data);
      window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
    } catch (err: any) {
      setDetailError(
        err?.response?.data?.detail || err?.message || "Failed to load recipe detail"
      );
    } finally {
      setDetailLoading(false);
    }
  };

const showConfidenceBanner = Boolean(meta?.fallback_suggested && mode === "retrieval");

const showDetailPanel =
  mode === "retrieval" &&
  (recipes.length > 0 || detailLoading || detailError || selectedRecipeDetail);

const showInitialGuidance =
  mode === "" &&
  !loading &&
  !generateLoading &&
  !error &&
  !meta &&
  recipes.length === 0 &&
  generatedRecipes.length === 0;

const showRetrievalEmptyState =
  mode === "retrieval" &&
  !loading &&
  !error &&
  recipes.length === 0;

const showGenerationEmptyState =
  mode === "generation_deterministic" &&
  !generateLoading &&
  !error &&
  generatedRecipes.length === 0;


const activeConstraintBadges = [
  ...parsedAvoidIngredients.map((item) => ({
    key: `avoid-${item}`,
    label: `Avoid: ${item}`,
  })),
  ...dietaryPreferences.map((item) => ({
    key: `preset-${item}`,
    label: `Preset: ${item}`,
  })),
];

const showConstraintBadges =
  activeConstraintBadges.length > 0 &&
  (mode === "retrieval" || mode === "generation_deterministic");

  const showDetailConstraintBadges =
  activeConstraintBadges.length > 0 &&
  mode === "retrieval" &&
  (detailLoading || detailError || selectedRecipeDetail);

const detailConstraintSummary =
  activeConstraintBadges.length === 0
    ? ""
    : "This grounded detail reflects your active avoid list and dietary preset filters.";


const buildDetailExportText = (detail: RecipeDetailItem) => {
  const lines: string[] = [
    detail.title,
    "",
    `Why chosen: ${detail.why_chosen}`,
    `Source recipe title: ${detail.source_recipe_title || detail.title}`,
    `Grounded: ${detail.grounded ? "Yes" : "No"}`,
  ];

  if (detail.constraint_notes && detail.constraint_notes.length > 0) {
    lines.push("", "Constraint notes:");
    detail.constraint_notes.forEach((note) => {
      lines.push(`- ${note}`);
    });
  }

  if (detail.warnings && detail.warnings.length > 0) {
    lines.push("", "Warnings:");
    detail.warnings.forEach((warning) => {
      lines.push(`- ${warning}`);
    });
  }

  if (detail.ingredients && detail.ingredients.length > 0) {
    lines.push("", "Ingredients:");
    detail.ingredients.forEach((item) => {
      const quantity = item.quantity?.trim();
      lines.push(`- ${item.name}${quantity ? `: ${quantity}` : ""}`);
    });
  }

  if (detail.steps && detail.steps.length > 0) {
    lines.push("", "Steps:");
    detail.steps.forEach((step, idx) => {
      lines.push(`${idx + 1}. ${step}`);
    });
  }

  if (detail.substitutions && detail.substitutions.length > 0) {
    lines.push("", "Substitutions:");
    detail.substitutions.forEach((substitution) => {
      lines.push(`- ${substitution}`);
    });
  }

  return lines.join("\n");
};

const handleCopyDetail = async () => {
  if (!selectedRecipeDetail) return;

  try {
    await navigator.clipboard.writeText(buildRecipeCardText(selectedRecipeDetail));
    setDetailActionMessage("Recipe card copied to clipboard.");
  } catch {
    setDetailActionMessage("Could not copy recipe card.");
  }
};

const handleDownloadDetail = () => {
  if (!selectedRecipeDetail) return;

  const text = buildRecipeCardText(selectedRecipeDetail);
  const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);

  const safeTitle =
    (selectedRecipeDetail.title || "recipe-card")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "") || "recipe-card";

  const link = document.createElement("a");
  link.href = url;
  link.download = `${safeTitle}-card.txt`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);

  setDetailActionMessage("Recipe card downloaded.");
};

const handlePrintDetail = () => {
  if (!selectedRecipeDetail) return;

  const printWindow = window.open("", "_blank", "width=900,height=700");

  if (!printWindow) {
    setDetailActionMessage("Could not open print view.");
    return;
  }

  printWindow.document.open();
  printWindow.document.write(buildRecipeCardPrintHtml(selectedRecipeDetail));
  printWindow.document.close();
  printWindow.focus();
  printWindow.print();

  setDetailActionMessage("Recipe card print view opened.");
};
    const escapeHtml = (value: string) =>
  value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");

const buildDetailPrintHtml = (detail: RecipeDetailItem) => {
  const constraintNotes = (detail.constraint_notes || [])
    .map((note) => `<li>${escapeHtml(note)}</li>`)
    .join("");

  const warnings = (detail.warnings || [])
    .map((warning) => `<li>${escapeHtml(warning)}</li>`)
    .join("");

  const ingredients = (detail.ingredients || [])
    .map(
      (item) =>
        `<li>${escapeHtml(item.name)}${
          item.quantity ? ` — ${escapeHtml(item.quantity)}` : ""
        }</li>`
    )
    .join("");

  const steps = (detail.steps || [])
    .map((step, idx) => `<li>${idx + 1}. ${escapeHtml(step)}</li>`)
    .join("");

  const substitutions = (detail.substitutions || [])
    .map((sub) => `<li>${escapeHtml(sub)}</li>`)
    .join("");

  return `<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>${escapeHtml(detail.title)}</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 32px; line-height: 1.5; color: #111827; }
      h1, h2 { margin-bottom: 8px; }
      .meta { margin-bottom: 20px; color: #374151; }
      .section { margin-top: 20px; }
      ul, ol { padding-left: 20px; }
    </style>
  </head>
  <body>
    <h1>${escapeHtml(detail.title)}</h1>
    <div class="meta">
      <div><strong>Why chosen:</strong> ${escapeHtml(detail.why_chosen)}</div>
      <div><strong>Source recipe title:</strong> ${escapeHtml(detail.source_recipe_title || detail.title)}</div>
      <div><strong>Grounded:</strong> ${detail.grounded ? "Yes" : "No"}</div>
    </div>

    ${
      constraintNotes
        ? `<div class="section"><h2>Constraint notes</h2><ul>${constraintNotes}</ul></div>`
        : ""
    }

    ${
      warnings
        ? `<div class="section"><h2>Warnings</h2><ul>${warnings}</ul></div>`
        : ""
    }

    <div class="section"><h2>Ingredients</h2><ul>${ingredients}</ul></div>
    <div class="section"><h2>Steps</h2><ol>${steps}</ol></div>

    ${
      substitutions
        ? `<div class="section"><h2>Substitutions</h2><ul>${substitutions}</ul></div>`
        : ""
    }
  </body>
</html>`;
};


const buildRecipeCardSections = (detail: RecipeDetailItem) => ({
  title: detail.title,
  subtitle: detail.source_recipe_title || detail.title,
  whyChosen: detail.why_chosen,
  grounded: detail.grounded ? "Yes" : "No",
  constraintNotes: detail.constraint_notes || [],
  warnings: detail.warnings || [],
  ingredients: detail.ingredients || [],
  steps: detail.steps || [],
});


const buildRecipeCardText = (detail: RecipeDetailItem) => {
  const card = buildRecipeCardSections(detail);

  const lines: string[] = [
    card.title,
    card.subtitle ? `Source: ${card.subtitle}` : "",
    `Why chosen: ${card.whyChosen}`,
    `Grounded: ${card.grounded}`,
  ].filter(Boolean);

  if (card.constraintNotes.length > 0) {
    lines.push("", "Constraint notes:");
    card.constraintNotes.forEach((note) => lines.push(`- ${note}`));
  }

  if (card.warnings.length > 0) {
    lines.push("", "Warnings:");
    card.warnings.forEach((warning) => lines.push(`- ${warning}`));
  }

  if (card.ingredients.length > 0) {
    lines.push("", "Ingredients:");
    card.ingredients.forEach((item) => {
      lines.push(`- ${item.quantity ? `${item.quantity} ` : ""}${item.name}`);
    });
  }

  if (card.steps.length > 0) {
    lines.push("", "Steps:");
    card.steps.forEach((step, idx) => lines.push(`${idx + 1}. ${step}`));
  }

  return lines.join("\n");
};

const buildRecipeCardPrintHtml = (detail: RecipeDetailItem) => {
  const card = buildRecipeCardSections(detail);

  const constraintNotes = card.constraintNotes
    .map((note) => `<li>${escapeHtml(note)}</li>`)
    .join("");

  const warnings = card.warnings
    .map((warning) => `<li>${escapeHtml(warning)}</li>`)
    .join("");

  const ingredients = card.ingredients
    .map(
      (item) =>
        `<li>${item.quantity ? `${escapeHtml(item.quantity)} ` : ""}${escapeHtml(item.name)}</li>`
    )
    .join("");

  const steps = card.steps
    .map((step, idx) => `<li>${idx + 1}. ${escapeHtml(step)}</li>`)
    .join("");

  return `<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>${escapeHtml(card.title)}</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 32px; line-height: 1.5; color: #111827; }
      h1, h2 { margin-bottom: 8px; }
      .meta { margin-bottom: 20px; color: #374151; }
      .section { margin-top: 20px; }
      .card { border: 1px solid #cbd5e1; border-radius: 16px; padding: 24px; background: #f8fafc; }
      ul, ol { padding-left: 20px; }
    </style>
  </head>
  <body>
    <div class="card">
      <h1>${escapeHtml(card.title)}</h1>
      <div class="meta">
        <div><strong>Source:</strong> ${escapeHtml(card.subtitle)}</div>
        <div><strong>Why chosen:</strong> ${escapeHtml(card.whyChosen)}</div>
        <div><strong>Grounded:</strong> ${escapeHtml(card.grounded)}</div>
      </div>

      ${
        constraintNotes
          ? `<div class="section"><h2>Constraint notes</h2><ul>${constraintNotes}</ul></div>`
          : ""
      }

      ${
        warnings
          ? `<div class="section"><h2>Warnings</h2><ul>${warnings}</ul></div>`
          : ""
      }

      <div class="section"><h2>Ingredients</h2><ul>${ingredients}</ul></div>
      <div class="section"><h2>Steps</h2><ol>${steps}</ol></div>
    </div>
  </body>
</html>`;
};

const handleShareDetail = async () => {
  if (!selectedRecipeDetail) return;

  const shareText = buildRecipeCardText(selectedRecipeDetail);

  try {
    if (navigator.share) {
      await navigator.share({
        title: selectedRecipeDetail.title,
        text: shareText,
      });
      setDetailActionMessage("Recipe card shared.");
      return;
    }

    await navigator.clipboard.writeText(shareText);
    setDetailActionMessage("Share not available, so the recipe card was copied instead.");
  } catch {
    setDetailActionMessage("Could not share recipe card.");
  }
};
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
  <span className="font-medium">Avoid ingredients</span>
  <input
    aria-label="Avoid ingredients"
    className="w-full border rounded-lg p-3"
    value={avoidIngredients}
    onChange={(e) => setAvoidIngredients(e.target.value)}
    placeholder="Optional: egg, peanut, garlic"
  />
</label>

<fieldset className="space-y-2">
  <legend className="font-medium">Dietary presets</legend>
  <div className="flex flex-wrap gap-4">
    {dietaryPresetOptions.map((option) => (
      <label key={option.value} className="inline-flex items-center gap-2">
        <input
          type="checkbox"
          aria-label={option.label}
          checked={dietaryPreferences.includes(option.value)}
          onChange={() => toggleDietaryPreference(option.value)}
        />
        <span>{option.label}</span>
      </label>
    ))}
  </div>
  <p className="text-sm text-slate-600">
    These presets automatically exclude ingredient groups during retrieval and generation.
  </p>
</fieldset>

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
{showInitialGuidance && (
  <div className="border rounded-xl p-6 bg-slate-50 space-y-3">
    <h2 className="text-xl font-semibold">Start with ingredients</h2>
    <p className="text-slate-700">
      Enter a few ingredients, choose a cuisine if you want, and click{" "}
      <strong>Find Recipes</strong> to see grounded retrieval results first.
    </p>
    <p className="text-sm text-slate-600">
      If retrieval looks weak, you can use <strong>Generate Instead</strong> for a
      deterministic fallback recipe.
    </p>
  </div>
)}
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

      {showConstraintBadges && (
  <div className="border rounded-xl p-4 space-y-3 bg-slate-50">
    <h2 className="text-lg font-semibold">Active constraints</h2>
    <div className="flex flex-wrap gap-2">
      {activeConstraintBadges.map((badge) => (
        <span
          key={badge.key}
          className="inline-flex items-center rounded-full border px-3 py-1 text-sm bg-white"
        >
          {badge.label}
        </span>
      ))}
    </div>
  </div>
)}

      {showRetrievalEmptyState && (
  <div className="border rounded-xl p-6 space-y-3 bg-amber-50">
    <h2 className="text-2xl font-semibold">No retrieval matches found</h2>
    <p className="text-slate-700">
      We could not find strong recipe summaries for your current request.
    </p>
    <p className="text-sm text-slate-600">
      Try adjusting ingredients or cuisine, or use <strong>Generate Instead</strong> to
      build a fallback recipe from your inputs.
    </p>

    {parsedIngredients.length > 0 && (
      <p className="text-sm">
        <strong>Current ingredients:</strong> {parsedIngredients.join(", ")}
      </p>
    )}

    <div className="flex gap-3 flex-wrap">
      <button
        onClick={handleGenerateInstead}
        className="px-4 py-2 rounded-lg border"
        disabled={generateLoading}
      >
        {generateLoading ? "Generating..." : "Generate Instead"}
      </button>
    </div>
  </div>
)}


      {mode === "retrieval" && recipes.length > 0 && (
        <div className="space-y-6">
          <h2 className="text-2xl font-semibold">Retrieved Recipe Suggestions</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {recipes.map((recipe, recipeIndex) => {
              const isSelected = selectedRecipeId === recipe.id;

              return (
                <div
                  key={recipe.id}
                  className={`border rounded-xl p-6 space-y-3 transition ${
  isSelected
    ? "border-black shadow-md bg-slate-50 ring-2 ring-slate-300"
    : "hover:shadow-sm"
}`}
                >
                  {isSelected && (
  <span className="inline-block px-2 py-1 rounded-full text-xs font-medium bg-black text-white">
    Selected
  </span>
)}
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
                    disabled={detailLoading && isSelected}
                  >
                    {detailLoading && isSelected ? "Loading detail..." : "View Full Recipe"}
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}



      {showDetailPanel && (
        <div className="border rounded-xl p-6 space-y-4">
        <div className="flex items-center justify-between gap-3 flex-wrap">
  <h2 className="text-2xl font-semibold">Recipe Detail</h2>

  <div className="flex items-center gap-3 flex-wrap">
    {selectedRecipeId && (
      <span className="text-sm text-slate-600">
        Selected recipe ID: {selectedRecipeId}
      </span>
    )}


{selectedRecipeDetail && (
  <>
    <button
      onClick={() => setShowRecipeCardPreview(true)}
      className="px-3 py-2 rounded-lg border"
    >
      Preview Recipe Card
    </button>

    <button
      onClick={handleShareDetail}
      className="px-3 py-2 rounded-lg border"
    >
      Share Recipe Card
    </button>

    <button
      onClick={handleCopyDetail}
      className="px-3 py-2 rounded-lg border"
    >
      Copy Recipe Card
    </button>

    <button
      onClick={handlePrintDetail}
      className="px-3 py-2 rounded-lg border"
    >
      Print Recipe Card
    </button>

    <button
      onClick={handleDownloadDetail}
      className="px-3 py-2 rounded-lg border"
    >
      Download Recipe Card
    </button>
  </>
)}

    {(selectedRecipeId || selectedRecipeDetail || detailError) && (
      <button
       onClick={() => {
  setSelectedRecipeId("");
  setSelectedRecipeDetail(null);
  setDetailError("");
  setDetailActionMessage("");
  setShowRecipeCardPreview(false);
}}
        className="px-3 py-2 rounded-lg border"
      >
        Clear Detail
      </button>
    )}
  </div>
</div>

{showDetailConstraintBadges && (
  <div className="border rounded-lg p-4 bg-slate-50 space-y-3">
    <h3 className="text-base font-semibold">Constraints used for this detail</h3>
    <p className="text-sm text-slate-600">{detailConstraintSummary}</p>
    <div className="flex flex-wrap gap-2">
      {activeConstraintBadges.map((badge) => (
        <span
          key={`detail-${badge.key}`}
          className="inline-flex items-center rounded-full border px-3 py-1 text-sm bg-white"
        >
          {badge.label}
        </span>
      ))}
    </div>
  </div>
)}

{detailActionMessage && (
  <div className="border rounded-lg p-3 bg-slate-50 text-sm">
    {detailActionMessage}
  </div>
)}
          {!selectedRecipeId && !selectedRecipeDetail && !detailLoading && !detailError && (
            <p className="text-slate-600">
              Choose a retrieved recipe and click <strong>View Full Recipe</strong> to load grounded
              recipe detail.
            </p>
          )}

          {detailLoading && (
            <div className="border rounded-lg p-4 bg-slate-50 space-y-2">
              <p className="font-medium">Loading grounded recipe detail...</p>
              <p className="text-sm text-slate-600">
                The selected recipe is being expanded using the stored recipe context.
              </p>
            </div>
          )}

          {detailError && (
            <div className="border rounded-lg p-4 bg-red-50 text-red-700">
              {detailError}
            </div>
          )}

          {selectedRecipeDetail && !detailLoading && (
            <div className="space-y-4">
              <h3 className="text-2xl font-semibold">{selectedRecipeDetail.title}</h3>

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
                <h4 className="font-semibold">Ingredients</h4>
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
                <h4 className="font-semibold">Steps</h4>
                <ol className="list-decimal pl-6">
                  {selectedRecipeDetail.steps.map((step, idx) => (
                    <li key={idx}>{step}</li>
                  ))}
                </ol>
              </div>

              <div>
                <h4 className="font-semibold">Substitutions</h4>
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
                <h4 className="font-semibold">Nutrition</h4>
                <p>Calories: {selectedRecipeDetail.nutrition_summary?.calories ?? "N/A"}</p>
                <p>Protein: {selectedRecipeDetail.nutrition_summary?.protein_g ?? "N/A"} g</p>
                <p>Carbs: {selectedRecipeDetail.nutrition_summary?.carbs_g ?? "N/A"} g</p>
                <p>Fats: {selectedRecipeDetail.nutrition_summary?.fats_g ?? "N/A"} g</p>
              </div>

              {selectedRecipeDetail.warnings?.length > 0 && (
                <div>
                  <h4 className="font-semibold">Warnings</h4>
                  <ul className="list-disc pl-6">
                    {selectedRecipeDetail.warnings.map((warning, idx) => (
                      <li key={idx}>{warning}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {selectedRecipeDetail?.constraint_notes &&
  selectedRecipeDetail.constraint_notes.length > 0 && (
    <div>
      <strong>Constraint notes:</strong>
      <ul className="list-disc pl-6 mt-2">
        {selectedRecipeDetail.constraint_notes.map((note, idx) => (
          <li key={idx}>{note}</li>
        ))}
      </ul>
    </div>
  )}
        </div>
      )}

      {showGenerationEmptyState && (
  <div className="border rounded-xl p-6 space-y-3 bg-slate-50">
    <h2 className="text-2xl font-semibold">No generated recipes returned</h2>
    <p className="text-slate-700">
      The generation request completed, but no recipe suggestions were returned.
    </p>
    <p className="text-sm text-slate-600">
      Try changing the ingredients slightly and run generation again.
    </p>

    {meta?.quality_notes && meta.quality_notes.length > 0 && (
      <div>
        <strong>Quality notes:</strong>
        <ul className="list-disc pl-6 mt-1">
          {meta.quality_notes.map((note, idx) => (
            <li key={idx}>{note}</li>
          ))}
        </ul>
      </div>
    )}
  </div>
)}

{showRecipeCardPreview && selectedRecipeDetail && (
  <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-6 z-50">
    <div className="bg-white w-full max-w-2xl rounded-2xl shadow-lg border p-6 space-y-4 max-h-[90vh] overflow-y-auto">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-2xl font-semibold">Recipe Card Preview</h3>
        <button
          onClick={() => setShowRecipeCardPreview(false)}
          className="px-3 py-2 rounded-lg border"
        >
          Close Preview
        </button>
      </div>

      {(() => {
        const card = buildRecipeCardSections(selectedRecipeDetail);
        return (
          <div className="border rounded-xl p-6 space-y-4 bg-slate-50">
            <div>
              <h4 className="text-2xl font-bold">{card.title}</h4>
              <p className="text-slate-600">{card.subtitle}</p>
            </div>

            <p><strong>Why chosen:</strong> {card.whyChosen}</p>
            <p><strong>Grounded:</strong> {card.grounded}</p>

            {card.constraintNotes.length > 0 && (
              <div>
                <h5 className="font-semibold">Constraint notes</h5>
                <ul className="list-disc pl-6">
                  {card.constraintNotes.map((note, idx) => (
                    <li key={idx}>{note}</li>
                  ))}
                </ul>
              </div>
            )}

            {card.warnings.length > 0 && (
              <div>
                <h5 className="font-semibold">Warnings</h5>
                <ul className="list-disc pl-6">
                  {card.warnings.map((warning, idx) => (
                    <li key={idx}>{warning}</li>
                  ))}
                </ul>
              </div>
            )}

            <div>
              <h5 className="font-semibold">Ingredients</h5>
              <ul className="list-disc pl-6">
                {card.ingredients.map((item, idx) => (
                  <li key={idx}>
                    {item.quantity ? `${item.quantity} ` : ""}
                    {item.name}
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h5 className="font-semibold">Steps</h5>
              <ol className="list-decimal pl-6">
                {card.steps.map((step, idx) => (
                  <li key={idx}>{step}</li>
                ))}
              </ol>
            </div>
          </div>
        );
      })()}
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

                  {recipe.constraint_notes && recipe.constraint_notes.length > 0 && (
  <div>
    <strong>Constraint notes:</strong>
    <ul className="list-disc pl-6 mt-2">
      {recipe.constraint_notes.map((note, idx) => (
        <li key={idx}>{note}</li>
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
    </main>
  );
}