import json
import uuid
import time
import random
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

_db_path: Optional[Path] = None

SEED_TOPICS = [
    {
        "id": "greetings",
        "name": "Greetings",
        "icon": "👋",
        "words": [
            {"id": "greet_1", "term": "Hello", "definition": "Halo", "example": "Hello, how are you today?", "language": "en"},
            {"id": "greet_2", "term": "Goodbye", "definition": "Selamat tinggal", "example": "Goodbye, see you tomorrow!", "language": "en"},
            {"id": "greet_3", "term": "Good morning", "definition": "Selamat pagi", "example": "Good morning, did you sleep well?", "language": "en"},
            {"id": "greet_4", "term": "Good night", "definition": "Selamat malam", "example": "Good night, sweet dreams!", "language": "en"},
            {"id": "greet_5", "term": "Thank you", "definition": "Terima kasih", "example": "Thank you for your help!", "language": "en"},
            {"id": "greet_6", "term": "Please", "definition": "Tolong", "example": "Please help me with this.", "language": "en"},
            {"id": "greet_7", "term": "Sorry", "definition": "Maaf", "example": "Sorry, I'm late.", "language": "en"},
            {"id": "greet_8", "term": "Yes", "definition": "Ya", "example": "Yes, I understand.", "language": "en"},
            {"id": "greet_9", "term": "No", "definition": "Tidak", "example": "No, thank you.", "language": "en"},
            {"id": "greet_10", "term": "How are you?", "definition": "Apa kabar?", "example": "How are you today?", "language": "en"},
        ],
    },
    {
        "id": "numbers",
        "name": "Angka & Numbers",
        "icon": "🔢",
        "words": [
            {"id": "num_1", "term": "One", "definition": "Satu", "example": "I have one book.", "language": "en"},
            {"id": "num_2", "term": "Two", "definition": "Dua", "example": "She has two cats.", "language": "en"},
            {"id": "num_3", "term": "Three", "definition": "Tiga", "example": "There are three chairs.", "language": "en"},
            {"id": "num_4", "term": "Four", "definition": "Empat", "example": "Four seasons in a year.", "language": "en"},
            {"id": "num_5", "term": "Five", "definition": "Lima", "example": "Five fingers on each hand.", "language": "en"},
            {"id": "num_6", "term": "Ten", "definition": "Sepuluh", "example": "Ten people are waiting.", "language": "en"},
            {"id": "num_7", "term": "Hundred", "definition": "Seratus", "example": "One hundred rupiah.", "language": "en"},
            {"id": "num_8", "term": "Thousand", "definition": "Seribu", "example": "One thousand steps.", "language": "en"},
        ],
    },
    {
        "id": "phrases",
        "name": "Daily Phrases",
        "icon": "💬",
        "words": [
            {"id": "phr_1", "term": "What is your name?", "definition": "Siapa nama Anda?", "example": "What is your name? Nice to meet you.", "language": "en"},
            {"id": "phr_2", "term": "My name is...", "definition": "Nama saya...", "example": "My name is John.", "language": "en"},
            {"id": "phr_3", "term": "Where are you from?", "definition": "Dari mana asal Anda?", "example": "Where are you from?", "language": "en"},
            {"id": "phr_4", "term": "I am from...", "definition": "Saya dari...", "example": "I am from Indonesia.", "language": "en"},
            {"id": "phr_5", "term": "How much?", "definition": "Berapa harganya?", "example": "How much is this?", "language": "en"},
            {"id": "phr_6", "term": "I like it", "definition": "Saya suka", "example": "I like this food.", "language": "en"},
            {"id": "phr_7", "term": "I don't understand", "definition": "Saya tidak mengerti", "example": "I don't understand, please repeat.", "language": "en"},
            {"id": "phr_8", "term": "Can you help me?", "definition": "Bisakah Anda membantu saya?", "example": "Can you help me with this?", "language": "en"},
        ],
    },
    {
        "id": "food",
        "name": "Makanan Indonesia",
        "icon": "🍜",
        "words": [
            {"id": "food_1", "term": "Nasi goreng", "definition": "Fried rice", "example": "Nasi goreng adalah makanan khas Indonesia.", "language": "id"},
            {"id": "food_2", "term": "Sate", "definition": "Satay", "example": "Sate ayam dengan bumbu kacang.", "language": "id"},
            {"id": "food_3", "term": "Rendang", "definition": "Beef rendang", "example": "Rendang berasal dari Padang.", "language": "id"},
            {"id": "food_4", "term": "Bakso", "definition": "Meatball soup", "example": "Bakso kuah hangat untuk cuaca dingin.", "language": "id"},
            {"id": "food_5", "term": "Gado-gado", "definition": "Mixed vegetables with peanut sauce", "example": "Gado-gado dengan saus kacang.", "language": "id"},
            {"id": "food_6", "term": "Mie ayam", "definition": "Chicken noodles", "example": "Mie ayam dengan pangsit.", "language": "id"},
            {"id": "food_7", "term": "Soto", "definition": "Traditional soup", "example": "Soto ayam hangat dan nikmat.", "language": "id"},
        ],
    },
]


def init_db(storage_dir: Path):
    global _db_path
    _db_path = storage_dir / "vocab_progress.json"
    if not _db_path.exists():
        _save({
            "learned_words": {},
            "progress": {
                "last_study_date": None,
                "streak": 0,
                "daily_log": {},
            },
        })


def _load() -> Dict[str, Any]:
    if _db_path and _db_path.exists():
        return json.loads(_db_path.read_text(encoding="utf-8"))
    return {"learned_words": {}, "progress": {"last_study_date": None, "streak": 0, "daily_log": {}}}


def _save(data: Dict[str, Any]):
    if _db_path:
        _db_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def get_topics() -> List[Dict[str, Any]]:
    topics = []
    for t in SEED_TOPICS:
        total = len(t["words"])
        learned = count_learned(t["id"])
        topics.append({
            "id": t["id"],
            "name": t["name"],
            "icon": t["icon"],
            "total_words": total,
            "learned_words": learned,
            "progress_pct": round(learned / total * 100) if total > 0 else 0,
        })
    return topics


def get_topic_words(topic_id: str) -> List[Dict[str, Any]]:
    for t in SEED_TOPICS:
        if t["id"] == topic_id:
            learned_ids = get_learned_ids(topic_id)
            words = []
            for w in t["words"]:
                word = dict(w)
                word["learned"] = w["id"] in learned_ids
                word["audio_filename"] = None
                words.append(word)
            return words
    return []


def get_learned_ids(topic_id: str) -> set:
    db = _load()
    return set(db["learned_words"].get(topic_id, []))


def count_learned(topic_id: str) -> int:
    return len(get_learned_ids(topic_id))


def mark_learned(topic_id: str, word_id: str) -> bool:
    db = _load()
    if topic_id not in db["learned_words"]:
        db["learned_words"][topic_id] = []
    if word_id not in db["learned_words"][topic_id]:
        db["learned_words"][topic_id].append(word_id)

    today = str(date.today())
    last = db["progress"].get("last_study_date")
    streak = db["progress"].get("streak", 0)

    if last == today:
        pass
    elif last == str(date.today() - timedelta(days=1)):
        streak += 1
    elif last != today:
        streak = 1

    db["progress"]["last_study_date"] = today
    db["progress"]["streak"] = streak

    daily_log = db["progress"].get("daily_log", {})
    daily_log[today] = daily_log.get(today, 0) + 1
    db["progress"]["daily_log"] = daily_log

    _save(db)
    return True


def mark_unlearned(topic_id: str, word_id: str) -> bool:
    db = _load()
    if topic_id in db["learned_words"]:
        if word_id in db["learned_words"][topic_id]:
            db["learned_words"][topic_id].remove(word_id)
            _save(db)
            return True
    return False


def get_progress() -> Dict[str, Any]:
    db = _load()
    total_all = sum(len(t["words"]) for t in SEED_TOPICS)
    total_learned = sum(len(get_learned_ids(t["id"])) for t in SEED_TOPICS)
    today = str(date.today())
    daily_log = db["progress"].get("daily_log", {})

    return {
        "streak": db["progress"].get("streak", 0),
        "last_study_date": db["progress"].get("last_study_date"),
        "total_words": total_all,
        "total_learned": total_learned,
        "overall_pct": round(total_learned / total_all * 100) if total_all > 0 else 0,
        "words_today": daily_log.get(today, 0),
    }


def update_word_audio(word_id: str, audio_filename: str):
    pass
