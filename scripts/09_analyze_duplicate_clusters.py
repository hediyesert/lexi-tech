from pathlib import Path
from collections import Counter
import json


PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_PATH = (
    PROJECT_ROOT
    / "reports"
    / "deduplication"
    / "near_duplicate_candidates.jsonl"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "reports"
    / "deduplication"
    / "near_duplicate_cluster_summary.json"
)


class UnionFind:
    def __init__(self):
        self.parent = {}
        self.rank = {}

    def add(self, item):
        if item not in self.parent:
            self.parent[item] = item
            self.rank[item] = 0

    def find(self, item):
        if self.parent[item] != item:
            self.parent[item] = self.find(
                self.parent[item]
            )

        return self.parent[item]

    def union(self, left, right):
        self.add(left)
        self.add(right)

        root_left = self.find(left)
        root_right = self.find(right)

        if root_left == root_right:
            return

        if self.rank[root_left] < self.rank[root_right]:
            root_left, root_right = (
                root_right,
                root_left
            )

        self.parent[root_right] = root_left

        if self.rank[root_left] == self.rank[root_right]:
            self.rank[root_left] += 1


def main():

    union_find = UnionFind()

    total_pairs = 0

    with open(
        INPUT_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        for line in file:

            record = json.loads(line)

            left_id = record["left"]["id"]
            right_id = record["right"]["id"]

            union_find.union(
                left_id,
                right_id
            )

            total_pairs += 1

    clusters = {}

    for record_id in union_find.parent:

        root = union_find.find(record_id)

        clusters.setdefault(
            root,
            []
        ).append(record_id)

    cluster_sizes = [
        len(members)
        for members in clusters.values()
    ]

    size_distribution = Counter(
        cluster_sizes
    )

    total_records = sum(cluster_sizes)

    largest_cluster = (
        max(cluster_sizes)
        if cluster_sizes
        else 0
    )

    potential_removals = sum(
        size - 1
        for size in cluster_sizes
    )

    summary = {
        "verified_near_duplicate_pairs": total_pairs,
        "unique_records_in_clusters": total_records,
        "cluster_count": len(clusters),
        "largest_cluster_size": largest_cluster,
        "potential_removals_if_one_record_kept_per_cluster": (
            potential_removals
        ),
        "cluster_size_distribution": {
            str(size): count
            for size, count in sorted(
                size_distribution.items()
            )
        },
    }

    with open(
        OUTPUT_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            summary,
            file,
            ensure_ascii=False,
            indent=2
        )

    print("=" * 70)
    print("NEAR-DUPLICATE CLUSTER ANALİZİ")
    print("=" * 70)

    print(
        f"Doğrulanmış çift              : {total_pairs}"
    )

    print(
        f"Cluster içindeki unique kayıt : {total_records}"
    )

    print(
        f"Toplam cluster                : {len(clusters)}"
    )

    print(
        f"En büyük cluster              : {largest_cluster} kayıt"
    )

    print(
        "Her cluster'dan 1 kayıt tutulursa "
        f"potansiyel çıkarılacak kayıt : {potential_removals}"
    )

    print("\nCluster boyut dağılımı:")

    for size, count in sorted(
        size_distribution.items()
    ):
        print(
            f"{size} kayıtlı cluster : {count}"
        )

    print(
        f"\nÖzet rapor: {OUTPUT_PATH}"
    )

    print(
        "\nNOT: Bu analiz hiçbir kaydı silmedi."
    )


if __name__ == "__main__":
    main()
