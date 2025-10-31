## Agentic Web Memory Extension

## FastAPI backend + Chrome extension for storing webpage embeddings and RAG search with Gemini.

### Quick start (PowerShell)
- **Install uv**:
```powershell
iwr https://astral.sh/uv/install.ps1 -UseBasicParsing | iex
```
- **Install deps**:
```powershell
cd agentic_web_memory_extension
uv sync
```

### API
- `GET /health` → `{ status: "ok" }`
- `POST /api/store_page` body: `{ url, text }`
- `POST /api/search` body: `{ query }`

### Load Chrome Extension
chrome://extensions → Load unpacked → `agentic_web_memory_extension/chrome_extension`

### Agentic layer (brief)
- **Perception (`perception.py`)**: parses the user query via LLM to infer `intent` (store|search) and a short `topic`.
- **Decision (`decision.py`)**: maps `intent` → action (`store_page` or `find_relevant_page`).
- **Memory ('memory.py')**: user preferences
- **Action (`action.py`)**: executes:
  - `store_page(url, text)`: chunk → embed → add to FAISS; summarize page to memory.
  - `find_relevant_page(query)`: embed query → vector search → filter → highlights.
    

### LLM interface (brief)
- Wrapper: `utils/llm_interface.py` (Gemini).
- Env: `GEMINI_API_KEY` (required), `GEMINI_MODEL` (default `gemini-2.0-flash`), `GEMINI_EMBED_MODEL` (default `gemini-embedding-001`).
- Methods: `embed_text`, `summarize`, `reason` (small classification/instructions).

### Embeddings & retrieval (brief)
- Store: `utils/embedding_store.py` using FAISS `IndexIDMap(IndexFlatIP)` with cosine similarity (via L2 normalization).
- Adds vectors with sidecar metadata `{ url, chunk }` persisted to `data/`.
- Query: normalize → search top-k → similarity threshold filter (≥ ~0.5) → de-dup and skip search-result URLs → highlights.

### Extension Logs
Text search - Physics

<img width="642" height="241" alt="image" src="https://github.com/user-attachments/assets/1f48f460-60be-496d-a6f2-11c3d58a2f7b" />


<img width="1265" height="434" alt="image" src="https://github.com/user-attachments/assets/edb18014-be3f-46eb-85fe-037ff698b3e8" />






