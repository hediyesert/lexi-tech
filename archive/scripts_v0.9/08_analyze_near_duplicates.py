from pathlib import Path
import json


PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_PATH = (
    PROJECT_ROOT
    / "reports"
    / "deduplication"
    / "near_duplicate_candidates.jsonl"
)


def main():

    total_pairs = 0

    unique_ids = set()

    similarity_85_90 = 0
    similarity_90_95 = 0
    similarity_95_100 = 0
    similarity_100 = 0

    same_question = 0
    same_answer = 0

    min_jaccard = 1.0
    max_jaccard = 0.0
    total_jaccard = 0.0

    with open(
        INPUT_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        for line in file:

            record = json.loads(line)

            total_pairs += 1

            jaccard = record["jaccard"]

            left = record["left"]
            right = record["right"]

            unique_ids.add(left["id"])
            unique_ids.add(right["id"])

            total_jaccard += jaccard

            min_jaccard = min(
                min_jaccard,
                jaccard
            )

            max_jaccard = max(
                max_jaccard,
                jaccard
            )

            if 0.85 <= jaccard < 0.90:
                similarity_85_90 += 1

            elif 0.90 <= jaccard < 0.95:
                similarity_90_95 += 1

            elif 0.95 <= jaccard < 1.0:
                similarity_95_100 += 1

            elif jaccard == 1.0:
                similarity_100 += 1

            if (
                left["question"].strip()
                == right["question"].strip()
            ):
                same_question += 1

            if (
                left["answer"].strip()
                == right["answer"].strip()
            ):
                same_answer += 1

    average_jaccard = (
        total_jaccard / total_pairs
        if total_pairs
        else 0.0
    )

    print("=" * 70)
    print("NEAR-DUPLICATE ANALİZİ")
    print("=" * 70)

    print(
        f"Toplam doğrulanmış çift : {total_pairs}"
    )

    print(
        f"Etkilenen benzersiz kayıt: {len(unique_ids)}"
    )

    print("\nJaccard dağılımı:")

    print(
        f"0.85 - <0.90 : {similarity_85_90}"
    )

    print(
        f"0.90 - <0.95 : {similarity_90_95}"
    )

    print(
        f"0.95 - <1.00 : {similarity_95_100}"
    )

    print(
        f"1.00         : {similarity_100}"
    )

    print("\nEk kontroller:")

    print(
        f"Aynı soru bulunan çift : {same_question}"
    )

    print(
        f"Aynı cevap bulunan çift: {same_answer}"
    )

    print(
        f"Minimum Jaccard         : {min_jaccard:.6f}"
    )

    print(
        f"Maksimum Jaccard        : {max_jaccard:.6f}"
    )

    print(
        f"Ortalama Jaccard        : {average_jaccard:.6f}"
    )


if __name__ == "__main__":
    main()
