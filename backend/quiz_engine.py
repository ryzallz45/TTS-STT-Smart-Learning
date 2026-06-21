import difflib
import re
from typing import List, Dict, Any


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def word_error_rate(reference: str, hypothesis: str) -> float:
    ref_words = normalize_text(reference).split()
    hyp_words = normalize_text(hypothesis).split()

    if not ref_words:
        return 0.0

    n, m = len(ref_words), len(hyp_words)
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if ref_words[i - 1] == hyp_words[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1,
                dp[i - 1][j - 1] + cost,
            )

    errors = dp[n][m]
    return errors / n


def evaluate_pronunciation(target_text: str, transcribed_text: str) -> Dict[str, Any]:
    ref = normalize_text(target_text)
    hyp = normalize_text(transcribed_text)

    ref_words = ref.split()
    hyp_words = hyp.split()

    wer = word_error_rate(target_text, transcribed_text)
    word_accuracy = max(0, (1 - wer) * 100)

    matcher = difflib.SequenceMatcher(None, ref_words, hyp_words)

    word_feedback = []
    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == 'equal':
            for w in ref_words[i1:i2]:
                word_feedback.append({"word": w, "status": "correct"})
        elif op == 'replace':
            for w in ref_words[i1:i2]:
                word_feedback.append({"word": w, "status": "wrong"})
        elif op == 'delete':
            for w in ref_words[i1:i2]:
                word_feedback.append({"word": w, "status": "missing"})

    extra_words = []
    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == 'insert':
            for w in hyp_words[j1:j2]:
                extra_words.append(w)

    ref_chars = list(ref)
    hyp_chars = list(hyp)
    if ref_chars:
        char_matches = sum(1 for a, b in zip(ref_chars, hyp_chars) if a == b)
        char_accuracy = (char_matches / len(ref_chars)) * 100
    else:
        char_accuracy = 100

    overall_score = round(word_accuracy * 0.7 + char_accuracy * 0.3, 1)

    if overall_score >= 90:
        grade = "Sempurna!"
        grade_class = "excellent"
    elif overall_score >= 75:
        grade = "Baik"
        grade_class = "good"
    elif overall_score >= 50:
        grade = "Cukup"
        grade_class = "fair"
    else:
        grade = "Perlu Latihan"
        grade_class = "poor"

    return {
        "score": overall_score,
        "grade": grade,
        "grade_class": grade_class,
        "word_accuracy": round(word_accuracy, 1),
        "char_accuracy": round(char_accuracy, 1),
        "wer": round(wer * 100, 1),
        "word_feedback": word_feedback,
        "extra_words": extra_words,
        "reference_text": target_text,
        "transcribed_text": transcribed_text,
    }
