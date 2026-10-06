from pathlib import Path
import hashlib
import json

import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"


def load_config():
    """Proje konfigürasyonunu yükler."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def create_record_id(source, question, answer):
    """
    Kaynak + soru + cevap üzerinden deterministik kayıt kimliği üretir.
    Aynı girdi her çalıştırmada aynı ID'yi verir.
    """
    content = f"{source}\n{question}\n{answer}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def read_jsonl(file_path):
    """JSONL dosyasını satır satır okur."""
    with open(file_path, "r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                yield line_number, json.loads(line)

            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Geçersiz JSON: {file_path}, satır {line_number}"
                ) from error


def transform_sinanelms(record, line_number):
    """sinanelms/hukukisorular kaydını ortak şemaya dönüştürür."""

    question = record.get("soru")
    answer = record.get("cevap")

    source = "sinanelms/hukukisorular"

    return {
        "id": create_record_id(source, question, answer),
        "source": source,
        "source_split": "train",
        "source_row": line_number,
        "source_document": record.get("dosya_adi"),
        "question": question,
        "answer": answer,
        "metadata": {
            "soru_uzunluk": record.get("soru_uzunluk"),
            "cevap_uzunluk": record.get("cevap_uzunluk"),
            "top_uzunluk": record.get("top_uzunluk"),
            "token_sayisi": record.get("token_sayisi"),
        },
    }


def transform_orioncaf(record, line_number):
    """OrionCAF kaydını ortak şemaya dönüştürür."""

    question = record.get("question")
    answer = record.get("answer")

    source = "OrionCAF/turkish_law_qa_dataset"

    return {
        "id": create_record_id(source, question, answer),
        "source": source,
        "source_split": "train",
        "source_row": line_number,

        # Kaynak dataset document ID sağlamıyor.
        "source_document": None,

        "question": question,
        "answer": answer,
        "metadata": {},
    }


def extract_file(input_path, output_path, transformer):
    """Bir raw JSONL dosyasını ortak şemaya dönüştürür."""

    output_path.parent.mkdir(parents=True, exist_ok=True)

    record_count = 0

    with open(output_path, "w", encoding="utf-8") as output_file:

        for line_number, record in read_jsonl(input_path):

            transformed = transformer(record, line_number)

            json.dump(
                transformed,
                output_file,
                ensure_ascii=False
            )

            output_file.write("\n")
            record_count += 1

    return record_count


def main():
    config = load_config()

    raw_directory = PROJECT_ROOT / config["paths"]["raw"]
    extracted_directory = PROJECT_ROOT / config["paths"]["extracted"]

    sources = [
        {
            "input": raw_directory
            / "sinanelms__hukukisorular"
            / "train.jsonl",

            "output": extracted_directory
            / "sinanelms__hukukisorular"
            / "train.jsonl",

            "transformer": transform_sinanelms,
        },
        {
            "input": raw_directory
            / "OrionCAF__turkish_law_qa_dataset"
            / "train.jsonl",

            "output": extracted_directory
            / "OrionCAF__turkish_law_qa_dataset"
            / "train.jsonl",

            "transformer": transform_orioncaf,
        },
    ]

    total = 0

    for source in sources:

        print(f"\nOkunuyor: {source['input']}")

        count = extract_file(
            source["input"],
            source["output"],
            source["transformer"],
        )

        total += count

        print(f"Yazıldı: {source['output']}")
        print(f"Kayıt sayısı: {count}")

    print(f"\nToplam extracted kayıt: {total}")


if __name__ == "__main__":
    main()
