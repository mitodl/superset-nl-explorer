# superset_config_custom.py
#
# Drop this file into your custom Superset image at:
#   /app/pythonpath/superset_config_docker.py
#
# It enables the NL Explorer extension and configures the LLM provider.

import os

# Enable the Superset extension system
FEATURE_FLAGS = {
    "ENABLE_EXTENSIONS": True,
}

# Point to the directory containing .supx extension files, OR
# use LOCAL_EXTENSIONS to point at an installed package.
#
# Option 1 — .supx file approach:
# EXTENSIONS_PATH = "/opt/superset/extensions"
#
# Option 2 — pip-installed package approach:
import nl_explorer
LOCAL_EXTENSIONS = [nl_explorer.extension_path()]

# NL Explorer LLM configuration.
# Set the LLM_API_KEY environment variable in your Docker run command
# or docker-compose.yml.
NL_EXPLORER_CONFIG = {
    # LiteLLM model string — examples:
    #   "gpt-4o"                          (OpenAI)
    #   "claude-3-5-sonnet-20241022"      (Anthropic)
    #   "ollama/llama3"                   (Ollama, set api_base below)
    #   "bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0"  (AWS Bedrock)
    "model": os.environ.get("NL_EXPLORER_MODEL", "gpt-4o"),

    # API key for the provider (not needed for Ollama)
    "api_key": os.environ.get("LLM_API_KEY"),

    # Optional: base URL for Ollama or other custom endpoints
    # "api_base": "http://ollama:11434",

    # Whether to use SSE streaming for chat responses
    "streaming": True,

    # Maximum number of datasets included in the LLM system prompt
    "max_datasets_in_context": 20,
}
