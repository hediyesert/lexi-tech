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


def load_config():
    """config.yaml dosyasını yükler."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def tokenize(text):
    """
    Metni küçük harfe çevirir ve kelime tabanlı tokenlara ayırır.
    """
    return re.findall(
        r"\w+",
        text.lower(),
        flags=re.UNICODE
    )


def create_shingles(question, answer, shingle_size=3):
    """
    Soru + cevap metninden 3 kelimelik shingles üretir.
    """

    text = f"{question} {answer}"
    tokens = tokenize(text)

    if len(tokens) < shingle_size:
        return {" ".join(tokens)}

    return {
        " ".join(tokens[i:i + shingle_size])
        for i in range(
            len(tokens) - shingle_size + 1
        )
    }


def create_minhash(shingles, num_perm):
    """
    Shingle kümesinden MinHash imzası oluşturur.
    """

    minhash = MinHash(
        num_perm=num_perm
    )

    for shingle in sorted(shingles):
        minhash.update(
            shingle.encode("utf-8")
        )

    return minhash


def calculate_jaccard(left_shingles, right_shingles):
    """
    İki shingle kümesi arasındaki gerçek Jaccard
    benzerliğini hesaplar.
    """

    intersection = (
        left_shingles
        & right_shingles
    )

    union = (
        left_shingles
        | right_shingles
    )

    if not union:
        return 0.0

    return len(intersection) / len(union)


def main():
    config = load_config()

    threshold = (
        config["deduplication"]["minhash"]["threshold"]
    )

    num_perm = (
        config["deduplication"]["minhash"]["num_perm"]
    )

    # Şimdilik yalnızca ilk 5000 kayıt üzerinde test ediyoruz.
    sample_limit = 5000

    print("=" * 70)
    print("MINHASH / LSH ÖRNEK ANALİZİ")
    print("=" * 70)

    print(f"Input        : {INPUT_PATH}")
    print(f"Threshold    : {threshold}")
    print(f"Num perm     : {num_perm}")
    print(f"Sample limit : {sample_limit}")

    lsh = MinHashLSH(
        threshold=threshold,
        num_perm=num_perm
    )

    records = {}
    candidate_pairs = set()

    # --------------------------------------------------------
    # KAYITLARI OKU VE LSH ADAYLARINI BUL
    # --------------------------------------------------------

    with open(
        INPUT_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        for index, line in enumerate(file):

            if index >= sample_limit:
                break

            record = json.loads(line)

            shingles = create_shingles(
                record["question"],
                record["answer"]
            )

            minhash = create_minhash(
                shingles,
                num_perm
            )

            key = str(index)

            # Önceden eklenmiş olası benzer kayıtları bul.
            matches = lsh.query(minhash)

            for match in matches:

                pair = tuple(
                    sorted(
                        (
                            int(match),
                            index
                        )
                    )
                )

                candidate_pairs.add(pair)

            # Mevcut kaydı LSH indeksine ekle.
            lsh.insert(
                key,
                minhash
            )

            # Gerçek Jaccard hesabında kullanmak için sakla.
            records[index] = {
                "record": record,
                "shingles": shingles,
            }

    # --------------------------------------------------------
    # LSH ADAYLARINI GERÇEK JACCARD İLE DOĞRULA
    # --------------------------------------------------------

    verified_pairs = []

    for left, right in candidate_pairs:

        jaccard = calculate_jaccard(
            records[left]["shingles"],
            records[right]["shingles"]
        )

        if jaccard >= threshold:

            verified_pairs.append(
                (
                    left,
                    right,
                    jaccard
                )
            )

    # Jaccard değeri yüksek olanları önce göstermek için sırala.
    verified_pairs.sort(
        key=lambda item: item[2],
        reverse=True
    )

    # --------------------------------------------------------
    # GENEL SONUÇLAR
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("SONUÇ")
    print("=" * 70)

    print(
        f"Analiz edilen kayıt : {len(records)}"
    )

    print(
        f"LSH aday çifti       : {len(candidate_pairs)}"
    )

    print(
        f"Doğrulanmış >= {threshold} : "
        f"{len(verified_pairs)}"
    )

    # --------------------------------------------------------
    # İLK 5 DOĞRULANMIŞ ADAYI GÖSTER
    # --------------------------------------------------------

    print("\nİlk 5 doğrulanmış near-duplicate:\n")

    for pair_number, (left, right, jaccard) in enumerate(
        verified_pairs[:5],
        start=1
    ):

        left_record = records[left]["record"]
        right_record = records[right]["record"]

        print("-" * 70)

        print(
            f"Aday #{pair_number}"
        )

        print(
            f"Jaccard: {jaccard:.4f}"
        )

        print(
            "\nSoru A:",
            left_record["question"][:300]
        )

        print(
            "Soru B:",
            right_record["question"][:300]
        )

        print(
            "\nCevap A:",
            left_record["answer"][:500]
        )

        print(
            "Cevap B:",
            right_record["answer"][:500]
        )

        print(
            "\nKaynak A:",
            left_record["source"]
        )

        print(
            "Kaynak B:",
            right_record["source"]
        )

        print(
            "\nID A:",
            left_record["id"]
        )

        print(
            "ID B:",
            right_record["id"]
        )

    print("-" * 70)


if __name__ == "__main__":
    main()
