#!/usr/bin/env python3
"""
EXPERIMENT 4: PROGRESSIVE COMPLEXITY LADDER
"""
import random
from pathlib import Path
from typing import List, Dict, Any

from utils import (
    load_lexicon, call_ollama_with_retries, check_lexical_adherence,
    save_experiment_artifacts, write_results_to_csv, MODEL_CANDIDATES, logger
)

# --- Configuration ---
TRIALS = 3
LEXICON_LIMIT = 2000
R = 20
CSV_PATH = Path("outputs/experiment_4_complexity.csv")

COMPLEXITY_LEVELS = [
    {"name": "L1_Lexical", "rules": []},
    {"name": "L2_Tense", "rules": ["Write in the past tense."]},
    {"name": "L3_Structure", "rules": [
        "Write in the past tense.",
        "The story must have exactly 3 paragraphs."
    ]},
    {"name": "L4_Hierarchy", "rules": [
        "Write in the past tense.",
        "The story must have exactly 3 paragraphs.",
        "The word 'apple' must appear in the first paragraph."
    ]}
]

def build_prompt(rules: List[str], complexity_rules: List[str]) -> str:
    """Builds prompt with progressive complexity rules."""
    header = "Create a short story subject to the following rules:\n"
    volatile = "Memorize these rules. Review requirements before writing. Keep in mind throughout.\n\n"
    lexical_body = "\n".join(f"- Include the word '{word}'" for word in rules)
    complexity_body = "\n".join(f"- {rule}" for rule in complexity_rules)
    return f"{header}{volatile}{lexical_body}\n{complexity_body}"

def run_experiment() -> None:
    """Runs progressive complexity experiment across models."""
    lexicon = load_lexicon(Path("/usr/share/dict/words"), LEXICON_LIMIT)
    
    for model in MODEL_CANDIDATES:
        for level in COMPLEXITY_LEVELS:
            experiment_name = f"complexity_{level['name']}_R{R}"
            logger.info(f"=== Starting {experiment_name} with model: {model} ===")
            
            for trial in range(1, TRIALS + 1):
                rules = random.sample(lexicon, R)
                # Ensure 'apple' is in the list for L4 to avoid making the task impossible
                if "Hierarchy" in level['name'] and 'apple' not in rules:
                    rules[0] = 'apple'
                
                prompt = build_prompt(rules, level["rules"])
                story = call_ollama_with_retries(prompt, model)
                
                artifact_name = f"{experiment_name}_{model.replace(':', '_')}"
                save_experiment_artifacts(
                    artifact_name, trial, prompt, story, trial == 1
                )
                
                lexical_result = check_lexical_adherence(story, rules)
                
                details = f"Complexity: {level['name']}"
                
                result = {
                    **lexical_result,
                    "R": R,
                    "prompt_len": len(prompt),
                    "details": details
                }
                
                write_results_to_csv(CSV_PATH, experiment_name, trial, model, result)
                logger.info(
                    "Model %s | Trial %d: Adherence: %.1f%% (%s)",
                    model, trial, lexical_result["adherence"] * 100, details
                )

if __name__ == "__main__":
    run_experiment()