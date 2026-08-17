"""
Expected Runs Saved API - Fielding Analytics
API 10 - Sprint 2 Phase 1 Submission
Student 4 - Fielding Analytics
"""

from fastapi import FastAPI, HTTPException, status
from schemas import ExpectedRunsSavedRequest, ExpectedRunsSavedResponse, ErrorResponse
from services import calculate_expected_runs_saved
from utils import validate_request_data
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Expected Runs Saved API",
    description="Fielding Analytics API to estimate runs saved by a fielder relative to expected outcomes",
    version="1.0.0"
)


@app.post(
    "/api/v1/fielding/expected-runs-saved",
    response_model=ExpectedRunsSavedResponse,
    responses={
        200: {"description": "Successful calculation"},
        400: {"description": "Validation error"},
        422: {"description": "Invalid input data"},
        500: {"description": "Internal server error"}
    },
    summary="Calculate Expected Runs Saved",
    description="Calculates the Expected Runs Saved (xRS) metric using counterfactual reasoning"
)
async def calculate_xrs(request: ExpectedRunsSavedRequest):
    """Calculate Expected Runs Saved for a fielding event."""
    try:
        # Validate request data
        validation_result = validate_request_data(request)
        if not validation_result["is_valid"]:
            logger.warning(f"Validation failed: {validation_result['message']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=validation_result["message"]
            )
        
        # Calculate expected runs saved
        result = calculate_expected_runs_saved(request)
        
        logger.info(f"xRS calculated for fielder {request.fielder_id}: {result['runs_saved']:.2f}")
        
        return ExpectedRunsSavedResponse(**result)
    
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/health", summary="Health Check")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Expected Runs Saved API"}


# For Render deployment
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
