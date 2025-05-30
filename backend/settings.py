import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env file
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-change-me-in-production")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", "True").lower() == "true"

ALLOWED_HOSTS = ["*"]

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 'django_rq',  # Temporarily disabled until we can rebuild with this dependency
    "app",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# Database configuration for PostgreSQL
# Use SQLite in-memory for tests
if 'test' in sys.argv or 'pytest' in sys.modules:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("DB_NAME", "content_management"),
            "USER": os.environ.get("DB_USER", "postgres"),
            "PASSWORD": os.environ.get("DB_PASSWORD", "postgres"),
            "HOST": os.environ.get("DB_HOST", "localhost"),
            "PORT": os.environ.get("DB_PORT", "5432"),
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://frontend:3000",
]

CORS_ALLOW_ALL_ORIGINS = DEBUG

# Model Configuration - Specify which models to use for different tasks
"""
Model Selection Strategy:
- gpt-4o-mini: Fast, cost-effective for simple structured tasks (key concepts, difficulty)
- gpt-4o: Advanced reasoning for complex tasks (study time estimation, conversations)
- gpt-3.5-turbo: Reliable fallback for keyword extraction

Temperature Settings:
- 0: Deterministic outputs for analysis tasks
- 0.7: Conversational model for more natural responses

Token Limits:
- Analysis tasks: 50-150 tokens (concise outputs)
- Study time: 100 tokens (needs reasoning explanation)
- Conversations: 2000 tokens (extended dialogue)
"""

# Analysis Models - for content analysis tasks
ANALYSIS_KEY_CONCEPTS_MODEL = os.getenv("ANALYSIS_KEY_CONCEPTS_MODEL", "gpt-4o-mini")
ANALYSIS_KEY_CONCEPTS_TEMPERATURE = float(os.getenv("ANALYSIS_KEY_CONCEPTS_TEMPERATURE", "0"))
ANALYSIS_KEY_CONCEPTS_MAX_TOKENS = int(os.getenv("ANALYSIS_KEY_CONCEPTS_MAX_TOKENS", "150"))

ANALYSIS_DIFFICULTY_MODEL = os.getenv("ANALYSIS_DIFFICULTY_MODEL", "gpt-4o-mini")
ANALYSIS_DIFFICULTY_TEMPERATURE = float(os.getenv("ANALYSIS_DIFFICULTY_TEMPERATURE", "0"))
ANALYSIS_DIFFICULTY_MAX_TOKENS = int(os.getenv("ANALYSIS_DIFFICULTY_MAX_TOKENS", "50"))

# Study time estimation benefits from more reasoning capability
ANALYSIS_STUDY_TIME_MODEL = os.getenv("ANALYSIS_STUDY_TIME_MODEL", "gpt-4o")
ANALYSIS_STUDY_TIME_TEMPERATURE = float(os.getenv("ANALYSIS_STUDY_TIME_TEMPERATURE", "0"))
ANALYSIS_STUDY_TIME_MAX_TOKENS = int(os.getenv("ANALYSIS_STUDY_TIME_MAX_TOKENS", "100"))

# Search Models - for query processing
# Keyword extraction using reliable model
SEARCH_KEYWORD_EXTRACTION_MODEL = os.getenv("SEARCH_KEYWORD_EXTRACTION_MODEL", "gpt-3.5-turbo")
SEARCH_KEYWORD_EXTRACTION_TEMPERATURE = float(os.getenv("SEARCH_KEYWORD_EXTRACTION_TEMPERATURE", "0"))
SEARCH_KEYWORD_EXTRACTION_MAX_TOKENS = int(os.getenv("SEARCH_KEYWORD_EXTRACTION_MAX_TOKENS", "100"))

# Conversation Models - for chat interactions
# Use GPT-4o for better conversational abilities and context understanding
CONVERSATION_ASSISTANT_MODEL = os.getenv("CONVERSATION_ASSISTANT_MODEL", "gpt-4o")
CONVERSATION_ASSISTANT_TEMPERATURE = float(os.getenv("CONVERSATION_ASSISTANT_TEMPERATURE", "0.7"))
CONVERSATION_ASSISTANT_MAX_TOKENS = int(os.getenv("CONVERSATION_ASSISTANT_MAX_TOKENS", "2000"))

# Embedding Models - for vector search
EMBEDDING_MODEL_TYPE = os.getenv("EMBEDDING_MODEL_TYPE", "openai")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
SENTENCE_TRANSFORMER_MODEL = os.getenv("SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2")

# Django-RQ configuration - using queue manager for actual queue instances
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
RQ_QUEUES = {
    "default": {
        "URL": redis_url,
        "DEFAULT_TIMEOUT": "10m",
        "CONNECTION_CLASS": "redis.Redis",
        "CONNECTION_KWARGS": {
            "health_check_interval": 30,
        },
    },
    "high": {
        "URL": redis_url,
        "DEFAULT_TIMEOUT": "5m",
    },
    "low": {
        "URL": redis_url,
        "DEFAULT_TIMEOUT": "30m",
    },
}

# Configure Django cache for debug info storage
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": redis_url,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

# Analysis prompts
KEY_CONCEPTS_PROMPT = """Analyze the following educational content and extract the key concepts. 
Identify the main concepts, maximum 5 concepts.
Content:\n {content}"""

DIFFICULTY_PROMPT = """Analyze the following educational content and determine its difficulty level.
Choose one of these levels: beginner, intermediate, advanced, expert
Content:\n {content}"""

STUDY_TIME_PROMPT = """Estimate the study time in minutes for the following educational content based on these features:

Content Features:
- Key Concepts: {key_concepts}
- Difficulty Level: {difficulty_level}
- Token Count: {token_count}
- Content Length: {content_length} characters
- Number of Concepts: {num_concepts}

Content Preview:
{content_preview}

Consider these factors:
- More concepts generally require more time
- Higher difficulty levels need more time per concept
- Token density affects reading comprehension time
- Base reading time: ~200 words per minute for beginners, ~300 for intermediate, ~400 for advanced/expert

Provide a realistic estimate in minutes (1-300 range)."""

SYSTEM_PROMPT = """
You are an educational content analyzer. Provide concise, accurate analysis.
"""

# JSON Schemas for structured outputs
KEY_CONCEPTS_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "key_concepts_response",
        "schema": {
            "type": "object",
            "properties": {
                "concepts": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 5,
                    "description": "Array of key concepts from the content",
                }
            },
            "required": ["concepts"],
            "additionalProperties": False,
        },
        "strict": True,
    },
}

DIFFICULTY_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "difficulty_response",
        "schema": {
            "type": "object",
            "properties": {
                "difficulty_level": {
                    "type": "string",
                    "enum": ["beginner", "intermediate", "advanced", "expert"],
                    "description": "The difficulty level of the content",
                }
            },
            "required": ["difficulty_level"],
            "additionalProperties": False,
        },
        "strict": True,
    },
}

STUDY_TIME_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "study_time_response",
        "schema": {
            "type": "object",
            "properties": {
                "estimated_minutes": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 300,
                    "description": "Estimated study time in minutes",
                }
            },
            "required": ["estimated_minutes"],
            "additionalProperties": False,
        },
        "strict": True,
    },
}
