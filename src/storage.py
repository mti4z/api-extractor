"""Persistencia: guarda los registros limpios en CSV y JSON."""
import csv
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def save_json(records: list[dict], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    logger.info("JSON guardado: %s (%d registros)", path.name, len(records))
    return path


def save_csv(records: list[dict], path: Path) -> Path:
    if not records:
        raise ValueError("No hay registros para guardar.")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)
    logger.info("CSV guardado: %s (%d registros)", path.name, len(records))
    return path
