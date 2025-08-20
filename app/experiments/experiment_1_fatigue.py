#!/usr/bin/env python3
"""
EXPERIMENT 1: SCALED RULE FATIGUE
"""
import random
from pathlib import Path
from typing import List

from utils import (
    load_lexicon, call_ollama_with_retries, check_lexical_adherence,
    save_experiment_artifacts, write_results_to_csv, MODEL_CANDIDATES, logger
)

# --- Configuration ---
TRIALS = 3
LEXICON_LIMIT = 2000
RULE_COUNTS = [5, 20, 50, 100]
CSV_PATH = Path("outputs/experiment_1_fatigue.csv")

def build_prompt(rules: List[str]) -> str:
    """Builds prompt for rule fatigue experiment with volatile components."""
    header = "Create a short story subject to the following rules:\n"
    volatile = "Memorize these rules. Review requirements before writing. Keep in mind throughout.\n\n"
    body = "\n".join(f"- Include the word '{word}'" for word in rules)
    return f"{header}{volatile}{body}\n"

def run_experiment() -> None:
    """Runs the rule fatigue experiment across defined rule counts and models."""
    lexicon = load_lexicon(Path("/usr/share/dict/words"), LEXICON_LIMIT)
    
    for model in MODEL_CANDIDATES:
        for R in RULE_COUNTS:
            experiment_name = f"fatigue_R{R}"
            logger.info(f"=== Starting {experiment_name} with model: {model} ===")
            
            for trial in range(1, TRIALS + 1):
                rules = random.sample(lexicon, R)
                prompt = build_prompt(rules)
                story = call_ollama_with_retries(prompt, model)
                
                artifact_name = f"{experiment_name}_{model.replace(':', '_')}"
                save_experiment_artifacts(
                    artifact_name, trial, prompt, story, trial == 1
                )
                
                result = check_lexical_adherence(story, rules)
                result.update({
                    "R": R,
                    "prompt_len": len(prompt),
                    "details": "Volatile components active"
                })
                
                write_results_to_csv(CSV_PATH, experiment_name, trial, model, result)
                logger.info(
                    "Model %s | Trial %d: %d/%d rules followed (%.1f%%)",
                    model, trial, result["passed_count"], R, result["adherence"] * 100
                )

if __name__ == "__main__":
    run_experiment()