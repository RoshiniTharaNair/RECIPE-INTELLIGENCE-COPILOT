def test_retrieve_api_strong_match(client, monkeypatch):
    from app.api.routes import retrieve as retrieve_route

    def fake_retrieve_with_fallback_signal(_data, top_k=10):
        return {
            "recipes": [
                {
                    "id": "recipe-1",
                    "title": "Saag Paneer",
                    "description": "Spinach and paneer curry.",
                    "cuisine": "Indian",
                    "prep_time_mins": 30,
                    "total_time_mins": 30,
                    "servings": 2,
                    "match_score": 0.92,
                    "why_chosen": "Strong ingredient and cuisine match.",
                    "matched_input_ingredients": ["spinach", "cheese"],
                    "extra_major_count": 1,
                    "confidence_score": 0.88,
                    "confidence_level": "high",
                    "confidence_reasons": [
                        "All requested ingredients matched strongly."
                    ],
                }
            ],
            "fallback_needed": False,
            "fallback_reason": None,
            "confidence_score": 0.88,
            "confidence_level": "high",
            "confidence_reasons": [
                "All requested ingredients matched strongly."
            ],
        }

    monkeypatch.setattr(
        retrieve_route,
        "retrieve_with_fallback_signal",
        fake_retrieve_with_fallback_signal,
    )

    response = client.post(
        "/retrieve",
        json={
            "ingredients": ["spinach", "cheese"],
            "cuisine": "Indian",
            "prep_time": 30,
            "servings": 2,
            "skill_level": "beginner",
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["mode"] == "retrieval"
    assert len(body["recipes"]) == 1
    assert body["generated_recipes"] == []

    meta = body["meta"]
    assert meta["recipe_count"] == 1
    assert meta["source"] == "local_dataset_retrieval_summary_only"
    assert meta["fallback_suggested"] is False
    assert meta["fallback_reason"] is None
    assert meta["confidence_score"] == 0.88
    assert meta["confidence_level"] == "high"
    assert len(meta["confidence_reasons"]) == 1


def test_retrieve_api_weak_match_sets_fallback(client, monkeypatch):
    from app.api.routes import retrieve as retrieve_route

    def fake_retrieve_with_fallback_signal(_data, top_k=10):
        return {
            "recipes": [],
            "fallback_needed": True,
            "fallback_reason": "no_retrieval_results",
            "confidence_score": 0.0,
            "confidence_level": "low",
            "confidence_reasons": [
                "No retrieval candidates were found."
            ],
        }

    monkeypatch.setattr(
        retrieve_route,
        "retrieve_with_fallback_signal",
        fake_retrieve_with_fallback_signal,
    )

    response = client.post(
        "/retrieve",
        json={
            "ingredients": ["dragonfruit", "truffle oil", "kimchi ice cream"],
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["mode"] == "retrieval"
    assert body["recipes"] == []
    assert body["generated_recipes"] == []

    meta = body["meta"]
    assert meta["recipe_count"] == 0
    assert meta["fallback_suggested"] is True
    assert meta["fallback_reason"] == "no_retrieval_results"
    assert meta["confidence_score"] == 0.0
    assert meta["confidence_level"] == "low"
    assert meta["confidence_reasons"] == ["No retrieval candidates were found."]