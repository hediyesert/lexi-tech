from pathlib import Path
import json
import re

from datasketch import MinHash, MinHashLSH
import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "deduplicated"
    / "exact_unique.jsonl"
)

REPORT_DIR = PROJECT_ROOT / "reports" / "deduplication"

RAW_CANDIDATE_PATH = (
    REPORT_DIR / "lsh_candidate_pairs.tsv"
)

VERIFIED_REPORT_PATH = (
    REPORT_DIR / "near_duplicate_candidates.jsonl"
)

SUMMARY_REPORT_PATH = (
    REPORT_DIR / "near_duplicate_summary.json"
)


def load_config():
    """config.yaml dosyasını yükler."""

    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def tokenize(text):
    """Metni küçük harfe çevirip kelime tokenlarına ayırır."""

    return re.findall(
        r"\w+",
        text.lower(),
        flags=re.UNICODE
    )


def create_shingles(question, answer, shingle_size=3):
    """Soru + cevap üzerinden kelime shingles üretir."""

    text = f"{question} {answer}"

    tokens = tokenize(text)

    if not tokens:
        return set()

    if len(tokens) < shingle_size:
        return {" ".join(tokens)}

    return {
        " ".join(tokens[i:i + shingle_size])
        for i in range(
            len(tokens) - shingle_size + 1
        )
    }


def create_minhash(shingles, num_perm):
    """Shingle kümesinden MinHash imzası üretir."""

    minhash = MinHash(
        num_perm=num_perm
    )

    for shingle in sorted(shingles):
        minhash.update(
            shingle.encode("utf-8")
        )

    return minhash


def calculate_jaccard(left, right):
    """İki shingle kümesinin gerçek Jaccard değerini hesaplar."""

    union = left | right

    if not union:
        return 0.0

    intersection = left & right

    return len(intersection) / len(union)


def pass_one_find_candidates(threshold, num_perm):
    """
    PASS 1

    Dataset'i streaming olarak okur.

    Her kayıt için:
    - shingles oluşturur,
    - MinHash hesaplar,
    - daha önce indekslenen kayıtları sorgular,
    - LSH aday çiftlerini doğrudan diske yazar,
    - ardından mevcut kaydı LSH indeksine ekler.

    Tam dataset veya shingle kümeleri RAM'de tutulmaz.
    """

    print("\nPASS 1/3")
    print("LSH adayları aranıyor...")

    lsh = MinHashLSH(
        threshold=threshold,
        num_perm=num_perm
    )

    record_count = 0
    candidate_count = 0

    with open(
        INPUT_PATH,
        "r",
        encoding="utf-8"
    ) as input_file, open(
        RAW_CANDIDATE_PATH,
        "w",
        encoding="utf-8"
    ) as candidate_file:

        for index, line in enumerate(input_file):

            record = json.loads(line)

            shingles = create_shingles(
                record["question"],
                record["answer"]
            )

            minhash = create_minhash(
                shingles,
                num_perm
            )

            matches = lsh.query(minhash)

            # query mevcut kayıt insert edilmeden önce yapıldığı için
            # match her zaman daha önceki bir kayıttır.
            for match in matches:

                candidate_file.write(
                    f"{int(match)}\t{index}\n"
                )

                candidate_count += 1

            lsh.insert(
                str(index),
                minhash
            )

            record_count += 1

            if record_count % 10000 == 0:
                print(
                    f"İşlenen kayıt: {record_count}"
                    f" | LSH adayı: {candidate_count}"
                )

    return record_count, candidate_count


def load_candidate_indexes():
    """
    PASS 2 için yalnızca aday çiftlerde geçen
    kayıt indekslerini toplar.
    """

    indexes = set()

    with open(
        RAW_CANDIDATE_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            left, right = line.split("\t")

            indexes.add(int(left))
            indexes.add(int(right))

    return indexes


def pass_two_collect_candidate_records(candidate_indexes):
    """
    Dataset'i ikinci kez streaming okur.

    Yalnızca LSH adaylarında geçen kayıtları RAM'e alır.
    """

    print("\nPASS 2/3")

    print(
        "Jaccard doğrulaması için gerekli kayıtlar yükleniyor..."
    )

    candidate_records = {}

    with open(
        INPUT_PATH,
        "r",
        encoding="utf-8"
    ) as input_file:

        for index, line in enumerate(input_file):

            if index not in candidate_indexes:
                continue

            record = json.loads(line)

            candidate_records[index] = {
                "id": record["id"],
                "source": record["source"],
                "question": record["question"],
                "answer": record["answer"],
            }

    print(
        f"RAM'e alınan aday kayıt: {len(candidate_records)}"
    )

    return candidate_records


def pass_three_verify(
    candidate_records,
    threshold,
    record_count,
    candidate_count,
    num_perm
):
    """
    PASS 3

    LSH tarafından bulunan aday çiftlerin gerçek
    shingle Jaccard değerini hesaplar.

    Sadece threshold üzerindeki çiftleri nihai
    rapora yazar.
    """

    print("\nPASS 3/3")
    print("Gerçek Jaccard doğrulaması yapılıyor...")

    verified_count = 0
    cross_source_count = 0
    checked_count = 0

    with open(
        RAW_CANDIDATE_PATH,
        "r",
        encoding="utf-8"
    ) as candidate_file, open(
        VERIFIED_REPORT_PATH,
        "w",
        encoding="utf-8"
    ) as verified_file:

        for line in candidate_file:

            line = line.strip()

            if not line:
                continue

            left_text, right_text = line.split("\t")

            left_index = int(left_text)
            right_index = int(right_text)

            left_record = candidate_records[left_index]
            right_record = candidate_records[right_index]

            left_shingles = create_shingles(
                left_record["question"],
                left_record["answer"]
            )

            right_shingles = create_shingles(
                right_record["question"],
                right_record["answer"]
            )

            jaccard = calculate_jaccard(
                left_shingles,
                right_shingles
            )

            checked_count += 1

            if jaccard < threshold:
                continue

            verified_count += 1

            cross_source = (
                left_record["source"]
                != right_record["source"]
            )

            if cross_source:
                cross_source_count += 1

            result = {
                "pair_number": verified_count,
                "jaccard": round(jaccard, 6),
                "left_index": left_index,
                "right_index": right_index,
                "left": {
                    "id": left_record["id"],
                    "source": left_record["source"],
                    "question": left_record["question"],
                    "answer": left_record["answer"],
                },
                "right": {
                    "id": right_record["id"],
                    "source": right_record["source"],
                    "question": right_record["question"],
                    "answer": right_record["answer"],
                },
                "cross_source": cross_source,
            }

            json.dump(
                result,
                verified_file,
                ensure_ascii=False
            )

            verified_file.write("\n")

            if checked_count % 10000 == 0:
                print(
                    f"Kontrol edilen aday: "
                    f"{checked_count}/{candidate_count}"
                )

    summary = {
        "input_records": record_count,
        "threshold": threshold,
        "num_perm": num_perm,
        "shingle_size": 3,
        "lsh_candidate_pairs": candidate_count,
        "verified_near_duplicate_pairs": verified_count,
        "cross_source_near_duplicate_pairs": cross_source_count,
    }

    with open(
        SUMMARY_REPORT_PATH,
        "w",
        encoding="utf-8"
    ) as summary_file:

        json.dump(
            summary,
            summary_file,
            ensure_ascii=False,
            indent=2
        )

    return verified_count, cross_source_count


def main():

    config = load_config()

    threshold = (
        config["deduplication"]["minhash"]["threshold"]
    )

    num_perm = (
        config["deduplication"]["minhash"]["num_perm"]
    )

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print("=" * 70)
    print("TAM CORPUS MINHASH / LSH ANALİZİ")
    print("=" * 70)

    print(f"Input       : {INPUT_PATH}")
    print(f"Threshold   : {threshold}")
    print(f"Num perm    : {num_perm}")
    print("Shingle size: 3")

    record_count, candidate_count = (
        pass_one_find_candidates(
            threshold,
            num_perm
        )
    )

    print("\nLSH taraması tamamlandı.")

    print(
        f"Toplam kayıt   : {record_count}"
    )

    print(
        f"LSH aday çifti : {candidate_count}"
    )

    candidate_indexes = load_candidate_indexes()

    print(
        f"Adaylarda geçen benzersiz kayıt: "
        f"{len(candidate_indexes)}"
    )

    candidate_records = (
        pass_two_collect_candidate_records(
            candidate_indexes
        )
    )

    verified_count, cross_source_count = (
        pass_three_verify(
            candidate_records,
            threshold,
            record_count,
            candidate_count,
            num_perm
        )
    )

    print("\n" + "=" * 70)
    print("ANALİZ TAMAMLANDI")
    print("=" * 70)

    print(
        f"Toplam kayıt                  : {record_count}"
    )

    print(
        f"LSH aday çifti                : {candidate_count}"
    )

    print(
        f"Doğrulanmış near-duplicate    : {verified_count}"
    )

    print(
        f"Cross-source near-duplicate   : {cross_source_count}"
    )

    print(
        f"\nHam LSH adayları : {RAW_CANDIDATE_PATH}"
    )

    print(
        f"Doğrulanmış rapor: {VERIFIED_REPORT_PATH}"
    )

    print(
        f"Özet rapor       : {SUMMARY_REPORT_PATH}"
    )

    print(
        "\nNOT: Bu işlem hiçbir kaydı silmedi."
    )


if __name__ == "__main__":
    main()
