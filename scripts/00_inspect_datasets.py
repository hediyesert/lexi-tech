from datasets import load_dataset


DATASETS = [
    "sinanelms/hukukisorular",
    "OrionCAF/turkish_law_qa_dataset",
]


def inspect_dataset(dataset_name):
    print("\n" + "=" * 70)
    print(f"Dataset: {dataset_name}")
    print("=" * 70)

    dataset = load_dataset(dataset_name)

    print("\nSplitler:")
    print(dataset)

    for split_name, split_data in dataset.items():
        print(f"\nSplit: {split_name}")
        print(f"Kayıt sayısı: {len(split_data)}")
        print(f"Kolonlar: {split_data.column_names}")

        if len(split_data) > 0:
            print("\nİlk kayıt:")
            print(split_data[0])


def main():
    for dataset_name in DATASETS:
        inspect_dataset(dataset_name)


if __name__ == "__main__":
    main()
