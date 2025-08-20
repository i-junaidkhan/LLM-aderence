#!/usr/bin/env python3
"""
EXPERIMENT 3: CONTRADICTION RESOLUTION
"""
import random
import re
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
CONTRADICTION = (
    "Write the story only in the past tense.",
    "Write the story only in the future tense."
)
CSV_PATH = Path("outputs/experiment_3_contradictions.csv")

def build_prompt(rules: List[str], contradiction: tuple) -> str:
    """Builds prompt with contradictory rules."""
    header = "Create a short story subject to the following rules:\n"
    volatile = "Memorize these rules. Review requirements before writing. Keep in mind throughout.\n\n"
    lexical_body = "\n".join(f"- Include the word '{word}'" for word in rules)
    contradiction_body = f"- {contradiction[0]}\n- {contradiction[1]}"
    return f"{header}{volatile}{lexical_body}\n{contradiction_body}"

def analyze_tense_resolution(story: str) -> Dict[str, Any]:
    """Analyzes tense usage to determine contradiction resolution strategy."""
    story_lower = story.lower()
    past_indicators = ["was", "were", "had", "did", "went", "saw", "thought", "said"]
    future_indicators = ["will", "shall", "going to", "would be"]
    
    past_count = sum(story_lower.count(word) for word in past_indicators)
    future_count = sum(story_lower.count(word) for word in future_indicators)
    
    total_tense_indicators = past_count + future_count
    if total_tense_indicators == 0:
        return {"resolution": "no_clear_tense", "past_count": 0, "future_count": 0}

    past_ratio = past_count / total_tense_indicators
    
    if past_ratio > 0.8:
        resolution = "followed_past_tense"
    elif past_ratio < 0.2:
        resolution = "followed_future_tense"
    else:
        resolution = "mixed_or_ignored"
        
    return {"resolution": resolution, "past_count": past_count, "future_count": future_count}

def run_experiment() -> None:
    """Runs contradiction resolution experiment across models."""
    lexicon = load_lexicon(Path("/usr/share/dict/words"), LEXICON_LIMIT)
    
    for model in MODEL_CANDIDATES:
        experiment_name = f"contradiction_tense_R{R}"
        logger.info(f"=== Starting {experiment_name} with model: {model} ===")
        
        for trial in range(1, TRIALS + 1):
            rules = random.sample(lexicon, R)
            prompt = build_prompt(rules, CONTRADICTION)
            story = call_ollama_with_retries(prompt, model)
            
            artifact_name = f"{experiment_name}_{model.replace(':', '_')}"
            save_experiment_artifacts(
                artifact_name, trial, prompt, story, trial == 1
            )
            
            lexical_result = check_lexical_adherence(story, rules)
            tense_analysis = analyze_tense_resolution(story)
            
            result = {
                **lexical_result,
                "R": R + 2,
                "prompt_len": len(prompt),
                "details": (
                    f"Tense resolution: {tense_analysis['resolution']}; "
                    f"Past: {tense_analysis['past_count']}, Future: {tense_analysis['future_count']}"
                )
            }
            
            write_results_to_csv(CSV_PATH, experiment_name, trial, model, result)
            logger.info(
                "Model %s | Trial %d: Lexical adherence: %.1f%%, Tense: %s",
                model, trial, lexical_result["adherence"] * 100, tense_analysis["resolution"]
            )

if __name__ == "__main__":
    run_experiment()