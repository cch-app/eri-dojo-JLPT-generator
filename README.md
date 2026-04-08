## JLPT Reflex Generator

Generate **original JLPT-style** practice questions (Reading/Listening, N5–N1), answer them one-by-one, then get a strengths/weaknesses summary at the end. The app loads **all questions in one LLM call**, then steps through them. UI is available in **English, Japanese, or Traditional Chinese** (default follows the browser language until you pick a language on the setup page). You can download the session **feedback as a PDF** (uses the bundled Noto Sans TC font for CJK text). Maximum **20** questions per session.

### Tech

- **Framework**: [Reflex](https://github.com/reflex-dev/reflex)
- **Env/deps**: `uv` (local `.venv`)
- **AI**: [Ollama](https://github.com/ollama/ollama-python) (local daemon or [Ollama Cloud](https://docs.ollama.com/cloud))
- **Deploy**: Vercel (static frontend) + separately hosted Reflex backend (required for websockets/state)

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
uv run reflex run
```

Open the app:
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`

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
- **API_URL**: Reflex backend URL (used for static export / self-hosting). Defaults to `http://localhost:8000`.

### Deploying on Vercel

Reflex uses a backend with websockets for interactivity. The recommended Vercel approach is:

1. **Host the Reflex backend** on a service that supports long-running processes + websockets (e.g. VM/container platform).
2. **Host the Reflex frontend build** on Vercel as static assets.

This follows Reflex’s self-hosting guidance (API URL must point to the backend): see [Reflex self-hosting docs](https://reflex.dev/docs/hosting/self-hosting/).

#### Backend (production)

On your backend host:

```bash
uv sync
uv run reflex run --env prod
```

#### Frontend (Vercel static export)

This repo includes a `vercel.json` + `scripts/vercel-build.sh` so Vercel can build the static site automatically.

In your Vercel Project Settings, set:

- **Build Command**: (leave default; the repo config handles it)
- **Output Directory**: (leave default; the repo config handles it)
- **Environment Variables**:
  - **API_URL**: The **public origin** of your reverse proxy / backend (must be an absolute URL)

Export frontend assets locally (optional) while pointing `API_URL` to your backend:

```bash
API_URL="https://YOUR_BACKEND_HOST:8000" uv run reflex export --frontend-only --no-zip
```

Deploy the generated static frontend from:

- `.web/build/client/`

### Containerization

This repo includes a `Dockerfile` and `docker-compose.yaml` for local validation and container-based hosting.

