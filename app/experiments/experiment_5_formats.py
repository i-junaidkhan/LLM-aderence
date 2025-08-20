#!/usr/bin/env python3
"""
EXPERIMENT 5: PRESENTATION FORMAT EFFECTS
"""
import random
import json
from pathlib import Path
from typing import List

from utils import (
    load_lexicon, call_ollama_with_retries, check_lexical_adherence,
    save_experiment_artifacts, write_results_to_csv, MODEL_CANDIDATES, logger
)

# --- Configuration ---
TRIALS = 3
LEXICON_LIMIT = 2000
R = 50
FORMATS = [
    {"name": "numbered", "description": "Standard numbered list"},
    {"name": "bullet", "description": "Bullet point format"},
    {"name": "json", "description": "JSON structured rules"},
    {"name": "paragraph", "description": "Paragraph prose format"}
]
CSV_PATH = Path("outputs/experiment_5_formats.csv")

def build_prompt(rules: List[str], format_type: str) -> str:
    """Builds prompt with rules in specified format."""
    header = "Create a short story with the following requirements:\n"
    volatile = "Memorize these rules. Review requirements before writing. Keep in mind throughout.\n\n"
    
    if format_type == "numbered":
        body = "\n".join(f"{i+1}. Include the word '{word}'" for i, word in enumerate(rules))
    elif format_type == "bullet":
        body = "\n".join(f"- Include the word '{word}'" for word in rules)
    elif format_type == "json":
        body = f"Please adhere to the constraints provided in the following JSON object:\n"
        body += json.dumps({"task": "write a story", "required_words": rules}, indent=2)
    elif format_type == "paragraph":
        body = f"Your story must include all of the following words: {', '.join(rules)}. " \
               "Please ensure every single word from this list appears naturally in your narrative."
    
    return f"{header}{volatile}{body}"

def run_experiment() -> None:
    """Runs presentation format experiment across models."""
    lexicon = load_lexicon(Path("/usr/share/dict/words"), LEXICON_LIMIT)
    
    for model in MODEL_CANDIDATES:
        for fmt in FORMATS:
            experiment_name = f"format_{fmt['name']}_R{R}"
            logger.info(f"=== Starting {experiment_name} with model: {model} ===")
            
            for trial in range(1, TRIALS + 1):
                rules = random.sample(lexicon, R)
                prompt = build_prompt(rules, fmt["name"])
                story = call_ollama_with_retries(prompt, model)
                
                artifact_name = f"{experiment_name}_{model.replace(':', '_')}"
                save_experiment_artifacts(
                    artifact_name, trial, prompt, story, trial == 1
                )
                
                result = check_lexical_adherence(story, rules)
                result.update({
                    "R": R,
                    "prompt_len": len(prompt),
                    "details": f"Format: {fmt['description']}"
                })
                
                write_results_to_csv(CSV_PATH, experiment_name, trial, model, result)
                logger.info(
                    "Model %s | Trial %d: %d/%d rules followed (%.1f%%) [Format: %s]",
                    model, trial, result["passed_count"], R, result["adherence"] * 100, fmt["name"]
                )

if __name__ == "__main__":
    run_experiment()