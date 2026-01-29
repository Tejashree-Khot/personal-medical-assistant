import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import JSONResponse

from agent.dependencies import get_orchestrator, get_profile_extractor
from agent.orchestration import Orchestrator
from agent.profile_extractor import ProfileExtractor
from config.node_schemas import UserInput

router = APIRouter()
LOGGER = logging.getLogger("service")
LOGGER.setLevel(logging.INFO)


@router.post("/chat")
async def chat(
    request: UserInput,
    orchestrator: Annotated[Orchestrator, Depends(get_orchestrator)],
    profile_extractor: Annotated[ProfileExtractor, Depends(get_profile_extractor)],
    background_tasks: BackgroundTasks,
) -> JSONResponse:
    session_id = request.session_id or str(uuid.uuid4())
    user_id = request.user_id or "user-123"
    user_input = request.user_input

    try:
        # extract user profile in the background to reduce the latency, (fire-and-forget)
        background_tasks.add_task(profile_extractor.run, user_id, user_input)
    except Exception:
        LOGGER.exception("Profile extraction failed.")

    try:
        result = await orchestrator.run(session_id, user_id, user_input)
        return JSONResponse(content=result, status_code=200)
    except Exception as e:
        LOGGER.exception("Orchestrator failed.")
        return JSONResponse(content={"error": f"Orchestrator error: {e}"}, status_code=500)


@router.get("/health_check", include_in_schema=False)
async def health_check():
    return JSONResponse(content={"status": "ok"}, status_code=200)
