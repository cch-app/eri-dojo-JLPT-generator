## JLPT Flask Generator

Generate **original JLPT-style** practice questions (Reading/Listening, N5–N1), answer them one-by-one, then get a strengths/weaknesses summary at the end. The app loads **all questions in one LLM call**, then steps through them. UI is available in **English, Japanese, or Traditional Chinese** (default follows the browser language until you pick a language on the setup page). You can download the session **feedback as a PDF** (uses the bundled Noto Sans TC font for CJK text). Maximum **20** questions per session.

### Tech

- **Framework**: Flask (server-rendered HTML)
- **Env/deps**: `uv` (local `.venv`)
- **AI**: [Ollama](https://github.com/ollama/ollama-python) (local daemon or [Ollama Cloud](https://docs.ollama.com/cloud))
- **Deploy**: Vercel (Python runtime) or Docker

### Local development

1. Create the local environment and install deps:

```bash
uv sync
```

2. Set Ollama env vars.

**Local Ollama** (default host `http://localhost:11434`):

```bash
export OLLAMA_MODEL="llama3.1"
```

**Ollama Cloud** ([docs](https://docs.ollama.com/cloud#python)):

```bash
export OLLAMA_HOST="https://ollama.com"
export OLLAMA_API_KEY="..."  # from https://ollama.com/settings/keys
export OLLAMA_MODEL="gpt-oss:120b"
```

3. Run the app:

```bash
make dev
```

Open the app:
- `http://localhost:8000`

### Running tests

```bash
uv run pytest
```

### Formatting

```bash
uv run isort .
uv run black .
```

### Environment variables

- **OLLAMA_MODEL**: Model name (required), e.g. `llama3.1` locally or a cloud model from [Ollama Cloud](https://docs.ollama.com/cloud).
- **OLLAMA_HOST**: Ollama API base (default `http://localhost:11434`). Use `https://ollama.com` for direct cloud API access.
- **OLLAMA_API_KEY**: Required when **OLLAMA_HOST** points at Ollama Cloud (`ollama.com`). Optional for a typical local daemon.
- **SECRET_KEY**: Optional but recommended. Used to sign the stateless session token passed between pages. Set a long random value in production.

### Deploying on Vercel

This project deploys as a single Flask app via Vercel’s Python runtime.

- **Entrypoint**: `api/wsgi.py` (exports `app`)
- **Recommended env vars**:
  - `OLLAMA_MODEL` (required)
  - `OLLAMA_HOST` / `OLLAMA_API_KEY` (as needed)
  - `SECRET_KEY` (recommended)

### Containerization

This repo includes a `Dockerfile` and `docker-compose.yaml` for local validation and container-based hosting.

