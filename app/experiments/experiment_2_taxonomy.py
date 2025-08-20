#!/usr/bin/env python3
"""
EXPERIMENT 2: CONSTRAINT TYPE TAXONOMY
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
CSV_PATH = Path("outputs/experiment_2_taxonomy.csv")

def build_prompt(rules: List[str], constraint_type: str) -> str:
    """Builds prompt with appropriate constraint type."""
    header = "Create a short story subject to the following rules:\n"
    volatile = "Memorize these rules. Review requirements before writing. Keep in mind throughout.\n\n"
    lexical_body = "\n".join(f"- Include the word '{word}'" for word in rules)
    
    if constraint_type == "structural":
        structural_rules = [
            "Write exactly 3 paragraphs.",
            "Every sentence must have 15 words or fewer."
        ]
        extra_body = "\n".join(f"- {rule}" for rule in structural_rules)
        return f"{header}{volatile}{lexical_body}\n{extra_body}"
    
    return f"{header}{volatile}{lexical_body}"

def verify_structural_rules(story: str) -> Dict[str, Any]:
    """Checks adherence to structural constraints."""
    results = {"paragraph_count": 0, "long_sentences": 0, "structural_adherence": 0.0}
    paragraphs = [p.strip() for p in story.split('\n\n') if p.strip()]
    results["paragraph_count"] = len(paragraphs)
    
    long_sentences = 0
    for para in paragraphs:
        sentences = [s.strip() for s in para.split('.') if s.strip()]
        for sent in sentences:
            if len(sent.split()) > 15:
                long_sentences += 1
    results["long_sentences"] = long_sentences
    
    para_ok = 1.0 if results["paragraph_count"] == 3 else 0.0
    sentence_ok = 1.0 if long_sentences == 0 else 0.0
    results["structural_adherence"] = (para_ok + sentence_ok) / 2
    return results

def run_experiment() -> None:
    """Runs comparison between lexical and structural constraints across models."""
    lexicon = load_lexicon(Path("/usr/share/dict/words"), LEXICON_LIMIT)
    
    for model in MODEL_CANDIDATES:
        for constraint_type in ["lexical", "structural"]:
            experiment_name = f"taxonomy_{constraint_type}_R{R}"
            logger.info(f"=== Starting {experiment_name} with model: {model} ===")
            
            for trial in range(1, TRIALS + 1):
                rules = random.sample(lexicon, R)
                prompt = build_prompt(rules, constraint_type)
                story = call_ollama_with_retries(prompt, model)
                
                artifact_name = f"{experiment_name}_{model.replace(':', '_')}"
                save_experiment_artifacts(
                    artifact_name, trial, prompt, story, trial == 1
                )
                
                lexical_result = check_lexical_adherence(story, rules)
                structural_details = ""
                if constraint_type == "structural":
                    structural_result = verify_structural_rules(story)
                    structural_details = (
                        f"Paragraphs: {structural_result['paragraph_count']}/3, "
                        f"Long sentences: {structural_result['long_sentences']}"
                    )
                    lexical_result["adherence"] = (
                        lexical_result["adherence"] * 0.5 +
                        structural_result["structural_adherence"] * 0.5
                    )
                
                result = {
                    **lexical_result,
                    "R": R,
                    "prompt_len": len(prompt),
                    "details": f"Type: {constraint_type}. {structural_details}".strip()
                }
                
                write_results_to_csv(CSV_PATH, experiment_name, trial, model, result)
                logger.info(
                    "Model %s | Trial %d: Combined adherence: %.1f%% (%s)",
                    model, trial, result["adherence"] * 100, structural_details
                )

if __name__ == "__main__":
    run_experiment()