import reflex as rx
import os

# Determine the api_url based on the deployment environment.
# - Hugging Face Spaces (single-port mode): api_url uses localhost placeholder at build time;
#   at runtime the browser talks to the same origin so the value doesn't matter.
# - Reflex Cloud: Set explicitly via API_URL env var.
# - Local dev: defaults to localhost:8000.

api_url = os.environ.get("API_URL")  # Explicit override always wins

# For Hugging Face Spaces with --single-port, detect via SPACE_ID env var (set by HF at runtime).
is_hf_space = bool(os.environ.get("SPACE_ID"))

# Reflex Cloud production fallback
if not api_url and not is_hf_space and os.getenv("REFLEX_ENV") == "prod":
    api_url = "https://neuralcompile-lime-sun.reflex.run"

# IMPORTANT: api_url must NEVER be None — Reflex 0.8.x crashes during `reflex export`
# if api_url is None (TypeError: sequence item 0: expected str instance, NoneType found).
# When running on HF Spaces in single-port mode, this value is overridden at runtime
# and the browser connects to the same origin anyway, so the placeholder is harmless.
if not api_url:
    api_url = "http://localhost:8000"

config = rx.Config(
    app_name="NeuralCompile",
    api_url=api_url,
    cors_allowed_origins=["*"],
    plugins=[
        rx.plugins.SitemapPlugin(),
    ],
)