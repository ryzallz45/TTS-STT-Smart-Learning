from typing import Dict, Any, List, Optional

SCENARIOS = [
    {
        "id": "restaurant",
        "title": "Di Restoran",
        "icon": "🍽️",
        "description": "Praktik memesan makanan di restoran dalam bahasa Indonesia",
        "language": "id",
        "dialogue": [
            {"speaker": "ai", "text": "Selamat datang di restoran kami. Ada yang bisa saya bantu?"},
            {"speaker": "user", "text": "", "hint": "Sapa dan minta meja untuk 2 orang"},
            {"speaker": "ai", "text": "Tentu, silakan duduk di meja nomor 5. Ini menu makanannya."},
            {"speaker": "user", "text": "", "hint": "Tanya menu rekomendasi hari ini"},
            {"speaker": "ai", "text": "Menu rekomendasi hari ini adalah nasi goreng spesial dan sate ayam."},
            {"speaker": "user", "text": "", "hint": "Pesan nasi goreng spesial dan es teh"},
            {"speaker": "ai", "text": "Baik, nasi goreng spesial dan es teh. Apakah ada tambahan?"},
            {"speaker": "user", "text": "", "hint": "Katakan tidak ada, terima kasih"},
            {"speaker": "ai", "text": "Baik, pesanan akan segera kami proses. Mohon tunggu sebentar."},
            {"speaker": "user", "text": "", "hint": "Ucapkan terima kasih"},
            {"speaker": "ai", "text": "Terima kasih sudah menunggu. Selamat menikmati makanan Anda!"},
        ],
    },
    {
        "id": "introduction",
        "title": "Introducing Yourself",
        "icon": "👋",
        "description": "Practice introducing yourself in English",
        "language": "en",
        "dialogue": [
            {"speaker": "ai", "text": "Hello! Welcome to our conversation practice. What is your name?"},
            {"speaker": "user", "text": "", "hint": "Say your name and greet back"},
            {"speaker": "ai", "text": "Nice to meet you! Where are you from?"},
            {"speaker": "user", "text": "", "hint": "Say where you are from"},
            {"speaker": "ai", "text": "That's wonderful! What do you do for work or study?"},
            {"speaker": "user", "text": "", "hint": "Tell about your job or study"},
            {"speaker": "ai", "text": "Interesting! What are your hobbies?"},
            {"speaker": "user", "text": "", "hint": "Tell about your hobbies"},
            {"speaker": "ai", "text": "Great! It was nice talking to you. Have a wonderful day!"},
        ],
    },
    {
        "id": "shopping",
        "title": "Di Toko",
        "icon": "🛍️",
        "description": "Praktik berbelanja di toko dalam bahasa Indonesia",
        "language": "id",
        "dialogue": [
            {"speaker": "ai", "text": "Selamat datang di toko kami. Ada yang bisa saya bantu cari?"},
            {"speaker": "user", "text": "", "hint": "Tanya apakah mereka menjual baju"},
            {"speaker": "ai", "text": "Ada, kami memiliki berbagai macam baju. Ukuran apa yang Anda cari?"},
            {"speaker": "user", "text": "", "hint": "Sebut ukuran dan warna yang diinginkan"},
            {"speaker": "ai", "text": "Silakan lihat bagian sini. Kami punya warna biru dan hitam untuk ukuran Anda."},
            {"speaker": "user", "text": "", "hint": "Tanya harga baju tersebut"},
            {"speaker": "ai", "text": "Harganya Rp150.000. Saat ini ada diskon 20%."},
            {"speaker": "user", "text": "", "hint": "Katakan Anda akan membelinya"},
            {"speaker": "ai", "text": "Baik, silakan ke kasir untuk pembayaran. Terima kasih!"},
        ],
    },
    {
        "id": "hotel",
        "title": "At the Hotel",
        "icon": "🏨",
        "description": "Practice checking in at a hotel in English",
        "language": "en",
        "dialogue": [
            {"speaker": "ai", "text": "Good evening, welcome to Grand Hotel. Do you have a reservation?"},
            {"speaker": "user", "text": "", "hint": "Say yes, you have a reservation under your name"},
            {"speaker": "ai", "text": "Let me check. Yes, I found your reservation. A deluxe room for two nights?"},
            {"speaker": "user", "text": "", "hint": "Confirm and ask about breakfast"},
            {"speaker": "ai", "text": "Breakfast is served from 6 to 10 AM at the restaurant on the ground floor."},
            {"speaker": "user", "text": "", "hint": "Ask about the Wi-Fi password"},
            {"speaker": "ai", "text": "The Wi-Fi password is 'grandhotel123'. Here is your room key, room 508."},
            {"speaker": "user", "text": "", "hint": "Say thank you and ask about check-out time"},
            {"speaker": "ai", "text": "Check-out time is at 12 PM. Enjoy your stay!"},
        ],
    },
]


def list_scenarios() -> List[Dict[str, Any]]:
    result = []
    for s in SCENARIOS:
        user_turns = sum(1 for d in s["dialogue"] if d["speaker"] == "user")
        ai_turns = sum(1 for d in s["dialogue"] if d["speaker"] == "ai")
        result.append({
            "id": s["id"],
            "title": s["title"],
            "icon": s["icon"],
            "description": s["description"],
            "language": s["language"],
            "total_turns": len(s["dialogue"]),
            "user_turns": user_turns,
            "ai_turns": ai_turns,
        })
    return result


def get_scenario(scenario_id: str) -> Optional[Dict[str, Any]]:
    for s in SCENARIOS:
        if s["id"] == scenario_id:
            return s
    return None


def get_dialogue_at(scenario_id: str, step: int) -> Optional[Dict[str, str]]:
    scenario = get_scenario(scenario_id)
    if not scenario:
        return None
    if 0 <= step < len(scenario["dialogue"]):
        return scenario["dialogue"][step]
    return None
