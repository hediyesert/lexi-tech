from pathlib import Path
import html
import json
import re
import unicodedata

from bs4 import BeautifulSoup
import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"


def load_config():
    """config.yaml dosyasını yükler."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def clean_text(text):
    """
    Metni normalize eder.

    İşlemler:
    - HTML entity çözme
    - HTML tag temizleme
    - Unicode NFC normalization
    - whitespace normalization
    """

    if text is None:
        return None

    text = str(text)

    # &amp;, &quot; vb.
    text = html.unescape(text)

    # HTML etiketlerini kaldır
    if "<" in text and ">" in text:
        text = BeautifulSoup(
            text,
            "lxml"
        ).get_text(" ")

    # Unicode normalization
    text = unicodedata.normalize("NFC", text)

    # Fazla boşluk, tab ve satır sonlarını normalize et
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def clean_record(record):
    """Tek bir extracted kaydı temizler."""

    question = clean_text(record.get("question"))
    answer = clean_text(record.get("answer"))

    # Boş soru veya cevap varsa kayıt kullanılamaz.
    if not question or not answer:
        return None

    cleaned_record = record.copy()

    cleaned_record["question"] = question
    cleaned_record["answer"] = answer

    return cleaned_record


def clean_file(input_path, output_path):
    """Extracted JSONL dosyasını temizler."""

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    total = 0
    kept = 0
    removed = 0
    changed = 0

    with open(input_path, "r", encoding="utf-8") as input_file, \
         open(output_path, "w", encoding="utf-8") as output_file:

        for line in input_file:
            line = line.strip()

            if not line:
                continue

            total += 1

            record = json.loads(line)
            cleaned_record = clean_record(record)

            if cleaned_record is None:
                removed += 1
                continue

            if (
                cleaned_record["question"] != record.get("question")
                or cleaned_record["answer"] != record.get("answer")
            ):
                changed += 1

            json.dump(
                cleaned_record,
                output_file,
                ensure_ascii=False
            )
            output_file.write("\n")

            kept += 1

    return {
        "total": total,
        "kept": kept,
        "removed": removed,
        "changed": changed,
    }


def main():
    config = load_config()

    extracted_directory = (
        PROJECT_ROOT / config["paths"]["extracted"]
    )

    cleaned_directory = (
        PROJECT_ROOT / config["paths"]["cleaned"]
    )

    input_files = sorted(
        extracted_directory.glob("*/train.jsonl")
    )

    grand_total = 0
    grand_kept = 0
    grand_removed = 0
    grand_changed = 0

    for input_path in input_files:

        relative_path = input_path.relative_to(
            extracted_directory
        )

        output_path = (
            cleaned_directory / relative_path
        )

        print("\n" + "=" * 70)
        print(f"Temizleniyor: {relative_path}")
        print("=" * 70)

        result = clean_file(
            input_path,
            output_path
        )

        for key, value in result.items():
            print(f"{key}: {value}")

        grand_total += result["total"]
        grand_kept += result["kept"]
        grand_removed += result["removed"]
        grand_changed += result["changed"]

    print("\n" + "=" * 70)
    print("CLEANING ÖZETİ")
    print("=" * 70)
    print(f"Toplam giriş : {grand_total}")
    print(f"Korunan      : {grand_kept}")
    print(f"Çıkarılan    : {grand_removed}")
    print(f"Değiştirilen : {grand_changed}")


if __name__ == "__main__":
    main()
