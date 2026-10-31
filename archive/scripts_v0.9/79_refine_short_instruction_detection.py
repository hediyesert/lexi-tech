import csv
import json
import re
from collections import Counter
from pathlib import Path

CANDIDATES = Path(
    "data/interim/instruction_quality_candidates_v0.9.csv"
)
DATA = Path(
    "data/interim/instruction_leakage_clean_v0.9"
)

OLD_ENDINGS = (
    "sayınız|sayın|açıklayınız|açıklayın|"
    "belirtiniz|belirtin|yazınız|yazın|"
    "sıralayınız|sıralayın|tanımlayınız|tanımlayın|"
    "karşılaştırınız|karşılaştırın|"
    "değerlendiriniz|değerlendirin|"
    "tartışınız|tartışın|anlatınız|anlatın|"
    "inceleyiniz|inceleyin|listeleyiniz|listeleyin|"
    "özetleyiniz|özetleyin|gösteriniz|gösterin|"
    "veriniz|verin|izah ediniz|izah edin"
)

NEW_ENDINGS = (
    OLD_ENDINGS
    + "|yapınız|yapın|"
    "açıklamasını yapınız|tanımını yapınız"
)

OLD_PATTERN = re.compile(
    r"(?:" + OLD_ENDINGS + r")\s*[.!…]*\s*$",
    re.IGNORECASE,
)

NEW_PATTERN = re.compile(
    r"(?:" + NEW_ENDINGS + r")\s*[.!…]*\s*$",
    re.IGNORECASE,
)

TRAILING_LAW = re.compile(
    r"\s*\([^()]{1,70}\)\s*$"
)

def normalize_tail(text):
    text = text.strip()

    # En fazla iki sonda yer alan parantezli notu kaldır.
    # Bu işlem yalnızca sınıflandırma için yapılır.
    for _ in range(2):
        match = TRAILING_LAW.search(text)

        if not match:
            break

        inside = match.group().strip().strip("()")

        if re.search(
            r"\b(?:TCK|TMK|TBK|CMK|TTK|VUK|"
            r"İİK|IİK|İYUK|IYUK|madde|m\.)\b",
            inside,
            re.IGNORECASE,
        ):
            text = text[:match.start()].rstrip()
        else:
            break

    return text

with CANDIDATES.open(encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

wanted = {
    row["record_id"]
    for row in rows
    if "short_question_without_question_mark"
    in row["quality_signals"].split("|")
}

if len(wanted) != 268:
    raise ValueError(
        f"268 kısa soru bekleniyordu: {len(wanted)}"
    )

questions = {}

for split in ("train", "validation", "test"):
    with (DATA / f"{split}.jsonl").open(
        encoding="utf-8"
    ) as f:
        for line in f:
            if not line.strip():
                continue

            record = json.loads(line)
            rid = record["id"]

            if rid in wanted:
                questions[rid] = (
                    split,
                    record["messages"][0]["content"]
                )

if set(questions) != wanted:
    raise ValueError("Bazı sorular bulunamadı.")

old_match = set()
new_match = set()

for rid, (split, question) in questions.items():
    if OLD_PATTERN.search(question.strip()):
        old_match.add(rid)

    normalized = normalize_tail(question)

    if NEW_PATTERN.search(normalized):
        new_match.add(rid)

if not old_match.issubset(new_match):
    raise ValueError(
        "Önceki geçerli eşleşmelerden bazıları kayboldu."
    )

newly_recognized = sorted(new_match - old_match)
still_unmatched = sorted(wanted - new_match)

print("LEXITECH TR - KISA TALIMAT KURALI v2")
print("=" * 65)
print("Toplam kısa soru:", len(wanted))
print("Eski kural eşleşmesi:", len(old_match))
print("Yeni kural eşleşmesi:", len(new_match))
print("Yeni tanınan talimat:", len(newly_recognized))
print("İçerik incelemesi gereken:", len(still_unmatched))

print("\nYENİ TANINAN TALİMAT ÖRNEKLERİ")
for rid in newly_recognized[:10]:
    split, question = questions[rid]
    print(f"- [{split}] {question[:160]}")

print("\n" + "=" * 65)
print("HALA EŞLEŞMEYEN TÜM METİNLER")
print("=" * 65)

for index, rid in enumerate(still_unmatched, 1):
    split, question = questions[rid]

    print(f"\n{index}. KAYIT")
    print("Split:", split)
    print("ID:", rid)
    print("METİN:", question.replace("\n", " ")[:300])

print("\nSplit dağılımı:", dict(
    Counter(questions[rid][0] for rid in still_unmatched)
))
print("\nHiçbir dosya değiştirilmedi.")
