from pathlib import Path
import json

import yaml
from datasets import load_dataset


# Projenin ana dizini
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"


def load_config():
    """config.yaml dosyasını yükler."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def safe_dataset_name(dataset_name):
    """
    Hugging Face dataset adını klasör adı olarak kullanılabilir hale getirir.

    Örnek:
    sinanelms/hukukisorular
        ->
    sinanelms__hukukisorular
    """
    return dataset_name.replace("/", "__")


def save_split_as_jsonl(split_data, output_path):
    """
    Bir Hugging Face dataset split'ini JSONL formatında kaydeder.

    Her satır bir JSON kaydıdır.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as file:
        for record in split_data:
            json.dump(record, file, ensure_ascii=False)
            file.write("\n")


def download_dataset(dataset_name, raw_directory):
    """Dataset'i Hugging Face'ten indirir ve raw katmanına kaydeder."""

    print("\n" + "=" * 70)
    print(f"İndiriliyor: {dataset_name}")
    print("=" * 70)

    dataset = load_dataset(dataset_name)

    dataset_directory = (
        raw_directory / safe_dataset_name(dataset_name)
    )

    dataset_directory.mkdir(
        parents=True,
        exist_ok=True
    )

    for split_name, split_data in dataset.items():

        output_path = (
            dataset_directory / f"{split_name}.jsonl"
        )

        print(f"Split: {split_name}")
        print(f"Kayıt sayısı: {len(split_data)}")
        print(f"Kaydediliyor: {output_path}")

        save_split_as_jsonl(
            split_data,
            output_path
        )

    print(f"Tamamlandı: {dataset_name}")


def main():

    config = load_config()

    raw_directory = (
        PROJECT_ROOT / config["paths"]["raw"]
    )

    datasets_config = (
        config["datasets"]["huggingface"]
    )

    for dataset_config in datasets_config:

        if not dataset_config.get("enabled", True):
            continue

        dataset_name = dataset_config["name"]

        download_dataset(
            dataset_name,
            raw_directory
        )

    print("\nTüm etkin datasetler başarıyla kaydedildi.")


if __name__ == "__main__":
    main()
