import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def get_data_dir() -> str:
    return os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "data"))


app = FastAPI(title="SMRT Systems Take-Home API", version="0.1.0")

# Basic CORS for local development and Expo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Routers
from .routers import health, datasource, chat  # noqa: E402

app.include_router(health.router)
app.include_router(datasource.router)
app.include_router(chat.router)


@app.on_event("startup")
def on_startup():
    # Defer heavy loading to /datasource/refresh to keep startup quick
    pass

