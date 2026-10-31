"""Vize istatistik raporunu ve temizleme öncesi-sonrası örneklerini üretir."""
import json
import re
from collections import Counter

from common import load_config, load_inventory, path_of, read_jsonl, write_json


def tr_number(value):
    return f"{value:,}".replace(",", ".")


def percent(part, whole):
    return f"%{100 * part / whole:.1f}".replace(".", ",")


def line_count(path):
    with path.open(encoding="utf-8") as f:
        return sum(1 for _ in f)


def table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def load_report(config, name):
    return json.loads(path_of(config["paths"]["reports"], name).read_text(encoding="utf-8"))


def cleaning_examples(config):
    """Gerçek metinden öncesi-sonrası örnekleri çıkarır."""
    sections = []
    final_dir = path_of(config["paths"]["cleaned"], "legislation_v1.0")
    extracted_dir = path_of(config["paths"]["extracted"], "legislation")

    for row in load_inventory():
        stem = path_of(row["raw_path"]).stem
        before = (extracted_dir / f"{stem}.txt").read_text(encoding="utf-8")
        after = (final_dir / f"{stem}.txt").read_text(encoding="utf-8")
        title = f"{row['law_name']} ({row['law_number']})"

        page = re.search(r"[^\n]*\n[^\n]*\n\d{2}\.\d{2}\.\d{4} [^\n]*\nSayfa \d+ / \d+[^\n]*\n[^\n]*", before)
        if page:
            lines = page.group().split("\n")
            anchor = " ".join(lines[1].split()) or " ".join(lines[0].split())
            kept = next((line for line in after.split("\n") if anchor in line), anchor)
            sections.append((title, "Sayfa başlığı", page.group(), kept[:400]))

        broken = re.search(r"[^\n]*\b\w+ [şğ]\w+[^\n]*", before)
        for match in re.finditer(r"[^\n]*\b(\w{2,}) (ş\w+)[^\n]*", before):
            joined = match.group(1) + match.group(2)
            if joined in after and f"{match.group(1)} {match.group(2)}" not in after:
                broken = match
                break
        if broken and len(sections) < 24:
            line = broken.group().strip()
            words = re.findall(r"\S+", line)
            fixed = next(
                (
                    candidate
                    for candidate in after.split("\n")
                    if "".join(words[2:6]) in "".join(candidate.split())
                ),
                None,
            )
            if fixed:
                sections.append((title, "Kırık kelime ve satır birleştirme", line, fixed[:400]))

    lines = [
        "# Temizleme öncesi-sonrası örnekleri",
        "",
        "Tüm örnekler `09_statistics.py` tarafından gerçek metinden çıkarılır.",
        "",
    ]
    for number, (title, kind, old, new) in enumerate(sections, start=1):
        lines += [
            f"## {number}. {title}: {kind}",
            "",
            "```text",
            "--- ÖNCE ---",
            old,
            "",
            "--- SONRA ---",
            new,
            "```",
            "",
        ]
    path_of(config["paths"]["reports"], "cleaning_examples_v1.0.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return len(sections)


def main():
    config = load_config()
    final_dir = path_of(config["paths"]["final"])
    documents = list(read_jsonl(final_dir / "domain_corpus_v1.0.jsonl"))
    examples = list(read_jsonl(final_dir / "instruction_v1.0.jsonl"))
    chunks = [
        record
        for split in ("train", "validation", "test")
        for record in read_jsonl(final_dir / f"{split}.jsonl")
    ]

    extraction = load_report(config, "statistics/legislation_extraction_v1.0.json")
    build = load_report(config, "statistics/domain_build_v1.0.json")
    instruction = load_report(config, "statistics/instruction_build_v1.0.json")
    filtering = load_report(config, "quality/instruction_filter_v1.0.json")
    tokens = load_report(config, "statistics/token_statistics_v1.0.json")
    cleaning = load_report(config, "quality/legislation_cleaning_v1.0.json")

    raw_counts = {
        "sinanelms/hukukisorular": line_count(path_of("data/raw/sinanelms__hukukisorular/train.jsonl")),
        "OrionCAF/turkish_law_qa_dataset": line_count(path_of("data/raw/OrionCAF__turkish_law_qa_dataset/train.jsonl")),
    }
    raw_total = sum(raw_counts.values())
    unique_total = line_count(path_of("data/deduplicated/exact_unique.jsonl"))
    cleaned_total = sum(
        line_count(path)
        for path in path_of(config["paths"]["cleaned"]).glob("*/train.jsonl")
    )

    words_total = sum(d["word_count"] for d in documents)
    chunk_languages = Counter(c["language"] for c in chunks)
    subtopics = Counter()
    for chunk in chunks:
        subtopics[chunk["subtopic"]] += chunk["token_count"]
    largest_doc = max(documents, key=lambda d: d["token_count"])
    reasons = filtering["exclusion_reasons"]

    summary = {
        "sources": 3,
        "domain": {
            "raw_documents": len(documents),
            "extraction_failed": extraction["documents_failed"],
            "pages": extraction["pages_total"],
            "final_documents": len(documents),
            "words": words_total,
            "tokens": tokens["domain_documents"]["total"],
            "training_tokens": tokens["domain_training_chunks"]["total"],
            "training_chunks": len(chunks),
            "chunks_by_split": build["chunks_by_split"],
            "excluded_chunks": build["chunks_excluded"],
            "turkish_chunk_share": chunk_languages["tr"] / len(chunks),
            "spaced_words_repaired": sum(d["spaced_s_words_joined"] for d in cleaning["documents"]),
        },
        "instruction": {
            "raw_records": raw_total,
            "raw_by_source": raw_counts,
            "cleaned": cleaned_total,
            "exact_unique": unique_total,
            "exact_duplicates": cleaned_total - unique_total,
            "after_kb_filter": filtering["output_candidates"],
            "final_examples": len(examples),
            "by_split": instruction["by_split"],
            "by_task": instruction["by_task"],
            "by_origin": instruction["by_origin"],
            "by_method": instruction["by_method"],
            "by_law": instruction["by_law"],
        },
    }
    write_json(path_of(config["paths"]["reports"], "statistics/summary_v1.0.json"), summary)

    example_count = cleaning_examples(config)

    d, i = summary["domain"], summary["instruction"]
    task_labels = {
        "usul_sure": ("Usul ve süre", "Başvuru yolu, süre ve görevli mahkemeyi söyler"),
        "kosul_unsur": ("Koşul ve unsur", "Bir kurumun şartlarını veya suçun unsurlarını sıralar"),
        "tanim_aciklama": ("Tanım ve açıklama", "Bir kavramı açıklar"),
        "madde_bulma": ("Madde bulma", "Konunun hangi kanun maddesinde olduğunu gösterir"),
        "hukuki_sonuc": ("Hukuki sonuç", "Bir durumun doğurduğu sonucu açıklar"),
        "karsilastirma": ("Karşılaştırma", "İki kurumu karşılaştırır"),
        "olay_uygulama": ("Olaya uygulama", "Hükmü verilen olaya uygular"),
        "neden_sonuc": ("Neden-sonuç", "Bir kuralın amacını veya nedenini açıklar"),
        "bilgi_yetersizligi": ("Bilgi yetersizliği", "Doğrulanamayan soruda sınırını bildirir"),
        "yaptirim": ("Yaptırım", "Öngörülen cezayı veya yaptırımı söyler"),
        "alan_disi": ("Alan dışı", "Hukuk dışı soruyu reddeder"),
        "madde_aciklama": ("Madde açıklama", "Bir maddenin içeriğini açıklar"),
    }

    report = [
        "# LexiTech TR — İstatistik Raporu v1.0-rc1",
        "",
        "Bu dosya `scripts/09_statistics.py` ile üretilir, elle düzenlenmez.",
        "",
        "## Sayısal özet",
        "",
        table(["Özellik", "Değer"], [
            ["Veri kaynağı sayısı", summary["sources"]],
            ["Ham kanun dokümanı (PDF)", d["raw_documents"]],
            ["Extraction başarılı / başarısız", f"{d['raw_documents'] - d['extraction_failed']} / {d['extraction_failed']}"],
            ["Final kanun dokümanı", d["final_documents"]],
            ["Toplam kelime (domain)", tr_number(d["words"])],
            ["Toplam token (domain)", tr_number(d["tokens"])],
            ["Eğitime giren token (domain)", tr_number(d["training_tokens"])],
            ["Eğitim chunk'ı", tr_number(d["training_chunks"])],
            ["Türkçe chunk oranı", percent(chunk_languages["tr"], len(chunks))],
            ["Ham soru-cevap kaydı", tr_number(raw_total)],
            ["Birebir tekrar", tr_number(i["exact_duplicates"])],
            ["Kanun metniyle desteklenen aday", tr_number(i["after_kb_filter"])],
            ["Final instruction örneği", tr_number(i["final_examples"])],
        ]),
        "",
        "## Verinin aşamalar boyunca erimesi",
        "",
        "### Domain Corpus",
        "",
        table(["Aşama", "Birim", "Sayı"], [
            ["Ham PDF", "doküman", d["raw_documents"]],
            ["Extraction sonrası", "doküman", d["raw_documents"] - d["extraction_failed"]],
            ["Temizleme sonrası", "doküman", d["final_documents"]],
            ["Chunk üretimi", "chunk", d["training_chunks"] + sum(d["excluded_chunks"].values())],
            ["Değişiklik tabloları çıkarıldıktan sonra", "chunk", d["training_chunks"]],
        ]),
        "",
        "### Instruction Dataset",
        "",
        table(["Aşama", "Kayıt"], [
            ["Ham", tr_number(raw_total)],
            ["Temizleme sonrası", tr_number(cleaned_total)],
            ["Birebir tekrar ayıklama sonrası", tr_number(unique_total)],
            ["Kanun metni filtresi ve yakın tekrar sonrası", tr_number(i["after_kb_filter"])],
            ["Görev dengeli seçim + kanundan üretilen + sınır örnekleri", tr_number(i["final_examples"])],
        ]),
        "",
        "## Çıkarma nedenleri (instruction)",
        "",
        table(["Neden", "Kayıt"], [[k, tr_number(v)] for k, v in reasons.items()]),
        "",
        "## Görev türü dağılımı",
        "",
        table(["Görev türü", "Ne yapar", "Örnek", "Oran"], [
            [task_labels[k][0], task_labels[k][1], tr_number(v), percent(v, len(examples))]
            for k, v in i["by_task"].items()
        ]),
        "",
        "## Instruction split",
        "",
        table(["Küme", "Örnek"], [[k, tr_number(v)] for k, v in sorted(i["by_split"].items())]),
        "",
        "## Kanun dağılımı (instruction, ilk atıf)",
        "",
        table(["Kanun", "Örnek"], [[k, tr_number(v)] for k, v in i["by_law"].items()]),
        "",
        "## Alt konu dağılımı (domain, eğitim tokenı)",
        "",
        table(["Alt konu", "Token", "Oran"], [
            [k, tr_number(v), percent(v, tokens["domain_training_chunks"]["total"])]
            for k, v in subtopics.most_common()
        ]),
        "",
        f"En büyük doküman {largest_doc['title']}: toplam tokenın "
        f"{percent(largest_doc['token_count'], tokens['domain_documents']['total'])} kadarı.",
        "",
        "## Token dağılımı",
        "",
        table(["Ölçüt", "Adet", "Toplam", "Min", "Medyan", "Ortalama", "P95", "Maks"], [
            [name, tr_number(s["count"]), tr_number(s["total"]), s["min"], s["median"], s["mean"], s["p95"], s["max"]]
            for name, s in [
                ("Kanun dokümanı", tokens["domain_documents"]),
                ("Eğitim chunk'ı", tokens["domain_training_chunks"]),
                ("Instruction soru", tokens["instruction_questions"]),
                ("Instruction cevap", tokens["instruction_responses"]),
            ]
        ]),
        "",
        f"Tokenizer: `{tokens['tokenizer']}`.",
        "",
    ]
    path_of(config["paths"]["reports"], "statistics/statistics_report_v1.0.md").write_text(
        "\n".join(report), encoding="utf-8"
    )
    print("Rapor yazıldı, temizleme örneği:", example_count)


if __name__ == "__main__":
    main()
