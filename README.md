# superset-nl-explorer

A natural language LLM interface for [Apache Superset](https://superset.apache.org/), packaged as a deployable extension plugin.

Users can type natural language queries in an embedded chat panel to explore data, preview charts, and create dashboards — without writing SQL or touching the chart builder.

---

## Features

- 💬 **Embedded chat UI** — dedicated "Ask Data" page + floating panel in Explore and Dashboard views
- 🤖 **Provider-agnostic LLM** — powered by [LiteLLM](https://github.com/BerriAI/litellm), supports OpenAI, Anthropic Claude, Ollama, AWS Bedrock, and more
- 📊 **Chart & dashboard creation** — LLM can preview charts (Explore links), save charts, and build dashboards
- 🔒 **Superset-native security** — all endpoints require Superset authentication; SQL execution and chart creation respect existing dataset/database permissions
- 📦 **Plugin architecture** — no core Superset modifications required; deployed as a `.supx` extension or pip package

---

## Quickstart

### 1. Build and install

```bash
# Install uv (if not already)
curl -Lsf https://astral.sh/uv/install.sh | sh

# Clone and set up the dev environment
git clone <repo-url> superset_llm_explorer
cd superset_llm_explorer
uv sync --group dev

# Build the Python wheel
uv build
```

### 2. Add to your custom Superset image

```dockerfile
FROM apache/superset:5.0.0
COPY dist/*.whl /tmp/
RUN pip install /tmp/*.whl
COPY superset_config_custom.py /app/pythonpath/superset_config_docker.py
```

### 3. Configure the LLM

Edit `superset_config_custom.py` (or set environment variables):

```python
NL_EXPLORER_CONFIG = {
    "model": "gpt-4o",                    # LiteLLM model string
    "api_key": os.environ["LLM_API_KEY"], # Provider API key
    "streaming": True,
}
```

### 4. Enable the extension

```python
FEATURE_FLAGS = {"ENABLE_EXTENSIONS": True}

import nl_explorer
LOCAL_EXTENSIONS = [nl_explorer.extension_path()]
```

---

## Configuration Reference

All settings go in `superset_config.py` under the `NL_EXPLORER_CONFIG` dict.

| Key | Default | Description |
|-----|---------|-------------|
| `model` | `"gpt-4o"` | LiteLLM model string (see examples below) |
| `api_key` | `None` | LLM provider API key |
| `api_base` | `None` | Custom base URL (for Ollama, vLLM, etc.) |
| `streaming` | `True` | Enable SSE streaming responses |
| `max_tokens` | `4096` | Max tokens per LLM response |
| `max_datasets_in_context` | `20` | Max datasets included in system prompt |

### LiteLLM model examples

| Provider | Model string |
|----------|-------------|
| OpenAI | `"gpt-4o"`, `"gpt-4.1"` |
| Anthropic | `"claude-3-5-sonnet-20241022"` |
| Ollama (local) | `"ollama/llama3"` + `api_base="http://ollama:11434"` |
| AWS Bedrock | `"bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0"` |
| Azure OpenAI | `"azure/<deployment>"` + `api_base`, `api_key` |

---

## API Endpoints

All endpoints live under `/api/v1/extensions/nl_explorer/` and require Superset authentication.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/context` | List datasets available to the current user |
| `POST` | `/chat` | Send a message, receive LLM response + actions |
| `POST` | `/chat` (stream=true) | SSE streaming chat |
| `POST` | `/execute` | Execute a structured action (create chart, etc.) |
| `GET` | `/config` | Non-sensitive plugin configuration |

---

## Development

```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=nl_explorer tests/

# Build frontend
cd frontend && npm install && npm run build

# Build the wheel
uv build
```

---

## Architecture

```
Chat UI (React)
    │
    ▼
POST /api/v1/extensions/nl_explorer/chat
    │
    ▼
NLExplorerRestApi.chat()
    ├── context_builder.get_user_context()  ← Superset DatasetDAO
    ├── prompts/system.py                   ← Build system prompt
    └── llm_service.chat()                  ← LiteLLM call
            │
            ▼ (tool calls)
    llm_service.dispatch_tool_call()
            ├── context_builder             ← list/describe datasets
            ├── chart_creator.preview_chart ← Explore URL
            ├── chart_creator.create_chart  ← Superset CreateChartCommand
            └── chart_creator.create_dashboard
```

---

## License

MIT
