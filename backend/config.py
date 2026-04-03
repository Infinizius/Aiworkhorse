import os
import logging

logger = logging.getLogger("ai_workhorse_config")

# Basic Settings
API_KEY = os.getenv("API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")
WEBUI_API_KEY = os.getenv("WEBUI_API_KEY", "")
WEBUI_INTERNAL_URL = os.getenv("WEBUI_INTERNAL_URL", "http://ai-workhorse-webui:8080")
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
CORS_ALLOW_ORIGINS = os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3002,http://localhost:3001").split(",")

# Database settings
POSTGRES_USER = os.getenv("POSTGRES_USER", "workhorse")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "workhorse_secure_pw")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "db")
POSTGRES_DB = os.getenv("POSTGRES_DB", "workhorse_db")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:5432/{POSTGRES_DB}",
)

# Limits
REACTIVE_MAX_ITERATIONS = int(os.getenv("REACTIVE_MAX_ITERATIONS", "3"))
GOAL_MAX_ITERATIONS = int(os.getenv("GOAL_MAX_ITERATIONS", "10"))

# Validation
def validate_config():
    """
    Validates the configuration at startup.
    Raises RuntimeError if mandatory variables are missing or insecure in production.
    """
    critical_missing = []
    
    if not GEMINI_API_KEY:
        critical_missing.append("GEMINI_API_KEY")
    
    # Fail-Fast on missing Encryption Key for Phase 2
    if not ENCRYPTION_KEY:
        critical_missing.append("ENCRYPTION_KEY")
    elif ENCRYPTION_KEY in (
        "CHANGE_ME_STRONG_ENCRYPTION_KEY",
        # BUG-11 fix: also block the example value shipped in .env.example
        # to prevent users who copy the file verbatim from running with a
        # publicly known encryption key.
        "f6-9E_zX_K-mX-Z-H-W-Y-G-m-X-Z-H-W-Y-G-m-X-Z-H-W-Y-G",
    ):
        logger.error("ENCRYPTION_KEY is the insecure default. Please change it.")
        critical_missing.append("ENCRYPTION_KEY (insecure default)")

    if critical_missing:
        msg = f"Critical environment variables missing: {', '.join(critical_missing)}. Please set them in your .env file."
        logger.critical(msg)
        raise RuntimeError(msg)

    if not API_KEY:
        logger.warning(
            "API_KEY is not set – authentication is DISABLED. Set API_KEY for production security."
        )

    logger.info("Configuration validated successfully.")
