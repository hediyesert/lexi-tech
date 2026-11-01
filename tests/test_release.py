"""Teslim dosyalarının otomatik kalite kuralları: pytest tests/"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from common import build_article_index, read_jsonl, words  # noqa: E402

SPLITS = ("train", "validation", "test")
FINAL = ROOT / "data/final"
REQUIRED_DOCUMENT_FIELDS = {
    "document_id", "title", "source", "url", "language", "document_type",
    "publication_year", "subtopic", "char_count", "token_count", "text",
}
REQUIRED_EXAMPLE_FIELDS = {
    "id", "messages", "source_document", "task_type", "instruction", "response",
    "generation_method", "verified_by", "verified",
}


@pytest.fixture(scope="module")
def documents():
    return list(read_jsonl(FINAL / "domain_corpus_v1.0.jsonl"))


@pytest.fixture(scope="module")
def chunks():
    return [c for s in SPLITS for c in read_jsonl(FINAL / f"{s}.jsonl")]


@pytest.fixture(scope="module")
def examples():
    return list(read_jsonl(FINAL / "instruction_v1.0.jsonl"))


def shingles(text, size=3):
    tokens = [w.lower() for w in words(text)]
    return {" ".join(tokens[i:i + size]) for i in range(max(1, len(tokens) - size + 1))}


def bad_char_ratio(text):
    return sum(c == "�" or ord(c) < 9 for c in text) / len(text)


def test_document_metadata_is_complete(documents):
    assert len(documents) == 12
    for document in documents:
        missing = [f for f in REQUIRED_DOCUMENT_FIELDS if not document.get(f)]
        assert not missing, (document["document_id"], missing)
        assert "MevzuatNo=" + document["law_number"] in document["url"]


def test_chunk_ids_are_unique_and_within_limit(chunks):
    assert len({c["chunk_id"] for c in chunks}) == len(chunks)
    assert all(0 < c["token_count"] <= 2048 for c in chunks)
    assert all(c["section_type"] != "amendment_table" for c in chunks)
    assert all(bad_char_ratio(c["text"]) == 0 for c in chunks)


def test_documents_do_not_cross_domain_splits(chunks):
    owners = {}
    for chunk in chunks:
        owners.setdefault(chunk["document_id"], set()).add(chunk["split"])
    assert all(len(found) == 1 for found in owners.values())


def test_no_exact_chunk_crosses_splits(chunks):
    owners = {}
    for chunk in chunks:
        owners.setdefault(chunk["text"], set()).add(chunk["split"])
    assert all(len(found) == 1 for found in owners.values())


def test_no_page_headers_or_spaced_letters_remain(chunks):
    text = "\n".join(c["text"] for c in chunks)
    assert not re.search(r"Sayfa \d+ / \d+", text)
    assert "mevzuat.gov.tr/anasayfa" not in text
    assert not re.search(r"\bki şi|\bBa şbakan|\bili şkin\b", text)


def test_example_schema(examples):
    assert 3000 <= len(examples) <= 5000
    assert len({e["id"] for e in examples}) == len(examples)
    for example in examples:
        assert REQUIRED_EXAMPLE_FIELDS <= set(example)
        roles = [m["role"] for m in example["messages"]]
        assert roles == ["user", "assistant"]
        assert example["messages"][0]["content"] == example["instruction"]
        assert example["messages"][1]["content"] == example["response"]
        assert example["instruction"].strip() and example["response"].strip()
        assert bad_char_ratio(example["response"]) == 0


def test_example_lengths_are_reasonable(examples):
    for example in examples:
        assert 8 <= len(example["instruction"]) <= 1500, example["id"]
        assert 30 <= len(example["response"]) <= 3000, example["id"]


def test_sourced_examples_keep_their_source(examples):
    for example in examples:
        assert example["origin"].get("dataset"), example["id"]
        if example["origin"]["dataset"] not in ("lexitech", "mevzuat"):
            assert example["source_document"], example["id"]
            assert example["source_articles"], example["id"]
            assert example["origin"].get("record_id"), example["id"]


def test_flags_never_claim_human_approval(examples, chunks):
    assert all(e["verified"] is False and e["verified_by"] is None for e in examples)
    assert all(e["training_approved"] is False for e in examples)
    assert all(c["training_approved"] is False for c in chunks)


def test_questions_are_unique(examples):
    counts = Counter(" ".join(e["instruction"].lower().split()) for e in examples)
    assert counts.most_common(1)[0][1] == 1


def test_source_files_do_not_cross_splits(examples):
    owners = {}
    for example in examples:
        name = example["origin"].get("file")
        if name:
            owners.setdefault(name, set()).add(example["split"])
    assert all(len(found) == 1 for found in owners.values())


def test_articles_do_not_cross_splits(examples):
    owners = {}
    for example in examples:
        for article in example["source_articles"]:
            owners.setdefault(article, set()).add(example["split"])
    assert not [a for a, found in owners.items() if len(found) > 1]


def test_cited_articles_exist(examples, documents):
    index = {d["law_number"]: build_article_index(d) for d in documents}
    for example in examples:
        for citation in example["source_articles"]:
            law, key = citation.split(":")
            assert key in index[law]


def test_no_question_near_duplicate_crosses_splits(examples):
    # Sınır şablonları ('TCK m. 400 neyi düzenler?') bilgi taşımaz; yalnızca
    # kaynak veri setinden gelen sorular karşılaştırılır.
    sourced = [e for e in examples if e["origin"]["dataset"] != "lexitech"]
    held_out = [e for e in sourced if e["split"] != "train"]
    train = [(e, shingles(e["instruction"])) for e in sourced if e["split"] == "train"]
    conflicts = []
    for example in held_out:
        current = shingles(example["instruction"])
        for other, other_shingles in train:
            union = current | other_shingles
            if len(current & other_shingles) / len(union) >= 0.85:
                conflicts.append((example["id"], other["id"]))
    assert not conflicts


def test_task_balance(examples):
    counts = Counter(e["task_type"] for e in examples)
    assert max(counts.values()) / len(examples) <= 0.25
    assert counts["bilgi_yetersizligi"] > 0 and counts["alan_disi"] > 0


def test_split_files_match_combined_file(examples):
    for split in SPLITS:
        rows = list(read_jsonl(FINAL / "instruction_v1.0" / f"{split}.jsonl"))
        assert len(rows) == sum(e["split"] == split for e in examples)
        assert json.dumps(rows[0], ensure_ascii=False)
