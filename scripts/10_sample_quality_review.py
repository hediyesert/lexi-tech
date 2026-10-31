"""Manuel kalite kontrolü için rastgele örneklem çeker.

Mevcut örneklem dosyaları üzerine yazılmaz: inceleme kayıtları korunur.
"""
import csv
import random

from common import load_config, path_of, read_jsonl


def write_sample(path, fieldnames, rows):
    if path.exists():
        print("Örneklem zaten var, korunuyor:", path)
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print("Yazıldı:", path, len(rows))


def main():
    config = load_config()
    seed = config["project"]["random_seed"]
    review = config["quality_review"]
    final_dir = path_of(config["paths"]["final"])
    output_dir = path_of(config["paths"]["reports"], "quality")
    rng = random.Random(seed)

    chunks = [
        record
        for split in ("train", "validation", "test")
        for record in read_jsonl(final_dir / f"{split}.jsonl")
    ]
    columns = [
        "readable", "in_domain", "extraction_ok", "header_footer_clean",
        "no_broken_chars", "metadata_ok",
    ]
    domain_rows = [
        {
            "chunk_id": c["chunk_id"],
            "law_number": c["law_number"],
            "split": c["split"],
            "text_start": c["text"][:300].replace("\n", " / "),
            "text_end": c["text"][-200:].replace("\n", " / "),
            **{f"assistant_{name}": "" for name in columns},
            "assistant_note": "",
            **{f"human_{name}": "" for name in columns},
            "human_reviewer": "",
        }
        for c in rng.sample(chunks, review["domain_sample"])
    ]
    write_sample(
        output_dir / "qc_domain_sample_v1.0.csv", list(domain_rows[0].keys()), domain_rows
    )

    examples = list(read_jsonl(final_dir / "instruction_v1.0.jsonl"))
    rows = [
        {
            "id": e["id"],
            "split": e["split"],
            "task_type": e["task_type"],
            "source_articles": ";".join(e["source_articles"]),
            "instruction": e["instruction"],
            "response": e["response"],
            "assistant_verdict": "",
            "assistant_task_ok": "",
            "assistant_note": "",
            "human_clear_instruction": "",
            "human_matches_source": "",
            "human_answers_instruction": "",
            "human_task_type_ok": "",
            "human_reviewer": "",
        }
        for e in rng.sample(examples, review["instruction_sample"])
    ]
    write_sample(output_dir / "qc_instruction_sample_v1.0.csv", list(rows[0].keys()), rows)


if __name__ == "__main__":
    main()
