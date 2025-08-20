#!/usr/bin/env python3
"""
Shared utilities for all experiments.
"""

import csv
import logging
import random
import time
from pathlib import Path
from typing import List, Dict, Any

import ollama

# --- Configuration ---
LEXICON_PATH = Path("/usr/share/dict/words")
LEXICON_LIMIT = 2000
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

MODEL_CANDIDATES = [
    "phi3:3.8b",
    "llama3.2:3b",
    "gemma2:2b",
    "qwen2:1.5b",
    "mistral:7b",
]

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# --- Ollama Client ---
client = ollama.Client(host='http://ollama:11434')

def load_lexicon(path: Path, limit: int) -> List[str]:
    """Loads a word list for rule sampling with fallback."""
    if not path.exists():
        logger.warning(f"Lexicon path {path} not found. Using default words.")
        default_words = ["apple", "river", "mountain", "journey", "discovery",
                         "whisper", "shadow", "sunlight", "memory", "horizon"]
        return (default_words * (limit // len(default_words) + 1))[:limit]
    
    words = []
    with path.open() as f:
        for line in f:
            word = line.strip().lower()
            if word.isalpha():
                words.append(word)
            if len(words) >= limit:
                break
    logger.info("Loaded %d words from lexicon", len(words))
    return words

def call_ollama_with_retries(
    prompt: str,
    model: str,
    max_retries: int = 3,
    timeout: float = 60.0 # Increased timeout for larger models
) -> str:
    """Robust LLM call with exponential backoff."""
    for attempt in range(max_retries):
        try:
            response = client.chat(
                model=model,
                messages=[{'role': 'user', 'content': prompt}],
                options={"temperature": 0.7} # Added for creativity in stories
            )
            return response['message']['content']
        except Exception as e:
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                logger.warning(
                    "Attempt %d/%d for model %s failed: %s. Retrying in %ds...",
                    attempt + 1, max_retries, model, str(e), wait
                )
                time.sleep(wait)
            else:
                logger.error("Model %s failed after %d attempts: %s", model, max_retries, str(e))
                return f"ERROR: Failed to generate response after {max_retries} attempts"

def check_lexical_adherence(story_text: str, rules: List[str]) -> Dict[str, Any]:
    """Checks lexical rule adherence with detailed metrics."""
    lower_story = story_text.lower()
    passed = [word for word in rules if word.lower() in lower_story]
    failed = [word for word in rules if word.lower() not in lower_story]
    
    return {
        "passed_count": len(passed),
        "failed_count": len(failed),
        "passed_words": passed,
        "failed_words": failed,
        "adherence": len(passed) / len(rules) if rules else 1.0
    }

def save_experiment_artifacts(
    experiment_name: str,
    trial: int,
    prompt: str,
    story: str,
    is_first_trial: bool = False
) -> None:
    """Saves prompt and story for analysis, only for first trial."""
    if not is_first_trial:
        return
        
    (OUTPUT_DIR / f"{experiment_name}_prompt.txt").write_text(
        prompt, encoding="utf-8"
    )
    (OUTPUT_DIR / f"{experiment_name}_story.txt").write_text(
        story, encoding="utf-8"
    )
    logger.info("Saved artifacts for %s (trial %d)", experiment_name, trial)

def write_results_to_csv(
    csv_path: Path,
    experiment_name: str,
    trial: int,
    model_name: str,
    result_data: Dict[str, Any]
) -> None:
    """Writes experiment results to CSV in standardized format."""
    fieldnames = [
        "experiment_name", "trial", "model", "R", "passed", "failed",
        "adherence", "prompt_len", "details"
    ]
    
    file_exists = csv_path.exists()
    
    with csv_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
            
        writer.writerow({
            "experiment_name": experiment_name,
            "trial": trial,
            "model": model_name,
            "R": result_data.get("R", 0),
            "passed": result_data.get("passed_count", 0),
            "failed": result_data.get("failed_count", 0),
            "adherence": result_data.get("adherence", 0.0),
            "prompt_len": result_data.get("prompt_len", 0),
            "details": result_data.get("details", "")
        })