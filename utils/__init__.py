import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
RESULTS_DIR = os.path.join(BASE_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)
TEMPLATE_FILENAME = "template.json"
TEMPLATE_FILENAME_ABR = "template_short.json"
SCHEMA_FILENAME = "schema_short.json"

MISSING_FIELD = "MISSING INFORMATION"
TEMPERATURE = 0.9
OBFUSCATION_RATE = 10
