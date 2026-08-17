"""
Pydantic schemas for Expected Runs Saved API
Defines request and response models with validation
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime


class FieldingOutcome(str, Enum):
    CATCH = "catch"
    STOP = "stop"
    MISSED = "missed"
    DEFLECTED = "deflected"
    DIRECT_HIT = "direct_hit"
    THROW_RUN_OUT = "throw_run_out"
    NO_INVOLVEMENT = "no_involvement"


class WicketType(str, Enum):
    CAUGHT = "caught"
    RUN_OUT = "run_out"
    STUMPED = "stumped"
    NOT_OUT = "not_out"


class MatchFormat(str, Enum):
    T20 = "T20"
    ODI = "ODI"
    TEST = "TEST"


class FielderPosition(BaseModel):
    """Fielder's starting position on the field"""
    position_name: str = Field(..., description="Fielding position name")
    x_coordinate: float = Field(..., ge=0, le=100, description="X coordinate (0-100m)")
    y_coordinate: float = Field(..., ge=0, le=100, description="Y coordinate (0-100m)")
    distance_from_stumps: float = Field(..., ge=0, description="Distance from stumps (meters)")
    angle_from_batsman: float = Field(..., ge=0, le=360, description="Angle from batsman (degrees)")


class BallEvent(BaseModel):
    """Raw ball event data from webapp"""
    ball_id: str = Field(..., description="Unique ball identifier")
    batsman_id: str = Field(..., description="Striker's ID")
    bowler_id: str = Field(..., description="Bowler's ID")
    runs_scored: int = Field(..., ge=0, description="Runs scored off the bat")
    extras: int = Field(default=0, ge=0, description="Extras conceded")
    is_wicket: bool = Field(default=False, description="Whether wicket fell")
    wicket_type: Optional[WicketType] = Field(default=None, description="Type of wicket")
    shot_type: str = Field(..., description="Type of shot played")
    shot_direction: str = Field(..., description="Direction of shot")
    ball_speed: float = Field(..., gt=0, description="Ball speed after being hit (km/h)")
    launch_angle: float = Field(..., ge=-90, le=90, description="Vertical launch angle (degrees)")
    horizontal_angle: float = Field(..., ge=-180, le=180, description="Horizontal angle (degrees)")
    fielding_outcome: FieldingOutcome = Field(..., description="What the fielder did")
    time_to_reach_ball: Optional[float] = Field(default=None, ge=0, description="Time to reach ball (seconds)")
    distance_covered: Optional[float] = Field(default=None, ge=0, description="Distance fielder ran (meters)")


class MatchContext(BaseModel):
    """Match situation and conditions"""
    match_id: str = Field(..., description="Unique match identifier")
    match_format: MatchFormat = Field(..., description="Format of the match")
    innings: int = Field(..., ge=1, le=4, description="Innings number")
    over: int = Field(..., ge=0, description="Over number (0-indexed)")
    ball_in_over: int = Field(..., ge=1, le=6, description="Ball number in over")
    runs_required: Optional[int] = Field(default=None, ge=0, description="Runs required to win")
    balls_remaining: Optional[int] = Field(default=None, ge=0, description="Balls remaining")
    current_run_rate: float = Field(..., ge=0, description="Current run rate")
    required_run_rate: Optional[float] = Field(default=None, ge=0, description="Required run rate")
    pitch_condition: str = Field(default="neutral", description="Pitch condition")
    weather_condition: str = Field(default="clear", description="Weather condition")
    ground_size: str = Field(default="medium", description="Ground size (small/medium/large)")


class FielderMovement(BaseModel):
    """Fielder's movement during the ball"""
    initial_reaction_time: float = Field(..., ge=0, description="Reaction time (seconds)")
    max_speed_achieved: float = Field(..., ge=0, description="Maximum speed (m/s)")
    average_speed: float = Field(..., ge=0, description="Average speed (m/s)")
    path_efficiency: float = Field(..., ge=0, le=1, description="Path efficiency (0-1)")
    body_position_quality: float = Field(..., ge=0, le=1, description="Body position quality (0-1)")


class ExpectedRunsSavedRequest(BaseModel):
    """Complete request schema for xRS calculation"""
    fielder_id: str = Field(..., description="Unique fielder identifier")
    ball_event: BallEvent = Field(..., description="Ball event data")
    match_context: MatchContext = Field(..., description="Match context")
    fielder_position: FielderPosition = Field(..., description="Fielder's starting position")
    fielder_movement: Optional[FielderMovement] = Field(default=None, description="Fielder's movement data")


class RunsSavedBreakdown(BaseModel):
    """Detailed breakdown of runs saved calculation"""
    expected_runs_without_fielder: float = Field(..., description="Expected runs if no fielder")
    expected_runs_with_average_fielder: float = Field(..., description="Expected runs with average fielder")
    actual_runs_conceded: float = Field(..., description="Actual runs conceded")
    runs_saved_vs_no_fielder: float = Field(..., description="Runs saved vs no fielder")
    runs_saved_vs_average: float = Field(..., description="Runs saved vs average fielder")
    catch_probability: float = Field(..., ge=0, le=1, description="Probability of catch")
    stop_probability: float = Field(..., ge=0, le=1, description="Probability of stop")


class ExpectedRunsSavedResponse(BaseModel):
    """Response schema for xRS calculation"""
    fielder_id: str = Field(..., description="Fielder ID")
    ball_id: str = Field(..., description="Ball ID")
    runs_saved: float = Field(..., description="Total runs saved (primary metric)")
    runs_saved_adjusted: float = Field(..., description="Runs saved adjusted for difficulty")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence score (0-1)")
    breakdown: RunsSavedBreakdown = Field(..., description="Detailed breakdown")
    interpretation: str = Field(..., description="Human-readable interpretation")
    difficulty_rating: str = Field(..., description="Difficulty rating")
    timestamp: datetime = Field(default_factory=datetime.now, description="Calculation timestamp")


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(default=None, description="Additional details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
