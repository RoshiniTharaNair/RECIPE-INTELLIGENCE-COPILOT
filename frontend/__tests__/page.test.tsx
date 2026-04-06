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

test("shows initial guidance before any action", () => {
  render(<Page />);

  const heading = screen.getByRole("heading", { name: /start with ingredients/i });
  expect(heading).toBeInTheDocument();

  const card = heading.closest("div");
  expect(card).not.toBeNull();
  expect(card as HTMLElement).toHaveTextContent(
    /enter a few ingredients, choose a cuisine if you want, and click\s*find recipes\s*to see grounded retrieval results first\./i
  );
});

test("shows retrieval empty state when no recipes are returned", async () => {
  mockedAxios.post.mockResolvedValueOnce({
    data: {
      mode: "retrieval",
      recipes: [],
      generated_recipes: [],
      meta: {
        recipe_count: 0,
        source: "local_dataset_retrieval_summary_only",
        fallback_reason: "no_strong_matches",
        fallback_suggested: true,
        confidence_score: 0.12,
        confidence_level: "low",
        confidence_reasons: ["No strong recipe candidates matched the request."]
      }
    }
  });

  render(<Page />);

  fireEvent.change(screen.getByLabelText(/^ingredients$/i), {
    target: { value: "dragonfruit, cocoa" }
  });

  fireEvent.click(screen.getByRole("button", { name: /find recipes/i }));

  const heading = await screen.findByRole("heading", {
    name: /no retrieval matches found/i
  });

  const card = heading.closest("div");
  expect(card).not.toBeNull();

  const scoped = within(card as HTMLElement);

  expect(
    scoped.getByText(/we could not find strong recipe summaries for your current request/i)
  ).toBeInTheDocument();

  expect(
    scoped.getByRole("button", { name: /generate instead/i })
  ).toBeInTheDocument();
});

test("shows generation empty state when no generated recipes are returned", async () => {
  mockedAxios.post.mockResolvedValueOnce({
    data: {
      recipes: [],
      meta: {
        recipe_count: 0,
        source: "deterministic_template_generation",
        quality_notes: ["No recipe could be assembled from the provided inputs."]
      }
    }
  });

  render(<Page />);

  fireEvent.change(screen.getByLabelText(/^ingredients$/i), {
    target: { value: "unknown1, unknown2" }
  });

  fireEvent.click(screen.getByRole("button", { name: /generate instead/i }));

  const heading = await screen.findByRole("heading", {
    name: /no generated recipes returned/i
  });

  const card = heading.closest("div");
  expect(card).not.toBeNull();

  const scoped = within(card as HTMLElement);

  expect(
    scoped.getByText(/the generation request completed, but no recipe suggestions were returned/i)
  ).toBeInTheDocument();

  expect(
    scoped.getByText(/no recipe could be assembled from the provided inputs/i)
  ).toBeInTheDocument();
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

    fireEvent.change(screen.getByLabelText(/^ingredients$/i), {
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

    fireEvent.change(screen.getByLabelText(/^ingredients$/i), {
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

    fireEvent.change(screen.getByLabelText(/^ingredients$/i), {
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

    fireEvent.change(screen.getByLabelText(/^ingredients$/i), {
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

  test("loads and shows grounded recipe detail", async () => {
  mockedAxios.post
    .mockResolvedValueOnce({
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
            matched_input_ingredients: ["spinach", "paneer"],
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
    })
    .mockResolvedValueOnce({
      data: {
        title: "Saag Paneer",
        why_chosen: "Selected from retrieved recipe candidates.",
        ingredients: [
          { name: "spinach", quantity: "3 cups" },
          { name: "paneer", quantity: "200 g" }
        ],
        steps: [
          "Wash and chop the spinach.",
          "Cook paneer with spices."
        ],
        substitutions: [],
        nutrition_summary: {
          calories: null,
          protein_g: null,
          carbs_g: null,
          fats_g: null
        },
        warnings: [],
        source_recipe_title: "Saag Paneer",
        grounded: true
      }
    });

  render(<Page />);

  fireEvent.change(screen.getByLabelText(/^ingredients$/i), {
    target: { value: "spinach, paneer" }
  });

  fireEvent.click(screen.getByRole("button", { name: /find recipes/i }));

  await waitFor(() => {
    expect(screen.getByRole("heading", { name: /saag paneer/i })).toBeInTheDocument();
  });

  fireEvent.click(screen.getByRole("button", { name: /view full recipe/i }));

  await waitFor(() => {
    expect(screen.getByRole("heading", { name: /recipe detail/i })).toBeInTheDocument();
  });

  expect(screen.getAllByText(/saag paneer/i).length).toBeGreaterThanOrEqual(2);
  expect(screen.getByText(/selected from retrieved recipe candidates/i)).toBeInTheDocument();
  expect(screen.getByText(/source recipe title:/i)).toBeInTheDocument();
  expect(screen.getByText(/grounded:/i)).toBeInTheDocument();
});

test("shows detail loading state before grounded detail resolves", async () => {
  mockedAxios.post
    .mockResolvedValueOnce({
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
            matched_input_ingredients: ["spinach", "paneer"],
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
    })
    .mockImplementationOnce(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () =>
              resolve({
                data: {
                  title: "Saag Paneer",
                  why_chosen: "Selected from retrieved recipe candidates.",
                  ingredients: [],
                  steps: [],
                  substitutions: [],
                  nutrition_summary: {
                    calories: null,
                    protein_g: null,
                    carbs_g: null,
                    fats_g: null
                  },
                  warnings: [],
                  source_recipe_title: "Saag Paneer",
                  grounded: true
                }
              }),
            50
          )
        )
    );

  render(<Page />);

  fireEvent.change(screen.getByLabelText(/^ingredients$/i), {
    target: { value: "spinach, paneer" }
  });

  fireEvent.click(screen.getByRole("button", { name: /find recipes/i }));

  await waitFor(() => {
    expect(screen.getByRole("heading", { name: /saag paneer/i })).toBeInTheDocument();
  });

  fireEvent.click(screen.getByRole("button", { name: /view full recipe/i }));

  expect(screen.getByText(/loading grounded recipe detail/i)).toBeInTheDocument();

  await waitFor(() => {
    expect(screen.queryByText(/loading grounded recipe detail/i)).not.toBeInTheDocument();
  });
});

test("shows detail error state when generate-detail fails", async () => {
  mockedAxios.post
    .mockResolvedValueOnce({
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
            matched_input_ingredients: ["spinach", "paneer"],
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
    })
    .mockRejectedValueOnce({
      response: {
        data: {
          detail: "Failed to load recipe detail"
        }
      }
    });

  render(<Page />);

  fireEvent.change(screen.getByLabelText(/^ingredients$/i), {
    target: { value: "spinach, paneer" }
  });

  fireEvent.click(screen.getByRole("button", { name: /find recipes/i }));

  await waitFor(() => {
    expect(screen.getByRole("heading", { name: /saag paneer/i })).toBeInTheDocument();
  });

  fireEvent.click(screen.getByRole("button", { name: /view full recipe/i }));

  await waitFor(() => {
    expect(screen.getByText(/failed to load recipe detail/i)).toBeInTheDocument();
  });

  expect(screen.getByRole("heading", { name: /recipe detail/i })).toBeInTheDocument();
});

test("clears detail panel when Clear Detail is clicked", async () => {
  mockedAxios.post
    .mockResolvedValueOnce({
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
            matched_input_ingredients: ["spinach", "paneer"],
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
    })
    .mockResolvedValueOnce({
      data: {
        title: "Saag Paneer",
        why_chosen: "Selected from retrieved recipe candidates.",
        ingredients: [{ name: "spinach", quantity: "3 cups" }],
        steps: ["Cook and serve."],
        substitutions: [],
        nutrition_summary: {
          calories: null,
          protein_g: null,
          carbs_g: null,
          fats_g: null
        },
        warnings: [],
        source_recipe_title: "Saag Paneer",
        grounded: true
      }
    });

  render(<Page />);

  fireEvent.change(screen.getByLabelText(/^ingredients$/i), {
    target: { value: "spinach, paneer" }
  });

  fireEvent.click(screen.getByRole("button", { name: /find recipes/i }));

  await waitFor(() => {
    expect(screen.getByRole("heading", { name: /saag paneer/i })).toBeInTheDocument();
  });

  fireEvent.click(screen.getByRole("button", { name: /view full recipe/i }));

  await waitFor(() => {
    expect(screen.getByRole("heading", { name: /recipe detail/i })).toBeInTheDocument();
  });

    fireEvent.click(screen.getByRole("button", { name: /clear detail/i }));

  expect(
    screen.queryByText(/selected from retrieved recipe candidates/i)
  ).not.toBeInTheDocument();

  expect(
    screen.getByText(/choose a retrieved recipe and click/i)
  ).toBeInTheDocument();

  expect(
    screen.queryByRole("button", { name: /clear detail/i })
  ).not.toBeInTheDocument();
});

test("shows egg toast metadata", async () => {
  mockedAxios.post.mockResolvedValueOnce({
    data: {
      recipes: [
        {
          title: "Egg Toast",
          why_chosen: "Built from bread and egg using a quick pan-toast template.",
          ingredients: [
            { name: "bread", quantity: "2 slices" },
            { name: "egg", quantity: "2" }
          ],
          steps: ["Beat the egg in a bowl.", "Cook the bread until the egg is set."],
          substitutions: [],
          nutrition_summary: { calories: null, protein_g: null, carbs_g: null, fats_g: null },
          warnings: [],
          match_score: 1.0,
          matched_input_ingredients: ["bread", "egg"],
          extra_major_ingredients: [],
          template_name: "egg_toast",
          grounding_source: "template_only"
        }
      ],
      meta: {
        latency_ms: 120,
        model_name: "deterministic_generator",
        recipe_count: 1,
        input_ingredients: ["bread", "egg"],
        quality_notes: [
          "No strong retrieved candidates were available, so recipe was assembled from user ingredients."
        ]
      }
    }
  });

  render(<Page />);
  fireEvent.change(screen.getByLabelText(/^ingredients$/i), { target: { value: "bread, egg" } });
  fireEvent.click(screen.getByRole("button", { name: /generate instead/i }));

  await waitFor(() => {
    expect(screen.getByRole("heading", { name: /egg toast/i })).toBeInTheDocument();
  });

  expect(screen.getAllByText(/egg_toast/i).length).toBeGreaterThanOrEqual(1);
  expect(screen.getAllByText(/template_only/i).length).toBeGreaterThanOrEqual(1);
});

test("shows egg fried rice metadata", async () => {
  mockedAxios.post.mockResolvedValueOnce({
    data: {
      recipes: [
        {
          title: "Egg Fried Rice",
          why_chosen: "Built from rice and egg using a quick stir-fried rice template.",
          ingredients: [
            { name: "rice", quantity: "1 cup" },
            { name: "egg", quantity: "2" }
          ],
          steps: ["Cook the rice.", "Scramble the egg and add rice."],
          substitutions: [],
          nutrition_summary: { calories: null, protein_g: null, carbs_g: null, fats_g: null },
          warnings: [],
          match_score: 1.0,
          matched_input_ingredients: ["rice", "egg"],
          extra_major_ingredients: [],
          template_name: "egg_fried_rice",
          grounding_source: "template_only"
        }
      ],
      meta: {
        latency_ms: 126,
        model_name: "deterministic_generator",
        recipe_count: 1,
        input_ingredients: ["rice", "egg"],
        quality_notes: [
          "No strong retrieved candidates were available, so recipe was assembled from user ingredients."
        ]
      }
    }
  });

  render(<Page />);
  fireEvent.change(screen.getByLabelText(/^ingredients$/i), { target: { value: "rice, egg" } });
  fireEvent.click(screen.getByRole("button", { name: /generate instead/i }));

  await waitFor(() => {
    expect(screen.getByRole("heading", { name: /egg fried rice/i })).toBeInTheDocument();
  });

  expect(screen.getAllByText(/egg_fried_rice/i).length).toBeGreaterThanOrEqual(1);
  expect(screen.getAllByText(/template_only/i).length).toBeGreaterThanOrEqual(1);
});

test("sends avoid ingredients in the retrieve request payload", async () => {
  mockedAxios.post.mockResolvedValueOnce({
    data: {
      mode: "retrieval",
      recipes: [],
      generated_recipes: [],
      meta: { recipe_count: 0, source: "local_dataset_retrieval_summary_only", fallback_suggested: true }
    }
  });

  render(<Page />);

  fireEvent.change(screen.getByLabelText(/^ingredients$/i), {
    target: { value: "tomato, onion" }
  });
  fireEvent.change(screen.getByLabelText(/avoid ingredients/i), {
    target: { value: "egg, garlic" }
  });

  fireEvent.click(screen.getByRole("button", { name: /find recipes/i }));

  await waitFor(() => expect(mockedAxios.post).toHaveBeenCalled());

  expect(mockedAxios.post).toHaveBeenCalledWith(
    expect.stringMatching(/\/retrieve$/),
    expect.objectContaining({
      ingredients: ["tomato", "onion"],
      avoid_ingredients: ["egg", "garlic"],
    })
  );
});

test("sends dietary preferences in the retrieve request payload", async () => {
  mockedAxios.post.mockResolvedValueOnce({
    data: {
      mode: "retrieval",
      recipes: [],
      generated_recipes: [],
      meta: {
        recipe_count: 0,
        source: "local_dataset_retrieval_summary_only",
        fallback_reason: "no_strong_matches",
        fallback_suggested: true,
        confidence_score: 0.12,
        confidence_level: "low",
        confidence_reasons: []
      }
    }
  });

  render(<Page />);

  fireEvent.change(screen.getByLabelText(/^ingredients$/i), {
    target: { value: "tomato, onion" }
  });

  fireEvent.click(screen.getByLabelText(/^vegetarian$/i));
  fireEvent.click(screen.getByLabelText(/^dairy-free$/i));

  fireEvent.click(screen.getByRole("button", { name: /find recipes/i }));

  await waitFor(() => {
    expect(mockedAxios.post).toHaveBeenCalled();
  });

  expect(mockedAxios.post).toHaveBeenCalledWith(
    expect.stringMatching(/\/retrieve$/),
    expect.objectContaining({
      ingredients: ["tomato", "onion"],
      dietary_preferences: ["vegetarian", "dairy-free"],
    })
  );
});

test("shows active constraint badges after retrieval", async () => {
  mockedAxios.post.mockResolvedValueOnce({
    data: {
      mode: "retrieval",
      recipes: [],
      generated_recipes: [],
      meta: {
        recipe_count: 0,
        source: "local_dataset_retrieval_summary_only",
        fallback_reason: "no_strong_matches",
        fallback_suggested: true,
        confidence_score: 0.12,
        confidence_level: "low",
        confidence_reasons: []
      }
    }
  });

  render(<Page />);

  fireEvent.change(screen.getByLabelText(/^ingredients$/i), {
    target: { value: "tomato, onion" }
  });

  fireEvent.change(screen.getByLabelText(/avoid ingredients/i), {
    target: { value: "garlic" }
  });

  fireEvent.click(screen.getByLabelText(/^dairy-free$/i));

  fireEvent.click(screen.getByRole("button", { name: /find recipes/i }));

  await waitFor(() => {
    expect(
      screen.getByRole("heading", { name: /active constraints/i })
    ).toBeInTheDocument();
  });

  expect(screen.getByText(/^Avoid: garlic$/i)).toBeInTheDocument();
  expect(screen.getByText(/^Preset: dairy-free$/i)).toBeInTheDocument();
});

});