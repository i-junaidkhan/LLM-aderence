#!/usr/bin/env python3
"""
MASTER RUNNER: Executes all experiments in sequence.

This script runs all individual experiments and aggregates results.
Use this to execute the full experimental suite.
"""

import logging
import subprocess
from pathlib import Path

# --- Configuration ---
# List of script filenames located in the 'experiments' subdirectory
EXPERIMENT_SCRIPTS = [
    "experiment_1_fatigue.py",
    "experiment_2_taxonomy.py",
    "experiment_3_contradictions.py",
    "experiment_4_complexity.py",
    "experiment_5_formats.py"
]
OUTPUT_DIR = Path("outputs")
LOG_FILE = OUTPUT_DIR / "master_runner.log"

def run_single_experiment(script_name: str, logger: logging.Logger):
    """Runs a single experiment script located in the 'experiments' folder."""
    script_path = Path("experiments") / script_name
    logger.info(f"--- Starting {script_path} ---")
    
    result = subprocess.run(
        ["python3", str(script_path)],
        capture_output=True,
        text=True,
        check=False  # We will check the return code manually
    )
    
    if result.returncode != 0:
        logger.error(f"!!! Experiment {script_name} FAILED !!!")
        logger.error("STDOUT:\n" + result.stdout)
        logger.error("STDERR:\n" + result.stderr)
    else:
        logger.info(f"--- Experiment {script_name} completed successfully ---")
        # Log the last few lines of output for a summary
        last_lines = "\n".join(result.stdout.strip().split('\n')[-5:])
        logger.info(f"Final output summary for {script_name}:\n{last_lines}")

def main():
    """Sets up logging and runs all experiments."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Setup logging to both file and console
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)

    logger.info("==============================================")
    logger.info("   STARTING FULL EXPERIMENT SUITE RUN")
    logger.info("==============================================")
    
    for script in EXPERIMENT_SCRIPTS:
        run_single_experiment(script, logger)
        
    logger.info("==============================================")
    logger.info("   ALL EXPERIMENTS COMPLETED")
    logger.info(f"  Log file saved to: {LOG_FILE}")
    logger.info("==============================================")

if __name__ == "__main__":
    main()