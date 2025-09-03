import json
from pathlib import Path
from typing import Any, Dict


def write_audit(audit: Dict[str, Any], out_path: Path):
    """
    Write the audit information as a JSON file to the specified output path.
    
    Args:
        audit (Dict): Dictionary containing audit data.
        out_path (Path): Path where the JSON file will be saved.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(audit, f, ensure_ascii=False, indent=2)
