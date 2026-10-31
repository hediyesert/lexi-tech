"""Soru-cevap havuzunu kanun metnine göre filtreler.

Girdi birebir tekrarları ayıklanmış havuzdur. Her kayıt için sorudaki ve
cevaptaki kanun-madde atıfları çözülür, atıf yapılan gerçek madde metni bulunur
ve cevap bu metinle karşılaştırılır. Elenen her kayıt nedeniyle loglanır.

Bu filtre hukuki doğruluğu kanıtlamaz; yalnızca kaynakla doğrulanamayan kayıtları
ayıklar ve insan incelemesinin yükünü azaltır.
"""
import re
from collections import Counter, defaultdict

from datasketch import MinHash, MinHashLSH

from common import (
    WORD_CHARS,
    build_article_index,
    load_config,
    path_of,
    read_jsonl,
    tr_lower,
    words,
    write_json,
    write_jsonl,
)

LAW_PATTERNS = {
    "2709": r"\b2709\s+sayılı|\bAnayasa(?:'|’)?(?:nın|ya|da|mız)?\b|\bAY\b",
    "4721": r"\b4721\s+sayılı|Türk Meden[iî] Kanunu|\bTMK\b|\bMedeni Kanun",
    "6098": r"\b6098\s+sayılı|Türk Borçlar Kanunu|\bTBK\b",
    "5237": r"\b5237\s+sayılı|Türk Ceza Kanunu|\bTCK\b",
    "5271": r"\b5271\s+sayılı|Ceza Muhakemesi Kanunu|\bCMK\b",
    "4857": r"\b4857\s+sayılı|\bİş Kanunu|\bİş K\.",
    "6102": r"\b6102\s+sayılı|Türk Ticaret Kanunu|\bTTK\b",
    "6502": r"\b6502\s+sayılı|Tüketicinin Korunması Hakkında Kanun|\bTKHK\b",
    "2577": r"\b2577\s+sayılı|İdari Yargılama Usulü Kanunu|\bİYUK\b",
    "213": r"\b213\s+sayılı|Vergi Usul Kanunu|\bVUK\b",
    "2004": r"\b2004\s+sayılı|İcra ve İflas Kanunu|\bİİK\b",
    "5510": r"\b5510\s+sayılı|Sosyal Sigortalar ve Genel Sağlık Sigortası Kanunu",
}
LAW_MENTION = [(law, re.compile(pattern)) for law, pattern in LAW_PATTERNS.items()]

# Dizinde metni bulunmayan kanunlar: atıf doğrulanamaz.
EXTERNAL_LAW = re.compile(
    r"\b(?:HMK|CGTİK|KTK|KVKK|FSEK|AATUHK|TBB|HUMK|CMUK|BK|EBK|ETCK|ETTK|PVSK|SGK Kanunu|Tebligat Kanunu)\b"
    r"|\b(?!(?:2709|4721|6098|5237|5271|4857|6102|6502|2577|213|2004|5510)\s)\d{3,4}\s+sayılı"
)
ARTICLE_MENTION = re.compile(
    r"(?i)(?:(geçici|ek|mükerrer)\s+)?"
    r"(?:madde(?:si|sinin|sinde|sine|sini)?\s*|md\.?\s*|m\.\s*)(\d{1,4})(?:/([A-Z])\b)?"
    r"|(?:(geçici|ek|mükerrer)\s+)?(\d{1,4})(?:/[0-9a-z]+)?\s*"
    r"(?:\.|'?\s*(?:inci|ıncı|uncu|üncü|nci|ncı|ncu|ncü))\s*madde"
)
LAW_THEN_NUMBER = re.compile(
    r"\b(TCK|CMK|TMK|TBK|TTK|İİK|İYUK|VUK|TKHK)(?:'?\w{0,4})?\s+(\d{1,4})(?![\d.]*\s*sayılı)\b"
)
ALIAS_TO_LAW = {
    "TCK": "5237", "CMK": "5271", "TMK": "4721", "TBK": "6098", "TTK": "6102",
    "İİK": "2004", "İYUK": "2577", "VUK": "213", "TKHK": "6502",
}

TERROR_LAW = re.compile(r"(?i)terörle mücadele|\bTMK\b[^.]{0,80}terör|terör[^.]{0,80}\bTMK\b")
CASE_NUMBER = re.compile(
    r"\b\d{4}/\d+\s*(?:E\b|K\b|Esas|Karar)|\bE\.?\s*[:,]?\s*\d{4}/\d+|\bK\.?\s*[:,]?\s*\d{4}/\d+"
)
CASE_REFERENCE = re.compile(
    r"Yargıtay|Danıştay|Anayasa Mahkemesi|\bAYM\b|\bAİHM\b|\bY?HGK\b|\bY?CGK\b|\bHD\.|\bCD\.|"
    r"içtihat|içtihad",
    re.IGNORECASE,
)
DRAFT = re.compile(r"(?i)\b(?:taslağ[ıia]|taslakta|taslak|kanun teklifi)\b")
CONTEXT = re.compile(
    r"(?i)\b(?:yukarıdaki|aşağıdaki metin|bu metin|metinde\w*|metne göre|metinden|makalede|sehven|"
    r"bu makale|bu yazı|yazıda|yazar|parçada|verilen karar|bu karar|söz konusu karar|"
    r"yapay zek|gemini|veri seti)\b"
)
WEB_ADDRESS = re.compile(
    r"(?i)\bwww\.|https?://|\.av\.tr\b|\.com\b|\.html?\b|\.php\b|\bilgili metin\s*:"
    r"|\(kaynak\s*:[^)]*(?:\w-\w|_|\.txt)|\bdosya_\d+"
)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
PHONE = re.compile(r"(?:\+?90|0)\s*\(?5\d{2}\)?[\s-]*\d{3}[\s-]*\d{2}[\s-]*\d{2}")
IBAN = re.compile(r"\bTR\d{2}[\s\d]{20,30}\b")
TCKN = re.compile(r"\b[1-9]\d{10}\b")
TRIMMED_END = re.compile(r"[.!?)\"'”’:;]\s*$")

NUMBER_WORDS = {
    "bir": 1, "iki": 2, "üç": 3, "dört": 4, "beş": 5, "altı": 6, "yedi": 7, "sekiz": 8,
    "dokuz": 9, "on": 10, "onbeş": 15, "yirmi": 20, "otuz": 30, "kırk": 40, "elli": 50,
    "altmış": 60, "yetmiş": 70, "seksen": 80, "doksan": 90, "yüz": 100,
}
NUMERIC_TERM = re.compile(
    rf"(?i)(\d+|(?:(?:on|yirmi|otuz|kırk|elli|altmış|yetmiş|seksen|doksan)\s+)?"
    rf"(?:bir|iki|üç|dört|beş|altı|yedi|sekiz|dokuz|on|yirmi|otuz|kırk|elli|altmış|"
    rf"yetmiş|seksen|doksan|yüz))\s+(gün|hafta|ay|yıl|saat)"
    rf"(?:a|e|dan|den|lık|lik|luk|lük|u|ü|ı|i|ın|in|un|ün)?\b"
)

STOPWORDS = set("""
ve veya ile ya da de ki bu şu o bir için gibi olarak olan olması olur olup ise ama
fakat ancak çünkü daha en çok az her hiç ne neden nasıl nedir mi mı mu mü kadar sonra
önce göre karşı üzerine üzerinde arasında tarafından ayrıca yani hem kendi diğer aynı
kanun kanunu kanunun madde maddesi maddesinde maddeye maddenin fıkra fıkrası bent
tck cmk tmk tbk ttk iik iyuk vuk anayasa sayılı türk hukuk hukuku hukuki hükmü durumda
durumunda halinde hâlinde gerekir gerekmektedir edilir edilmesi yapılır yapılması
vardır yoktur bulunur bulunmaktadır olabilir olmaktadır etmektedir değildir temel
""".split())


def stems(text):
    """Eklemeli yapıyı kaba biçimde gidermek için kelimenin ilk 5 harfi alınır."""
    result = set()
    for word in words(text):
        lowered = tr_lower(word)
        if len(lowered) >= 3 and lowered not in STOPWORDS:
            result.add(lowered[:5])
    return result


def numeric_terms(text):
    pairs = set()
    for match in NUMERIC_TERM.finditer(text):
        value, unit = match.group(1), tr_lower(match.group(2))
        if value.isdigit():
            number = int(value)
        else:
            number = sum(NUMBER_WORDS.get(tr_lower(part), 0) for part in value.split())
        pairs.add((number, unit))
    return pairs


def valid_tckn(digits):
    values = [int(d) for d in digits]
    tenth = (sum(values[0:9:2]) * 7 - sum(values[1:8:2])) % 10
    return tenth == values[9] and sum(values[:10]) % 10 == values[10]


def has_personal_data(text):
    if EMAIL.search(text) or PHONE.search(text) or IBAN.search(text):
        return True
    return any(valid_tckn(m) for m in TCKN.findall(text))


def find_laws(text):
    mentions = []
    for law, pattern in LAW_MENTION:
        mentions.extend((match.start(), match.end(), law) for match in pattern.finditer(text))
    return sorted(mentions)


def resolve_citations(text):
    """Metindeki (kanun, madde) atıflarını çözer.

    Madde, en yakın önceki kanun adına bağlanır; yoksa yakın sonraki ada;
    o da yoksa metinde tek kanun geçiyorsa ona.
    """
    laws = find_laws(text)
    distinct = {law for _, _, law in laws}
    citations = set()

    for match in LAW_THEN_NUMBER.finditer(text):
        citations.add((ALIAS_TO_LAW[match.group(1)], match.group(2)))

    for match in ARTICLE_MENTION.finditer(text):
        prefix = match.group(1) or match.group(4) or ""
        number = match.group(2) or match.group(5)
        letter = match.group(3)
        key = {"": "", "geçici": "G", "ek": "E", "mükerrer": "M"}[tr_lower(prefix)]
        key += str(int(number)) + (f"/{letter}" if letter else "")

        before = [m for m in laws if m[1] <= match.start() and match.start() - m[1] <= 80]
        after = [m for m in laws if m[0] >= match.end() and m[0] - match.end() <= 40]

        if before:
            citations.add((before[-1][2], key))
        elif after:
            citations.add((after[0][2], key))
        elif len(distinct) == 1:
            citations.add((next(iter(distinct)), key))

    return citations


def normalize_question(text):
    return " ".join(words(tr_lower(text)))


def main():
    config = load_config()
    settings = config["instruction"]
    documents = list(read_jsonl(path_of(config["paths"]["final"], "domain_corpus_v1.0.jsonl")))
    index = {d["law_number"]: build_article_index(d) for d in documents}
    article_stems = {
        (law, key): stems(article["caption"] + " " + article["text"])
        for law, articles in index.items()
        for key, article in articles.items()
    }
    article_numbers = {
        (law, key): numeric_terms(article["text"])
        for law, articles in index.items()
        for key, article in articles.items()
    }

    reasons = Counter()
    exclusions = []
    candidates = []

    def reject(record, reason):
        reasons[reason] += 1
        exclusions.append({"id": record["id"], "source": record["source"], "reason": reason})

    total = 0
    scores = []
    for record in read_jsonl(path_of("data/deduplicated/exact_unique.jsonl")):
        total += 1
        question, answer = record["question"], record["answer"]
        combined = question + " " + answer

        if (
            len(question) < settings["min_question_chars"]
            or len(answer) < settings["min_answer_chars"]
        ):
            reject(record, "too_short")
            continue
        if len(answer) > settings["max_answer_chars"]:
            reject(record, "too_long")
            continue
        if not TRIMMED_END.search(answer):
            reject(record, "truncated_answer")
            continue
        if WEB_ADDRESS.search(combined):
            reject(record, "source_artifact")
            continue
        if has_personal_data(combined):
            reject(record, "personal_data")
            continue
        if DRAFT.search(combined):
            reject(record, "draft_legislation")
            continue
        if CONTEXT.search(question) or CONTEXT.search(answer):
            reject(record, "context_dependent")
            continue
        if CASE_NUMBER.search(combined) or CASE_REFERENCE.search(combined):
            reject(record, "unverifiable_case_law")
            continue
        if EXTERNAL_LAW.search(combined):
            reject(record, "law_outside_corpus")
            continue

        # TMK burada Terörle Mücadele Kanunu demektir, Medeni Kanun değil.
        if TERROR_LAW.search(combined):
            reject(record, "law_outside_corpus")
            continue

        citations = resolve_citations(combined)
        if not citations:
            reject(record, "no_resolvable_citation")
            continue

        missing = [c for c in citations if c not in article_stems]
        if missing:
            reject(record, "article_not_found")
            continue

        if any(index[l][k]["text"].find("Mülga", 0, 80) >= 0 for l, k in citations):
            reject(record, "repealed_article")
            continue

        source_stems = set().union(*(article_stems[c] for c in citations))
        answer_stems = stems(answer)
        if len(answer_stems) < 5:
            reject(record, "too_short")
            continue

        evidence = len(answer_stems & source_stems) / len(answer_stems)
        scores.append(evidence)
        if evidence < settings["min_evidence_score"]:
            reject(record, "low_evidence")
            continue

        allowed = set().union(*(article_numbers[c] for c in citations)) | numeric_terms(question)
        if numeric_terms(answer) - allowed:
            reject(record, "numeric_mismatch")
            continue

        candidates.append({
            "id": record["id"],
            "source": record["source"],
            "source_file": record.get("source_document"),
            "question": question,
            "answer": answer,
            "citations": sorted(f"{law}:{key}" for law, key in citations),
            "evidence_score": round(evidence, 4),
        })

    print("Girdi:", total, "Ön aday:", len(candidates))

    # Aynı sorunun farklı cevapları: kanıt skoru en yüksek olan kalır.
    best = {}
    for record in candidates:
        key = normalize_question(record["question"])
        best.setdefault(key, []).append(record)
    kept = []
    for group in best.values():
        group.sort(key=lambda r: (-r["evidence_score"], r["id"]))
        kept.append(group[0])
        for record in group[1:]:
            reject(record, "alternative_answer")
    candidates = kept

    # Yakın tekrar: yalnızca soru metni, gerçek Jaccard ile doğrulanır.
    dedup = config["deduplication"]["minhash"]
    size = dedup["shingle_words"]
    shingles = {}
    lsh = MinHashLSH(threshold=dedup["threshold"], num_perm=dedup["num_perm"])
    parent = {}

    def find(item):
        while parent.setdefault(item, item) != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    pairs = 0
    for record in candidates:
        tokens = normalize_question(record["question"]).split()
        current = {
            " ".join(tokens[i:i + size]) for i in range(max(1, len(tokens) - size + 1))
        }
        signature = MinHash(num_perm=dedup["num_perm"])
        for shingle in current:
            signature.update(shingle.encode("utf-8"))
        for other in lsh.query(signature):
            jaccard = len(current & shingles[other]) / len(current | shingles[other])
            if jaccard >= dedup["threshold"]:
                pairs += 1
                parent[find(record["id"])] = find(other)
        lsh.insert(record["id"], signature)
        shingles[record["id"]] = current

    clusters = defaultdict(list)
    for record in candidates:
        clusters[find(record["id"])].append(record)

    final = []
    for group in clusters.values():
        group.sort(key=lambda r: (-r["evidence_score"], r["id"]))
        final.append(group[0])
        for record in group[1:]:
            reject(record, "near_duplicate")

    final.sort(key=lambda r: r["id"])
    write_jsonl(path_of("data/interim/instruction_candidates_v1.0.jsonl"), final)
    write_jsonl(path_of("data/interim/instruction_exclusions_v1.0.jsonl"), exclusions)

    write_json(path_of(config["paths"]["reports"], "quality/instruction_filter_v1.0.json"), {
        "input_records": total,
        "output_candidates": len(final),
        "exclusion_reasons": dict(reasons.most_common()),
        "question_near_duplicate_pairs": pairs,
        "min_evidence_score": settings["min_evidence_score"],
        "candidates_by_source": dict(Counter(r["source"] for r in final)),
        "evidence_score_quantiles": {
            q: sorted(scores)[int(len(scores) * q)] for q in (0.1, 0.25, 0.5, 0.75, 0.9)
        },
    })
    print("Aday:", len(final))
    print(reasons.most_common())


if __name__ == "__main__":
    main()
