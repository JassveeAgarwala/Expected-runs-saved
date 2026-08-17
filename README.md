# Expected Runs Saved API

## Sprint 2 — Player Analytics Sprint — Phase 1 Submission
**Student 4 — Fielding Analytics**  
**API 10: Expected Runs Saved**

---

## Overview

This API calculates **Expected Runs Saved (xRS)** for cricket fielding events using counterfactual reasoning and probabilistic modeling. It estimates how many runs a fielder saved relative to what would have happened with an average fielder.

**Scientific Principle:** Counterfactual reasoning with logistic regression-based probability estimation

---

## Quick Start

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run the API

```bash
python main.py
```

The API will start at `http://localhost:8000`

### View Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Example Request

```bash
curl -X POST "http://localhost:8000/api/v1/fielding/expected-runs-saved" \
  -H "Content-Type: application/json" \
  -d '{
    "fielder_id": "F12345",
    "ball_event": {
      "ball_id": "B001",
      "batsman_id": "B5678",
      "bowler_id": "B9012",
      "runs_scored": 0,
      "is_wicket": true,
      "wicket_type": "caught",
      "shot_type": "drive",
      "shot_direction": "cover",
      "ball_speed": 85.5,
      "launch_angle": 25,
      "horizontal_angle": 45,
      "fielding_outcome": "catch"
    },
    "match_context": {
      "match_id": "M2026001",
      "match_format": "T20",
      "innings": 1,
      "over": 5,
      "ball_in_over": 3,
      "current_run_rate": 7.5,
      "ground_size": "medium"
    },
    "fielder_position": {
      "position_name": "cover",
      "x_coordinate": 25,
      "y_coordinate": 30,
      "distance_from_stumps": 35,
      "angle_from_batsman": 45
    },
    "fielder_movement": {
      "initial_reaction_time": 0.3,
      "max_speed_achieved": 6.5,
      "average_speed": 5.2,
      "path_efficiency": 0.85,
      "body_position_quality": 0.9
    }
  }'
```

---

## Example Response

```json
{
  "fielder_id": "F12345",
  "ball_id": "B001",
  "runs_saved": 2.85,
  "runs_saved_adjusted": 3.12,
  "confidence_score": 0.87,
  "breakdown": {
    "expected_runs_without_fielder": 4.2,
    "expected_runs_with_average_fielder": 2.85,
    "actual_runs_conceded": 0,
    "catch_probability": 0.68,
    "stop_probability": 0.92
  },
  "interpretation": "Excellent fielding effort. This catch saved an estimated 2.85 runs compared to average expectation. Difficulty: hard.",
  "difficulty_rating": "hard"
}
```

---

## Files

- `main.py` - FastAPI app and routes
- `schemas.py` - Request/response models
- `services.py` - Core analytics logic
- `utils.py` - Validation and probability functions
- `requirements.txt` - Dependencies

---

## API Endpoints

- `POST /api/v1/fielding/expected-runs-saved` - Calculate xRS
- `GET /health` - Health check

---

## Documentation

- **HANDOVER.md** - Comprehensive integration guide
- **Swagger UI** - Interactive API documentation

---

## About

**Version**: 1.0.0  
**Date**: August 17, 2026  
**Sprint**: 2 — Player Analytics Sprint
