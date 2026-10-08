"""Application configuration and logging.

Documentation:
- os.getenv: https://docs.python.org/3/library/os.html#os.getenv
- python-dotenv load_dotenv: https://bbc2.github.io/python-dotenv/
- logging.basicConfig: https://docs.python.org/3/library/logging.html#logging.basicConfig

Why:
Environment/configuration concerns belong in one module so model selection and
logging policy are not scattered through the application.
"""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger("coder_agent")

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
MAX_RETRIES = 3
