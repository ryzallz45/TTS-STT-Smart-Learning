import json
import uuid
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

_db_path: Optional[Path] = None


def init_db(storage_dir: Path):
    global _db_path
    _db_path = storage_dir / "flashcards.json"
    if not _db_path.exists():
        _save({"sets": [], "cards": []})


def _load() -> Dict[str, Any]:
    if _db_path and _db_path.exists():
        return json.loads(_db_path.read_text(encoding="utf-8"))
    return {"sets": [], "cards": []}


def _save(data: Dict[str, Any]):
    if _db_path:
        _db_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def create_set(name: str) -> Dict[str, Any]:
    db = _load()
    new_set = {"id": str(uuid.uuid4()), "name": name, "created_at": time.time()}
    db["sets"].append(new_set)
    _save(db)
    return new_set


def list_sets() -> List[Dict[str, Any]]:
    return _load()["sets"]


def delete_set(set_id: str) -> bool:
    db = _load()
    before = len(db["sets"])
    db["sets"] = [s for s in db["sets"] if s["id"] != set_id]
    db["cards"] = [c for c in db["cards"] if c["set_id"] != set_id]
    if len(db["sets"]) < before:
        _save(db)
        return True
    return False


def create_card(set_id: str, term: str, definition: str, language: str = "en") -> Dict[str, Any]:
    db = _load()
    card = {
        "id": str(uuid.uuid4()),
        "set_id": set_id,
        "term": term,
        "definition": definition,
        "language": language,
        "audio_filename": None,
        "created_at": time.time(),
    }
    db["cards"].append(card)
    _save(db)
    return card


def list_cards(set_id: Optional[str] = None) -> List[Dict[str, Any]]:
    db = _load()
    cards = db["cards"]
    if set_id:
        cards = [c for c in cards if c["set_id"] == set_id]
    return sorted(cards, key=lambda c: c["created_at"])


def get_card(card_id: str) -> Optional[Dict[str, Any]]:
    db = _load()
    for c in db["cards"]:
        if c["id"] == card_id:
            return c
    return None


def delete_card(card_id: str) -> bool:
    db = _load()
    before = len(db["cards"])
    db["cards"] = [c for c in db["cards"] if c["id"] != card_id]
    if len(db["cards"]) < before:
        _save(db)
        return True
    return False


def update_card_audio(card_id: str, audio_filename: str) -> bool:
    db = _load()
    for c in db["cards"]:
        if c["id"] == card_id:
            c["audio_filename"] = audio_filename
            _save(db)
            return True
    return False
