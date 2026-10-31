import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

DATA = Path("data/interim/instruction_leakage_clean_v0.9")
REPORT = Path("reports/quality/instruction_quality_signals_v0.9.json")
CANDIDATES = Path("data/interim/instruction_quality_candidates_v0.9.csv")
QUARANTINE = Path("data/interim/instruction_quality_quarantine_v0.9.csv")

if REPORT.exists() or CANDIDATES.exists():
    raise SystemExit("Çıktı dosyası zaten var; üzerine yazılmadı.")

url_pattern = re.compile(r"https?://[^\s)\]]+", re.I)
markdown_link = re.compile(r"\[[^\]]*\]\(https?://[^)]*\)", re.I)

law_reference = re.compile(
    r"(?:TCK|TMK|TBK|CMK|TTK|İİK|IİK|İYUK|IYUK|VUK)"
    r"\s*(?:md\.?|m\.?|madde(?:si)?)\s*"
    r"\d+(?:/\d+)?",
    re.I
)

def reference_only_answer(answer):
    text = markdown_link.sub(" ", answer)
    text = url_pattern.sub(" ", text)
    text = text.strip().strip("()[]{}.,;: \t\n")
    text = " ".join(text.split())
    return bool(law_reference.fullmatch(text))

def detect_signals(question, answer):
    signals = []

    q = question.strip()
    a = answer.strip()

    if len(q) <= 80 and "?" not in q:
        signals.append("short_question_without_question_mark")

    if len(q) <= 10:
        signals.append("very_short_question")

    if len(a) <= 12:
        signals.append("very_short_answer")

    if url_pattern.search(q):
        signals.append("url_in_question")

    if url_pattern.search(a):
        signals.append("url_in_answer")

    if reference_only_answer(a):
        signals.append("possible_reference_only_answer")

    return signals

with QUARANTINE.open(encoding="utf-8-sig", newline="") as f:
    known_issues = {
        row["record_id"]: row["quality_flag"]
        for row in csv.DictReader(f)
    }

if len(known_issues) != 2:
    raise ValueError("Önceki iki karantina kaydı bekleniyordu.")

total = 0
candidate_count = 0
schema_errors = 0
signal_counts = Counter()
split_counts = Counter()
candidate_splits = Counter()
examples = defaultdict(list)
known_matches = {}

CANDIDATES.parent.mkdir(parents=True, exist_ok=True)
REPORT.parent.mkdir(parents=True, exist_ok=True)

temporary_csv = CANDIDATES.with_suffix(".csv.tmp")

try:
    with temporary_csv.open(
        "w", encoding="utf-8-sig", newline=""
    ) as output:
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "record_id",
                "split",
                "quality_signals",
                "question_length",
                "answer_length",
                "review_status",
            ],
        )
        writer.writeheader()

        for split in ("train", "validation", "test"):
            path = DATA / f"{split}.jsonl"

            with path.open(encoding="utf-8") as f:
                for line_number, line in enumerate(f, 1):
                    if not line.strip():
                        continue

                    total += 1
                    split_counts[split] += 1

                    try:
                        record = json.loads(line)
                        record_id = record["id"]
                        messages = record["messages"]

                        question = messages[0]["content"]
                        answer = messages[1]["content"]

                        if not isinstance(question, str) or not isinstance(answer, str):
                            raise ValueError("Metin alanı string değil.")

                    except (KeyError, IndexError, TypeError, ValueError):
                        schema_errors += 1
                        continue

                    signals = detect_signals(question, answer)

                    if record_id in known_issues:
                        known_matches[record_id] = {
                            "original_quality_flag": known_issues[record_id],
                            "detected_signals": signals,
                            "split": split,
                        }

                    if not signals:
                        continue

                    candidate_count += 1
                    candidate_splits[split] += 1

                    for signal in signals:
                        signal_counts[signal] += 1

                        if len(examples[signal]) < 8:
                            examples[signal].append({
                                "record_id": record_id,
                                "split": split,
                                "question_preview": question[:100],
                                "answer_preview": answer[:100],
                            })

                    writer.writerow({
                        "record_id": record_id,
                        "split": split,
                        "quality_signals": "|".join(signals),
                        "question_length": len(question),
                        "answer_length": len(answer),
                        "review_status": "needs_review",
                    })

    if total != 124510:
        raise ValueError(
            f"124510 kayıt bekleniyordu, {total} bulundu."
        )

    if schema_errors:
        raise ValueError(
            f"{schema_errors} kayıt yapısı okunamadı."
        )

    if set(known_matches) != set(known_issues):
        raise ValueError(
            "Önceden bilinen iki kalite kaydı bulunamadı."
        )

    report = {
        "project": "LexiTech TR",
        "version": "v0.9",
        "scan_type": "heuristic_quality_signals",
        "total_qa": total,
        "total_candidates": candidate_count,
        "candidate_percentage": round(
            100 * candidate_count / total, 3
        ),
        "signal_counts": dict(signal_counts),
        "split_counts": dict(split_counts),
        "candidate_splits": dict(candidate_splits),
        "schema_errors": schema_errors,
        "known_issues_crosscheck": known_matches,
        "examples_per_signal": dict(examples),
        "important_note": (
            "Bu kurallar yalnızca şüpheli kayıtları belirler. "
            "İşaretlenen kayıtlar otomatik olarak hatalı "
            "veya eğitim için uygunsuz kabul edilemez."
        ),
        "records_removed": 0,
        "human_approved": 0,
    }

    REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    temporary_csv.replace(CANDIDATES)

except Exception:
    if temporary_csv.exists():
        temporary_csv.unlink()
    raise

print("LEXITECH TR - TAM INSTRUCTION KALITE TARAMASI")
print("=" * 60)
print("Taranan QA:", total)
print("Inceleme adayi QA:", candidate_count)
print("Aday orani (%):", round(100 * candidate_count / total, 3))
print("Yapisal okuma hatasi:", schema_errors)

print("\nKALITE BELIRTILERI")
for signal, count in signal_counts.most_common():
    print(f"{signal}: {count}")

print("\nSPLIT DAGILIMI")
for split in ("train", "validation", "test"):
    print(
        f"{split}: {candidate_splits[split]} aday / "
        f"{split_counts[split]} QA"
    )

print("\nONCEDEN BILINEN IKI KAYIT")
for record_id, details in known_matches.items():
    print("Kayit:", record_id)
    print("Onceki uyari:", details["original_quality_flag"])
    print("Yeni belirtiler:", ", ".join(details["detected_signals"]))

print("\nRapor:", REPORT)
print("Inceleme adaylari:", CANDIDATES)
print("Silinen kayit: 0")
print("Nihai insan onayi: 0")
print("Ana veri setleri degistirilmedi.")
