"""Central settings for the agent team: model, Portkey routing, limits, paths."""

import json
import os
from pathlib import Path

from dotenv import dotenv_values

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# The one and only model used by every agent.
MODEL_NAME = "gpt-6-luna"

# --- Portkey gateway -------------------------------------------------------
PORTKEY_BASE_URL = "https://api.portkey.ai/v1"
PORTKEY_API_KEY_ENV = "PORTKEY_API_KEY"
# Optional routing values, read from env vars (names only appear in .env.example).
# Set whichever your Portkey workspace needs to reach the model.
PORTKEY_PROVIDER_ENV = "PORTKEY_PROVIDER"  # provider slug, e.g. an "@workspace-provider" slug
PORTKEY_VIRTUAL_KEY_ENV = "PORTKEY_VIRTUAL_KEY"
PORTKEY_CONFIG_ENV = "PORTKEY_CONFIG"

# --- Limits (every guard in one place) -------------------------------------
MAX_DELEGATION_DEPTH = 3  # Boss is depth 0
MAX_DELEGATIONS_PER_TICKET = 8
TICKET_REQUEST_LIMIT = 40  # model requests, all agents combined
TICKET_TOTAL_TOKENS_LIMIT = 200_000  # all agents combined
MAX_STEPS_PER_AGENT = 8  # model requests per single agent run
MAX_OUTPUT_TOKENS = 1_000  # per model response, keeps replies short

# --- API (FastAPI) ----------------------------------------------------------
# Local React dev servers only; no wildcard.
CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]
RUN_TIMEOUT_SECONDS = 300  # one ticket run may take at most this long
CASH_ACCOUNT_NAME = "checking"  # the account GET /cash reports
EVENTS_DEFAULT_LIMIT = 100
EVENTS_MAX_LIMIT = 500

# --- Paths ------------------------------------------------------------------
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
AUDIT_PATH_ENV = "CAMPUS_CUSTOMS_AUDIT_PATH"  # optional override for tests
DEFAULT_AUDIT_PATH = PROJECT_ROOT / "output" / "audit_trail.json"
MCP_CONFIG_PATH = PROJECT_ROOT / ".mcp.json"
MCP_SERVER_NAME = "campus-customs"
DB_PATH_ENV = "CAMPUS_CUSTOMS_DB_PATH"  # forwarded to the MCP server for tests


def load_env() -> None:
    """Load .env files into the environment without overriding values already set.

    Looks in the project folder, then up to two parent folders (the course root
    can hold a shared .env). Empty values are treated as unset. Nothing is printed.
    """
    for folder in [PROJECT_ROOT, *PROJECT_ROOT.parents[:2]]:
        for key, value in dotenv_values(folder / ".env").items():
            if value and not os.environ.get(key):
                os.environ[key] = value


def audit_path() -> Path:
    return Path(os.environ.get(AUDIT_PATH_ENV) or DEFAULT_AUDIT_PATH)


def mcp_command() -> tuple[str, list[str]]:
    """The MCP server command, read from .mcp.json so it matches the project MCP setup."""
    entry = json.loads(MCP_CONFIG_PATH.read_text())["mcpServers"][MCP_SERVER_NAME]
    command = entry["command"]
    if "/" in command and not Path(command).is_absolute():
        # Resolve from the project root, not the current directory. Not .resolve():
        # that would follow the venv symlink and lose the venv's packages.
        command = str(PROJECT_ROOT / command)
    return command, list(entry.get("args", []))


def mcp_env() -> dict[str, str]:
    """Env for the MCP server subprocess. Secrets are never forwarded."""
    env: dict[str, str] = {}
    if os.environ.get(DB_PATH_ENV):
        env[DB_PATH_ENV] = os.environ[DB_PATH_ENV]
    return env


def portkey_headers() -> dict[str, str]:
    """Portkey gateway headers. Raises if the API key is missing."""
    load_env()
    key = os.environ.get(PORTKEY_API_KEY_ENV)
    if not key:
        raise RuntimeError(f"{PORTKEY_API_KEY_ENV} is not set (put it in .env).")
    headers = {"x-portkey-api-key": key}
    for env_name, header in (
        (PORTKEY_PROVIDER_ENV, "x-portkey-provider"),
        (PORTKEY_VIRTUAL_KEY_ENV, "x-portkey-virtual-key"),
        (PORTKEY_CONFIG_ENV, "x-portkey-config"),
    ):
        if os.environ.get(env_name):
            headers[header] = os.environ[env_name]
    return headers


def build_model():
    """Create the Portkey-routed model used by every agent."""
    from openai import AsyncOpenAI
    from pydantic_ai.models.openai import OpenAIChatModel
    from pydantic_ai.providers.openai import OpenAIProvider

    headers = portkey_headers()
    client = AsyncOpenAI(
        base_url=PORTKEY_BASE_URL,
        api_key=headers["x-portkey-api-key"],
        default_headers=headers,
    )
    return OpenAIChatModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))
