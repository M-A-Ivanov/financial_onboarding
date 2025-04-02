"""
Configuration settings for the Financial Onboarding system.
This module loads settings from environment variables and provides defaults.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# LLM API settings
# I put this here to show how we can load and use API keys for other clients too (openai loads it automatically)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Processing settings
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.7))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 4096))

# Template generation settings
TEMPLATE_EXTRACTION_TEMPERATURE = float(os.getenv("TEMPLATE_EXTRACTION_TEMPERATURE", 0.2))
CONVERSATION_GENERATION_TEMPERATURE = float(os.getenv("CONVERSATION_GENERATION_TEMPERATURE", 0.8))
TRANSCRIPT_PROCESSING_TEMPERATURE = float(os.getenv("TRANSCRIPT_PROCESSING_TEMPERATURE", 0.2))
