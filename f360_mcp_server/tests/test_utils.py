import os
import json
import difflib
from typing import List, Dict, Any

def compare_command_logs(test_name: str, history: List[Dict[str, Any]], reference_dir: str = "tests/references"):
    """
    Compares the current command history with a golden reference file.
    Automatically handles updating references if UPDATE_REFERENCES env var is set.
    """
    os.makedirs(reference_dir, exist_ok=True)
    ref_path = os.path.join(reference_dir, f"{test_name}.json")
    
    # Clean history of non-stable fields for comparison
    clean_history = []
    for entry in history:
        clean_entry = entry.copy()
        clean_entry.pop("timestamp", None)
        # Ignore volatile command_metadata (docstrings/help text)
        res = clean_entry.get("result")
        if isinstance(res, dict):
            res.pop("command_metadata", None)
        clean_history.append(clean_entry)

    if os.environ.get("UPDATE_REFERENCES", "false").lower() == "true":
        with open(ref_path, "w") as f:
            json.dump(clean_history, f, indent=2)
        print(f"\n[STABILITY] Updated reference for {test_name} at {ref_path}")
        return

    if not os.path.exists(ref_path):
        raise FileNotFoundError(
            f"Reference file not found for {test_name} at {ref_path}. "
            "Run tests with UPDATE_REFERENCES=true to generate it."
        )

    with open(ref_path, "r") as f:
        reference = json.load(f)

    if clean_history != reference:
        # Generate a nice diff
        ref_str = json.dumps(reference, indent=2).splitlines()
        hist_str = json.dumps(clean_history, indent=2).splitlines()
        diff = difflib.unified_diff(ref_str, hist_str, fromfile="reference", tofile="current", lineterm="")
        diff_text = "\n".join(diff)
        
        raise AssertionError(
            f"Command stability check failed for {test_name}!\n"
            f"Diff:\n{diff_text}\n\n"
            "If this change is intentional, run with UPDATE_REFERENCES=true to update the golden files."
        )
