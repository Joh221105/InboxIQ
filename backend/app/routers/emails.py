from fastapi import APIRouter, Depends, HTTPException

from app.auth_jwt import current_user_id
from app.gmail_fetch import list_message_previews

router = APIRouter(prefix="/emails", tags=["emails"])


@router.get("")
async def list_emails(user_id: str = Depends(current_user_id)):
    try:
        messages = list_message_previews(user_id, max_results=15)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Gmail API error: {e!s}") from e
    return {"count": len(messages), "messages": messages}
