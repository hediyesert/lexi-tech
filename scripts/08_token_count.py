"""Domain ve instruction dosyalarının token dağılımını hesaplar."""
from statistics import mean, median

from transformers import AutoTokenizer

from common import load_config, path_of, read_jsonl, write_json


def distribution(values):
    ordered = sorted(values)
    return {
        "count": len(ordered),
        "total": sum(ordered),
        "min": ordered[0],
        "median": median(ordered),
        "mean": round(mean(ordered), 1),
        "p95": ordered[int(len(ordered) * 0.95)],
        "max": ordered[-1],
    }


def main():
    config = load_config()
    final_dir = path_of(config["paths"]["final"])
    tokenizer = AutoTokenizer.from_pretrained(config["tokenizer"], use_fast=True)

    def count(text):
        return len(tokenizer.encode(text, add_special_tokens=False, truncation=False))

    documents = list(read_jsonl(final_dir / "domain_corpus_v1.0.jsonl"))
    chunks = [
        record
        for split in ("train", "validation", "test")
        for record in read_jsonl(final_dir / f"{split}.jsonl")
    ]
    examples = list(read_jsonl(final_dir / "instruction_v1.0.jsonl"))

    report = {
        "tokenizer": config["tokenizer"],
        "domain_documents": distribution([d["token_count"] for d in documents]),
        "domain_training_chunks": distribution([c["token_count"] for c in chunks]),
        "domain_chunks_by_split": {
            split: sum(c["token_count"] for c in chunks if c["split"] == split)
            for split in ("train", "validation", "test")
        },
        "instruction_questions": distribution([count(e["instruction"]) for e in examples]),
        "instruction_responses": distribution([count(e["response"]) for e in examples]),
    }
    write_json(path_of(config["paths"]["reports"], "statistics/token_statistics_v1.0.json"), report)
    print(report)


if __name__ == "__main__":
    main()
