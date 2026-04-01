# RECIPE-INTELLIGENCE-COPILOT


A retrieval-first recipe assistant with a FastAPI AI service, a Next.js frontend, and automated tests.

It supports two main flows:

- **Retrieve**: find matching recipes from a local dataset using hybrid retrieval, confidence scoring, and fallback signals
- **Generate**: create deterministic, template-based recipes from user ingredients when retrieval is weak or when the user chooses generation

---

## Features

### Retrieval-first recipe search
- Hybrid retrieval pipeline
- Ingredient normalization and canonical matching
- Confidence score, confidence level, and confidence reasons
- Fallback suggestion when retrieval quality is low

### Deterministic generation
- Fast template-based generation
- No LLM latency in the current generation path
- Template metadata:
  - `template_name`
  - `grounding_source`
- Honest low-confidence fallback for unknown ingredient combinations

### Frontend UX
- Retrieve vs generate flows shown clearly
- Confidence metadata displayed for retrieval
- Template and grounding metadata displayed for generated recipes
- Quality notes and latency surfaced in the UI

### Testing
- Backend tests with `pytest`
- Frontend tests with Jest + React Testing Library
- Ready for GitHub Actions CI

---

## Repository structure

```text
RECIPE-INTELLIGENCE-COPILOT/
├── .github/
│   └── workflows/
├── ai-service-python/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   ├── models/
│   │   └── services/
│   ├── tests/
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── pytest.ini
├── frontend/
│   ├── __tests__/
│   ├── app/
│   ├── public/
│   ├── package.json
│   └── jest.config.ts
├── backend-node/
└── docs/