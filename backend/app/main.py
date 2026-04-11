from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import emails, gmail_auth

app = FastAPI(title="InboxIQ API", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}


def _configure_cors(application: FastAPI) -> None:
    settings = get_settings()
    origins = {
        settings.frontend_url.rstrip("/"),
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    }
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


_configure_cors(app)
app.include_router(gmail_auth.router)
app.include_router(emails.router)
