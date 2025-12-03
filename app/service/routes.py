import logging
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from agent.dependencies import get_orchestrator
from agent.orchestration import Orchestrator
from config.schemas import UserInput

router = APIRouter()
LOGGER = logging.getLogger("service")
LOGGER.setLevel(logging.INFO)


@router.post("/chat")
async def chat(
    request: UserInput, orchestrator: Annotated[Orchestrator, Depends(get_orchestrator)]
) -> JSONResponse:
    session_id = request.session_id or f"session-{uuid4()}"
    user_id = request.user_id or "user-123"
    user_input = request.user_input
    try:
        result = await orchestrator.run(session_id, user_id, user_input)
        return JSONResponse(content=result, status_code=200)
    except Exception as e:
        LOGGER.exception("Orchestrator failed.")
        return JSONResponse(content={"error": f"Orchestrator error: {e}"}, status_code=500)


@router.get("/health_check", include_in_schema=False)
async def health_check():
    return JSONResponse(content={"status": "ok"}, status_code=200)
