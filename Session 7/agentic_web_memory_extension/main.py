import os
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from action import Actions
from decision import decide_action
from perception import parse_query


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

app = FastAPI(title="Agentic Web Memory Extension API")

# Allow local dev and Chrome extension origins
allowed_origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
    "chrome-extension://*",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

actions = Actions(DATA_DIR)


class StoreRequest(BaseModel):
    url: str
    text: str


class SearchRequest(BaseModel):
    query: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/store_page")
def store_page(req: StoreRequest) -> dict:
    return actions.store_page(req.url, req.text)


@app.post("/api/search")
def search(req: SearchRequest) -> dict:
    parsed = parse_query(actions.llm, req.query)
    action_name = decide_action(parsed.get("intent", "search"))
    if action_name == "store_page":
        # Not used from popup, but keep interface consistent
        return {"status": "noop"}
    result = actions.find_relevant_page(req.query)
    return result


def run() -> None:
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    run()


