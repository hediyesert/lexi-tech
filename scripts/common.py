"""Pipeline adımlarının paylaştığı yardımcılar."""
import csv
import hashlib
import json
import re
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"
INVENTORY = PROJECT_ROOT / "reports/sources/legislation_documents.csv"

WORD_CHARS = "A-Za-zÇĞİÖŞÜçğıöşüÂâÎîÛû"

# Madde başlığı: "MADDE 12 –", "Geçici Madde 1 –", "Mükerrer Madde 355 –", "Ek Madde 3 –".
ARTICLE_HEADING = re.compile(
    r"(?im)^[ \t]*(?:(mükerrer|ek|geçici)[ \t]+)?"
    r"madde[ \t]+(\d+)(?:/([A-Z]))?(?=[ \t.\-–—]|$)"
)


def load_config():
    with CONFIG_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def path_of(*parts):
    return PROJECT_ROOT.joinpath(*parts)


def read_jsonl(path):
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def write_jsonl(path, records):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1
    return count


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_inventory():
    with INVENTORY.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def tr_lower(text):
    return text.replace("I", "ı").replace("İ", "i").lower()


def words(text):
    return re.findall(rf"[{WORD_CHARS}]+", text)


def strip_whitespace(text):
    return re.sub(r"\s+", "", text)


def article_key(prefix, number, letter=None):
    """Madde kimliği: '81', 'G1' (geçici), 'E3' (ek), 'M355' (mükerrer), '26/A'."""
    prefix = tr_lower(prefix or "")
    mark = {"": "", "geçici": "G", "ek": "E", "mükerrer": "M"}[prefix]
    return f"{mark}{int(number)}" + (f"/{letter}" if letter else "")


def build_article_index(document):
    """Kanun metnini maddelere ayırır: {madde_kimliği: {caption, text}}.

    Yalnızca ana kanun bölümüne bakılır; değişiklik tablolarındaki madde
    numaraları dizine girmez. Aynı numara tekrar ederse ilk geçiş korunur.
    """
    text = document["text"]
    main = next(s for s in document["sections"] if s["section_type"] == "main_law")
    headings = list(ARTICLE_HEADING.finditer(text, main["start_char"], main["end_char"]))

    index = {}
    for position, match in enumerate(headings):
        key = article_key(match.group(1), match.group(2), match.group(3))
        if key in index:
            continue

        end = (
            headings[position + 1].start()
            if position + 1 < len(headings)
            else main["end_char"]
        )
        before = text[max(0, match.start() - 120):match.start()].rstrip("\n")
        caption = before.rsplit("\n", 1)[-1].strip()
        body = text[match.start():end].strip()
        index[key] = {"caption": caption, "text": body}

    return index
