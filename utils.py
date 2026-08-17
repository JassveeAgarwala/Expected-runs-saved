"""
Utility and validation functions for Expected Runs Saved API
"""

import math
from typing import Dict, Any, Optional
from schemas import ExpectedRunsSavedRequest, FielderMovement


def validate_request_data(request: ExpectedRunsSavedRequest) -> Dict[str, Any]:
    """Validate incoming request data."""
    errors = []
    
    ball_event = request.ball_event
    if ball_event.ball_speed <= 0:
        errors.append("Ball speed must be positive")
    if ball_event.ball_speed > 150:
        errors.append("Ball speed seems unrealistically high (>150 km/h)")
    if not -90 <= ball_event.launch_angle <= 90:
        errors.append("Launch angle must be between -90 and 90 degrees")
    
    fielder_pos = request.fielder_position
    if fielder_pos.distance_from_stumps <= 0:
        errors.append("Distance from stumps must be positive")
    if fielder_pos.distance_from_stumps > 100:
        errors.append("Fielder distance seems too large (>100m)")
    
    match_ctx = request.match_context
    if match_ctx.over < 0:
        errors.append("Over number cannot be negative")
    if not 1 <= match_ctx.ball_in_over <= 6:
        errors.append("Ball in over must be between 1 and 6")
    if match_ctx.current_run_rate < 0:
        errors.append("Run rate cannot be negative")
    
    if ball_event.is_wicket and ball_event.fielding_outcome.value == "missed":
        errors.append("Wicket cannot fall if fielder missed the ball")
    
    if request.fielder_movement:
        movement = request.fielder_movement
        if movement.initial_reaction_time < 0:
            errors.append("Reaction time cannot be negative")
        if not 0 <= movement.path_efficiency <= 1:
            errors.append("Path efficiency must be between 0 and 1")
        if not 0 <= movement.body_position_quality <= 1:
            errors.append("Body position quality must be between 0 and 1")
    
    if errors:
        return {"is_valid": False, "message": "; ".join(errors)}
    
    return {"is_valid": True, "message": "Validation passed"}


def calculate_catch_probability(
    ball_speed: float,
    launch_angle: float,
    distance: float,
    angle_difference: float,
    is_average_fielder: bool = True,
    movement_data: Optional[FielderMovement] = None
) -> float:
    """Calculate probability of taking a catch using logistic regression."""
    difficulty_score = 0.0
    
    # Ball speed factor
    if 60 <= ball_speed <= 90:
        speed_factor = 0.0
    elif ball_speed < 60:
        speed_factor = (60 - ball_speed) / 60 * 0.5
    else:
        speed_factor = min((ball_speed - 90) / 60, 1.0) * 0.5
    difficulty_score += speed_factor
    
    # Launch angle factor
    if 15 <= launch_angle <= 35:
        angle_factor = 0.0
    elif launch_angle < 15:
        angle_factor = (15 - launch_angle) / 15 * 0.4
    else:
        angle_factor = min((launch_angle - 35) / 55, 1.0) * 0.4
    difficulty_score += angle_factor
    
    # Distance factor
    if distance < 15:
        distance_factor = 0.0
    elif distance < 30:
        distance_factor = (distance - 15) / 15 * 0.3
    elif distance < 50:
        distance_factor = 0.3 + (distance - 30) / 20 * 0.4
    else:
        distance_factor = 0.7 + (distance - 50) / 50 * 0.3
    difficulty_score += distance_factor
    
    # Angle difference factor
    if angle_difference < 15:
        angle_diff_factor = 0.0
    elif angle_difference < 45:
        angle_diff_factor = (angle_difference - 15) / 30 * 0.3
    else:
        angle_diff_factor = 0.3 + min((angle_difference - 45) / 45, 1.0) * 0.4
    difficulty_score += angle_diff_factor
    
    # Movement adjustment
    if movement_data and not is_average_fielder:
        movement_bonus = (
            movement_data.path_efficiency * 0.15 +
            movement_data.body_position_quality * 0.15 -
            min(movement_data.initial_reaction_time / 1.0, 1.0) * 0.1
        )
        difficulty_score -= movement_bonus
    
    base_probability = 1.0 / (1.0 + math.exp(difficulty_score * 3))
    
    if is_average_fielder:
        final_probability = base_probability * 0.85
    else:
        final_probability = base_probability * (1.05 if movement_data else 0.95)
    
    return max(0.0, min(1.0, final_probability))


def calculate_stop_probability(
    ball_speed: float,
    launch_angle: float,
    distance: float,
    angle_difference: float,
    is_average_fielder: bool = True,
    movement_data: Optional[FielderMovement] = None
) -> float:
    """Calculate probability of stopping the ball."""
    difficulty_score = 0.0
    
    if 50 <= ball_speed <= 100:
        speed_factor = 0.0
    elif ball_speed < 50:
        speed_factor = (50 - ball_speed) / 50 * 0.3
    else:
        speed_factor = min((ball_speed - 100) / 50, 1.0) * 0.4
    difficulty_score += speed_factor
    
    if launch_angle < 10:
        angle_factor = 0.0
    elif launch_angle < 25:
        angle_factor = (launch_angle - 10) / 15 * 0.3
    else:
        angle_factor = 0.3 + min((launch_angle - 25) / 65, 1.0) * 0.4
    difficulty_score += angle_factor
    
    if distance < 20:
        distance_factor = 0.0
    elif distance < 40:
        distance_factor = (distance - 20) / 20 * 0.3
    elif distance < 60:
        distance_factor = 0.3 + (distance - 40) / 20 * 0.4
    else:
        distance_factor = 0.7 + min((distance - 60) / 40, 1.0) * 0.3
    difficulty_score += distance_factor
    
    if angle_difference < 20:
        angle_diff_factor = 0.0
    elif angle_difference < 50:
        angle_diff_factor = (angle_difference - 20) / 30 * 0.3
    else:
        angle_diff_factor = 0.3 + min((angle_difference - 50) / 40, 1.0) * 0.4
    difficulty_score += angle_diff_factor
    
    if movement_data and not is_average_fielder:
        movement_bonus = (
            movement_data.path_efficiency * 0.12 +
            movement_data.body_position_quality * 0.12 -
            min(movement_data.initial_reaction_time / 1.0, 1.0) * 0.08
        )
        difficulty_score -= movement_bonus
    
    base_probability = 1.0 / (1.0 + math.exp(difficulty_score * 2.5))
    
    if is_average_fielder:
        final_probability = min(0.95, base_probability * 0.90 + 0.08)
    else:
        final_probability = min(0.98, base_probability * 1.0 + 0.05) if movement_data else min(0.95, base_probability * 0.92 + 0.06)
    
    return max(0.0, min(1.0, final_probability))


def get_difficulty_rating(
    ball_speed: float,
    launch_angle: float,
    distance: float,
    angle_diff: float,
    movement_data: Optional[FielderMovement] = None
) -> str:
    """Assign difficulty rating to the fielding chance."""
    difficulty_score = 0.0
    
    if ball_speed < 70:
        difficulty_score += 0.2
    elif ball_speed < 90:
        difficulty_score += 0.4
    elif ball_speed < 110:
        difficulty_score += 0.6
    else:
        difficulty_score += 0.8
    
    if 15 <= launch_angle <= 35:
        difficulty_score += 0.3
    elif launch_angle < 10:
        difficulty_score += 0.2
    else:
        difficulty_score += 0.5
    
    if distance < 20:
        difficulty_score += 0.2
    elif distance < 35:
        difficulty_score += 0.4
    elif distance < 50:
        difficulty_score += 0.6
    else:
        difficulty_score += 0.8
    
    if angle_diff < 20:
        difficulty_score += 0.2
    elif angle_diff < 45:
        difficulty_score += 0.4
    else:
        difficulty_score += 0.6
    
    if movement_data and movement_data.path_efficiency > 0.85 and movement_data.body_position_quality > 0.85:
        difficulty_score -= 0.15
    
    if difficulty_score < 0.8:
        return "easy"
    elif difficulty_score < 1.4:
        return "medium"
    elif difficulty_score < 2.0:
        return "hard"
    else:
        return "very_hard"
