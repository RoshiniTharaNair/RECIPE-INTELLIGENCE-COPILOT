import React from "react";
import { render, screen, fireEvent, waitFor, within } from "@testing-library/react";
import axios from "axios";
import Page from "../app/page";

jest.mock("axios");
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe("Recipe page", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("shows generated deterministic recipe metadata", async () => {
    mockedAxios.post.mockResolvedValueOnce({
      data: {
        recipes: [
          {
            title: "Saag Paneer",
            why_chosen: "Built from spinach and paneer with an Indian-style template.",
            ingredients: [
              { name: "spinach", quantity: "3 cups" },
              { name: "paneer", quantity: "200 g" }
            ],
            steps: [
              "Wash and chop the spinach.",
              "Heat oil and sauté garlic with cumin."
            ],
            substitutions: [],
            nutrition_summary: {
              calories: null,
              protein_g: null,
              carbs_g: null,
              fats_g: null
            },
            warnings: [],
            match_score: 1.0,
            matched_input_ingredients: ["spinach", "paneer"],
            extra_major_ingredients: [],
            template_name: "saag_paneer",
            grounding_source: "retrieval_grounded"
          }
        ],
        meta: {
          latency_ms: 188,
          model_name: "deterministic_generator",
          recipe_count: 1,
          input_ingredients: ["spinach", "paneer"],
          quality_notes: [
            "Recipe was assembled deterministically using retrieved grounding."
          ]
        }
      }
    });

    render(<Page />);

    fireEvent.change(screen.getByLabelText(/ingredients/i), {
      target: { value: "spinach, paneer" }
    });

    fireEvent.click(screen.getByRole("button", { name: /generate instead/i }));

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /saag paneer/i })).toBeInTheDocument();
    });

    expect(screen.getAllByText(/saag_paneer/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/retrieval_grounded/i).length).toBeGreaterThanOrEqual(1);
    expect(
      screen.getByText(/Recipe was assembled deterministically using retrieved grounding/i)
    ).toBeInTheDocument();
  });

  test("shows template_only metadata for cheese toast", async () => {
    mockedAxios.post.mockResolvedValueOnce({
      data: {
        recipes: [
          {
            title: "Cheese Toast",
            why_chosen: "Built from bread and cheese using a quick beginner-friendly template.",
            ingredients: [
              { name: "bread", quantity: "2 slices" },
              { name: "cheese", quantity: "1/2 cup" }
            ],
            steps: [
              "Place the bread on a pan or tray.",
              "Top evenly with cheese."
            ],
            substitutions: [],
            nutrition_summary: {
              calories: null,
              protein_g: null,
              carbs_g: null,
              fats_g: null
            },
            warnings: [],
            match_score: 1.0,
            matched_input_ingredients: ["bread", "cheese"],
            extra_major_ingredients: [],
            template_name: "cheese_toast",
            grounding_source: "template_only"
          }
        ],
        meta: {
          latency_ms: 132,
          model_name: "deterministic_generator",
          recipe_count: 1,
          input_ingredients: ["bread", "cheese"],
          quality_notes: [
            "No strong retrieved candidates were available, so recipe was assembled from user ingredients."
          ]
        }
      }
    });

    render(<Page />);

    fireEvent.change(screen.getByLabelText(/ingredients/i), {
      target: { value: "bread, cheese" }
    });

    fireEvent.click(screen.getByRole("button", { name: /generate instead/i }));

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /cheese toast/i })).toBeInTheDocument();
    });

    expect(screen.getAllByText(/cheese_toast/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/template_only/i).length).toBeGreaterThanOrEqual(1);
  });

  test("shows generic fallback warning UX", async () => {
    mockedAxios.post.mockResolvedValueOnce({
      data: {
        recipes: [
          {
            title: "Custom Abc Xyz Recipe",
            why_chosen: "Built directly from your ingredients: abc, xyz.",
            ingredients: [
              { name: "abc", quantity: "1 unit" },
              { name: "xyz", quantity: "1 unit" }
            ],
            steps: [
              "Prepare the ingredients: abc, xyz.",
              "Heat a pan with a little oil."
            ],
            substitutions: [],
            nutrition_summary: {
              calories: null,
              protein_g: null,
              carbs_g: null,
              fats_g: null
            },
            warnings: [
              "Low-confidence generated fallback: no known recipe template matched these ingredients.",
              "No retrieval grounding was available, so this recipe is only a basic placeholder."
            ],
            match_score: 0.25,
            matched_input_ingredients: ["abc", "xyz"],
            extra_major_ingredients: [],
            template_name: "generic_fallback",
            grounding_source: "template_only"
          }
        ],
        meta: {
          latency_ms: 140,
          model_name: "deterministic_generator",
          recipe_count: 1,
          input_ingredients: ["abc", "xyz"],
          quality_notes: [
            "No known template matched the input ingredients.",
            "Generated output is a low-confidence fallback.",
            "No strong retrieved candidates were available for grounding."
          ]
        }
      }
    });

    render(<Page />);

    fireEvent.change(screen.getByLabelText(/ingredients/i), {
      target: { value: "abc, xyz" }
    });

    fireEvent.click(screen.getByRole("button", { name: /generate instead/i }));

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /custom abc xyz recipe/i })).toBeInTheDocument();
    });

    expect(screen.getAllByText(/generic_fallback/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/Low-confidence fallback/i).length).toBeGreaterThanOrEqual(1);
    expect(
      screen.getByText(/No known template matched the input ingredients/i)
    ).toBeInTheDocument();
  });

  test("shows retrieval confidence info", async () => {
    mockedAxios.post.mockResolvedValueOnce({
      data: {
        mode: "retrieval",
        recipes: [
          {
            id: "r1",
            title: "Saag Paneer",
            description: "Spinach and paneer curry.",
            cuisine: "Indian",
            prep_time_mins: 30,
            total_time_mins: 30,
            servings: 2,
            match_score: 0.92,
            why_chosen: "Strong ingredient and cuisine match.",
            matched_input_ingredients: ["spinach", "cheese"],
            extra_major_count: 1,
            confidence_score: 0.88,
            confidence_level: "high",
            confidence_reasons: ["All requested ingredients matched strongly."]
          }
        ],
        generated_recipes: [],
        meta: {
          recipe_count: 1,
          source: "local_dataset_retrieval_summary_only",
          fallback_reason: null,
          fallback_suggested: false,
          confidence_score: 0.88,
          confidence_level: "high",
          confidence_reasons: ["All requested ingredients matched strongly."]
        }
      }
    });

    render(<Page />);

    fireEvent.change(screen.getByLabelText(/ingredients/i), {
      target: { value: "spinach, cheese" }
    });

    fireEvent.click(screen.getByRole("button", { name: /find recipes/i }));

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /saag paneer/i })).toBeInTheDocument();
    });

    const confidenceLabels = screen.getAllByText(/confidence:/i);
    expect(confidenceLabels.length).toBeGreaterThanOrEqual(2);

    const heading = screen.getByRole("heading", { name: /saag paneer/i });
    const recipeCard = heading.closest("div");
    expect(recipeCard).not.toBeNull();

    const cardScope = within(recipeCard as HTMLElement);
    expect(cardScope.getByText(/confidence:/i)).toBeInTheDocument();
    expect(cardScope.getByText(/high/i)).toBeInTheDocument();
    expect(
      screen.getAllByText(/All requested ingredients matched strongly/i).length
    ).toBeGreaterThanOrEqual(1);
  });
});