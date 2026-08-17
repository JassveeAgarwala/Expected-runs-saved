"""
Core analytics logic for Expected Runs Saved API
Implements counterfactual reasoning and statistical modeling
"""

import math
from typing import Dict, Any
from schemas import ExpectedRunsSavedRequest, RunsSavedBreakdown
from utils import calculate_catch_probability, calculate_stop_probability, get_difficulty_rating


def calculate_expected_runs_without_fielder(
    ball_speed: float,
    launch_angle: float,
    ground_size: str,
    match_format: str
) -> float:
    """Calculate expected runs if no fielder was present (counterfactual baseline)."""
    speed_factor = min(ball_speed / 100.0, 1.5)
    
    if 15 <= launch_angle <= 35:
        launch_factor = 1.0
    elif launch_angle < 15:
        launch_factor = 0.7 + (launch_angle / 15) * 0.3
    else:
        launch_factor = max(0.3, 1.0 - (launch_angle - 35) / 55)
    
    ground_multipliers = {"small": 0.85, "medium": 1.0, "large": 1.15}
    ground_factor = ground_multipliers.get(ground_size, 1.0)
    
    format_multipliers = {"T20": 1.1, "ODI": 1.0, "TEST": 0.9}
    format_factor = format_multipliers.get(match_format, 1.0)
    
    base_runs = speed_factor * launch_factor * 6.0
    expected_runs = base_runs * ground_factor * format_factor
    
    return min(expected_runs, 6.0)


def calculate_expected_runs_with_average_fielder(
    ball_speed: float,
    launch_angle: float,
    horizontal_angle: float,
    fielder_distance: float,
    fielder_angle_diff: float,
    shot_direction: str,
    match_context: Dict[str, Any]
) -> float:
    """Calculate expected runs with an average fielder."""
    catch_prob_avg = calculate_catch_probability(
        ball_speed=ball_speed,
        launch_angle=launch_angle,
        distance=fielder_distance,
        angle_difference=fielder_angle_diff,
        is_average_fielder=True
    )
    
    stop_prob_avg = calculate_stop_probability(
        ball_speed=ball_speed,
        launch_angle=launch_angle,
        distance=fielder_distance,
        angle_difference=fielder_angle_diff,
        is_average_fielder=True
    )
    
    runs_if_catch = 0.0
    runs_if_stopped = 1.5
    runs_if_missed = calculate_expected_runs_without_fielder(
        ball_speed, launch_angle, match_context.get("ground_size", "medium"),
        match_context.get("match_format", "ODI")
    )
    
    expected_runs = (
        catch_prob_avg * runs_if_catch +
        stop_prob_avg * (1 - catch_prob_avg) * runs_if_stopped +
        (1 - stop_prob_avg) * runs_if_missed
    )
    
    return expected_runs


def calculate_actual_runs_conceded(ball_event: Dict[str, Any], fielding_outcome: str) -> float:
    """Calculate actual runs conceded."""
    runs_scored = ball_event.get("runs_scored", 0)
    extras = ball_event.get("extras", 0)
    
    if fielding_outcome in ["catch", "direct_hit", "throw_run_out"] and ball_event.get("is_wicket", False):
        return 0.0
    
    if fielding_outcome in ["stop", "deflected"]:
        return float(runs_scored)
    
    if fielding_outcome == "missed":
        return float(runs_scored + extras + 2)
    
    return float(runs_scored + extras)


def calculate_runs_saved_breakdown(request: ExpectedRunsSavedRequest) -> RunsSavedBreakdown:
    """Calculate complete breakdown of runs saved components."""
    ball_event = request.ball_event
    match_context = request.match_context
    fielder_position = request.fielder_position
    
    ball_speed = ball_event.ball_speed
    launch_angle = ball_event.launch_angle
    horizontal_angle = ball_event.horizontal_angle
    shot_direction = ball_event.shot_direction
    fielding_outcome = ball_event.fielding_outcome.value
    
    fielder_distance = fielder_position.distance_from_stumps
    fielder_angle = fielder_position.angle_from_batsman
    
    direction_angles = {
        "cover": 45, "mid-off": 20, "mid-on": -20, "mid-wicket": -45,
        "square-leg": -70, "point": 60, "gully": 80, "slip": 85,
        "third-man": 110, "fine-leg": -110, "long-off": 15, "long-on": -15
    }
    shot_angle = direction_angles.get(shot_direction, horizontal_angle)
    angle_diff = abs(fielder_angle - shot_angle)
    
    context_dict = {
        "ground_size": match_context.ground_size,
        "match_format": match_context.match_format.value
    }
    
    expected_no_fielder = calculate_expected_runs_without_fielder(
        ball_speed=ball_speed,
        launch_angle=launch_angle,
        ground_size=match_context.ground_size,
        match_format=match_context.match_format.value
    )
    
    expected_avg_fielder = calculate_expected_runs_with_average_fielder(
        ball_speed=ball_speed,
        launch_angle=launch_angle,
        horizontal_angle=horizontal_angle,
        fielder_distance=fielder_distance,
        fielder_angle_diff=angle_diff,
        shot_direction=shot_direction,
        match_context=context_dict
    )
    
    actual_runs = calculate_actual_runs_conceded(
        ball_event=ball_event.dict(),
        fielding_outcome=fielding_outcome
    )
    
    catch_prob = calculate_catch_probability(
        ball_speed=ball_speed,
        launch_angle=launch_angle,
        distance=fielder_distance,
        angle_difference=angle_diff,
        is_average_fielder=False,
        movement_data=request.fielder_movement
    )
    
    stop_prob = calculate_stop_probability(
        ball_speed=ball_speed,
        launch_angle=launch_angle,
        distance=fielder_distance,
        angle_difference=angle_diff,
        is_average_fielder=False,
        movement_data=request.fielder_movement
    )
    
    runs_saved_vs_no_fielder = expected_no_fielder - actual_runs
    runs_saved_vs_average = expected_avg_fielder - actual_runs
    
    return RunsSavedBreakdown(
        expected_runs_without_fielder=round(expected_no_fielder, 2),
        expected_runs_with_average_fielder=round(expected_avg_fielder, 2),
        actual_runs_conceded=round(actual_runs, 2),
        runs_saved_vs_no_fielder=round(runs_saved_vs_no_fielder, 2),
        runs_saved_vs_average=round(runs_saved_vs_average, 2),
        catch_probability=round(catch_prob, 2),
        stop_probability=round(stop_prob, 2)
    )


def calculate_confidence_score(request: ExpectedRunsSavedRequest, breakdown: RunsSavedBreakdown) -> float:
    """Calculate confidence score for the xRS estimate."""
    confidence = 0.7
    
    if request.fielder_movement is not None:
        confidence += 0.15
    
    if 0.2 <= breakdown.catch_probability <= 0.8:
        confidence += 0.1
    elif 0.1 <= breakdown.catch_probability <= 0.9:
        confidence += 0.05
    
    ball_speed = request.ball_event.ball_speed
    if ball_speed < 50 or ball_speed > 130:
        confidence -= 0.1
    
    return max(0.0, min(1.0, confidence))


def generate_interpretation(runs_saved: float, difficulty: str, fielding_outcome: str, breakdown: RunsSavedBreakdown) -> str:
    """Generate human-readable interpretation."""
    outcome_text = {
        "catch": "catch", "stop": "stop", "missed": "missed opportunity",
        "deflected": "deflection", "direct_hit": "direct hit", "throw_run_out": "run-out throw"
    }.get(fielding_outcome, "fielding effort")
    
    if runs_saved > 2.0:
        quality = "Exceptional"
    elif runs_saved > 1.0:
        quality = "Excellent"
    elif runs_saved > 0.5:
        quality = "Good"
    elif runs_saved > 0:
        quality = "Slightly positive"
    elif runs_saved > -0.5:
        quality = "Neutral"
    else:
        quality = "Below expectation"
    
    return (
        f"{quality} fielding effort. This {outcome_text} saved an estimated "
        f"{runs_saved:.2f} runs compared to average expectation. "
        f"Difficulty: {difficulty}. "
        f"Catch probability: {breakdown.catch_probability:.0%}, "
        f"Stop probability: {breakdown.stop_probability:.0%}."
    )


def calculate_expected_runs_saved(request: ExpectedRunsSavedRequest) -> Dict[str, Any]:
    """Main function to calculate Expected Runs Saved."""
    breakdown = calculate_runs_saved_breakdown(request)
    runs_saved = breakdown.runs_saved_vs_average
    
    difficulty = get_difficulty_rating(
        ball_speed=request.ball_event.ball_speed,
        launch_angle=request.ball_event.launch_angle,
        distance=request.fielder_position.distance_from_stumps,
        angle_diff=abs(request.fielder_position.angle_from_batsman - request.ball_event.horizontal_angle),
        movement_data=request.fielder_movement
    )
    
    difficulty_multipliers = {"easy": 0.8, "medium": 1.0, "hard": 1.2, "very_hard": 1.4}
    runs_saved_adjusted = runs_saved * difficulty_multipliers.get(difficulty, 1.0)
    
    confidence = calculate_confidence_score(request, breakdown)
    interpretation = generate_interpretation(
        runs_saved=runs_saved,
        difficulty=difficulty,
        fielding_outcome=request.ball_event.fielding_outcome.value,
        breakdown=breakdown
    )
    
    return {
        "fielder_id": request.fielder_id,
        "ball_id": request.ball_event.ball_id,
        "runs_saved": round(runs_saved, 2),
        "runs_saved_adjusted": round(runs_saved_adjusted, 2),
        "confidence_score": round(confidence, 2),
        "breakdown": breakdown.dict(),
        "interpretation": interpretation,
        "difficulty_rating": difficulty
    }
