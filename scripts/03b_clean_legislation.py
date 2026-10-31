"""Kanun metinlerini temizler. Kurallar: reports/cleaning_rules.md

Bütün kurallar yalnızca sayfa başlıklarını siler veya boşlukları değiştirir.
Her dosya için boşluklar atıldıktan sonra karakter dizisinin özeti envanterdeki
content_sha256 ile karşılaştırılır; böylece hiçbir hukuki içerik kaybolmaz.
"""
import re
import unicodedata
from collections import Counter

from common import (
    WORD_CHARS,
    load_config,
    load_inventory,
    path_of,
    sha256_text,
    strip_whitespace,
    tr_lower,
    words,
    write_json,
)

PAGE_DATE = re.compile(r"\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}(?:\d{4})?")
PAGE_LINE = re.compile(r"^Sayfa\s+(\d+)\s*/\s*(\d+)")
SPACED_G = re.compile(rf"[{WORD_CHARS}]{{2,}} [ğĞ][{WORD_CHARS}]+")
LETTER_RUN = re.compile(rf"(?<![{WORD_CHARS}])[{WORD_CHARS}](?: [{WORD_CHARS}])+(?: [{WORD_CHARS}]+)?")
IMPOSSIBLE_ONSET = re.compile(rf"(?<![{WORD_CHARS}])([{WORD_CHARS}]+) (ş[bcçdfgğhjklmnprsştvyz][{WORD_CHARS}]*)")
WORD_PAIR = re.compile(rf"(?<![{WORD_CHARS}/(\d])([{WORD_CHARS}]+) ([{WORD_CHARS}]+)(?![{WORD_CHARS}])")
SPACED_S = re.compile(rf"\b([{WORD_CHARS}]+) ([şŞğĞ][{WORD_CHARS}]*)")


def remove_page_headers(text):
    """Tarih + 'Sayfa x / y' çiftlerini siler; eksik sayfa kabul etmez."""
    lines = text.splitlines()
    kept = []
    removed = []
    index = 0

    while index < len(lines):
        if index + 1 < len(lines):
            page = PAGE_LINE.match(lines[index + 1].strip())
            if (
                PAGE_DATE.fullmatch(lines[index].strip())
                and page
                and "mevzuat.gov.tr" in lines[index + 1]
            ):
                removed.append((int(page.group(1)), int(page.group(2))))
                index += 2
                continue
        kept.append(lines[index])
        index += 1

    total = removed[-1][1]
    if [number for number, _ in removed] != list(range(1, total + 1)):
        raise ValueError("Sayfa başlıkları eksiksiz doğrulanamadı.")

    return "\n".join(kept), len(removed)


def normalize_characters(text):
    text = unicodedata.normalize("NFC", text)
    return text.replace(" ", " ").replace("ﬂ", "fl").replace("ﬁ", "fi")


def join_spaced_g(text):
    """PDF'in 'ğ' harfinden önce eklediği boşluğu siler: 'varlı ğını'."""
    return SPACED_G.sub(lambda m: m.group().replace(" ", "", 1), text)


def join_spaced_s(text, vocabulary, prefixes):
    """'ki şi' gibi kırık kelimeleri birleştirir.

    'ş' ile başlayan gerçek kelimeler de vardır ('bu şekilde'). Bu yüzden
    yalnızca birleşik biçim korpusta ayrık biçimden daha sık geçiyorsa
    birleştirilir. Ekli biçim korpusta hiç geçmiyorsa ('ki şiyse') kelime kökü
    ile aynı başlangıcın yaygınlığına bakılır.
    """
    joined = Counter()

    def replace(match):
        left, right = match.group(1), match.group(2)
        together = tr_lower(left + right)
        # Tek başına "ş" kelime olamaz: 'verilmemi ş'.
        if vocabulary[together] > 0 and len(right) == 1:
            joined[left + right] += 1
            return left + right
        if vocabulary[together] > vocabulary[tr_lower(right)]:
            joined[left + right] += 1
            return left + right
        if vocabulary[tr_lower(right)] <= 2 and prefixes[together[:len(left) + 1]] >= 8:
            joined[left + right] += 1
            return left + right
        return match.group()

    return SPACED_S.sub(replace, text), joined


def segment(letters, vocabulary):
    """Aralıklı yazılmış harfleri en az kelimeyle sözlüğe göre böler."""
    best = {0: []}
    for end in range(1, len(letters) + 1):
        for start in range(max(0, end - 25), end):
            word = letters[start:end]
            known = vocabulary[tr_lower(word)] > 0 and (len(word) > 1 or word in "ve")
            if start in best and known:
                option = best[start] + [word]
                if end not in best or len(option) < len(best[end]):
                    best[end] = option
    return best.get(len(letters))


def collapse_letter_spacing(text, vocabulary):
    """'B u K a n u n d a' biçimindeki harf aralıklı yazımı kelimelere döndürür."""

    def replace(match):
        letters = match.group().replace(" ", "")
        words_found = segment(letters, vocabulary)
        if words_found:
            return " ".join(words_found)
        # Sözlükte yoksa ('p a r ç a l a r a') tek kelime kabul edilir.
        return letters if len(letters) <= 24 else match.group()

    return LETTER_RUN.sub(replace, text)


def join_impossible_onset(text):
    """Türkçe kelime 'şs', 'şt' gibi başlamaz: 'olunmamı şsa' tek kelimedir."""
    return IMPOSSIBLE_ONSET.sub(lambda m: m.group(1) + m.group(2), text)


def join_fragments(text, vocabulary):
    """'b aşlangıcı', 'gerçek leşmesi' gibi kelime içi boşlukları siler.

    Birleşik kelime korpusta geçiyor ve parçalardan biri nadir ya da tek
    harfse birleştirilir. İki parça da yaygın kelimeyse dokunulmaz.
    """
    joined = Counter()

    def replace(match):
        left, right = match.group(1), match.group(2)
        together = tr_lower(left + right)
        rarest = min(vocabulary[tr_lower(left)], vocabulary[tr_lower(right)])
        short_part = min(len(left), len(right)) == 1
        if vocabulary[together] >= 2 and (rarest <= 3 or short_part) and vocabulary[together] > rarest:
            joined[left + right] += 1
            return left + right
        return match.group()

    for _ in range(3):
        text = WORD_PAIR.sub(replace, text)
    return text, joined


def normalize_whitespace(text):
    """Satır içi boşlukları teke indirir, boş satırları ve kelime ortası
    satır kaymalarını kaldırır. Madde başları ve bentler satır başında kalır."""
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    lines = [re.sub(r"\( (\d{1,2}) \)", r"(\1)", line) for line in lines]
    lines = [re.sub(r"(?<=[^\s.)…]) ([,;])", r"\1", line) for line in lines]
    lines = [re.sub(r"\( (?=[A-ZÇĞİÖŞÜ])", "(", line) for line in lines]
    lines = [re.sub(r"^([IVXA-ZÇĞİÖŞÜ]{1,4}) \. ", r"\1. ", line) for line in lines]
    lines = [line for line in lines if line]

    merged = []
    for line in lines:
        starts_lower = line[0].islower()
        if merged and starts_lower and not merged[-1].endswith((".", ":", ";")):
            merged[-1] += " " + line
        else:
            merged.append(line)

    return "\n".join(merged) + "\n"


def main():
    config = load_config()
    rows = load_inventory()
    output_dir = path_of(config["paths"]["cleaned"], "legislation_v1.0")
    output_dir.mkdir(parents=True, exist_ok=True)

    stages = {}
    for row in rows:
        stem = path_of(row["raw_path"]).stem
        extracted = path_of(config["paths"]["extracted"], "legislation", f"{stem}.txt")
        text, pages = remove_page_headers(extracted.read_text(encoding="utf-8"))
        stages[row["document_id"]] = {
            "row": row,
            "stem": stem,
            "pages": pages,
            "before": text,
            "text": join_spaced_g(normalize_characters(text)),
        }

    # Sözlük boşluk onarımından sonra yeniden kurulur ki onarılan kelimeler de sayılsın.
    summary = []
    joined_total = {doc: Counter() for doc in stages}
    for _ in range(3):
        vocabulary = Counter(
            tr_lower(word)
            for stage in stages.values()
            for word in words(stage["text"])
        )
        prefixes = Counter()
        for word, count in vocabulary.items():
            for size in range(2, min(len(word), 9) + 1):
                prefixes[word[:size]] += count
        for doc, stage in stages.items():
            stage["text"], joined = join_spaced_s(stage["text"], vocabulary, prefixes)
            joined_total[doc].update(joined)

    vocabulary = Counter(
        tr_lower(word)
        for stage in stages.values()
        for word in words(stage["text"])
    )
    for doc, stage in stages.items():
        row = stage["row"]
        repaired = collapse_letter_spacing(stage["text"], vocabulary)
        repaired = join_impossible_onset(repaired)
        repaired, fragments = join_fragments(repaired, vocabulary)
        joined_total[doc].update(fragments)
        final = normalize_whitespace(repaired)

        if sha256_text(strip_whitespace(final)) != row["content_sha256"]:
            raise ValueError(f"Boşluk dışı karakter değişti: {doc}")

        (output_dir / f"{stage['stem']}.txt").write_text(final, encoding="utf-8")

        summary.append({
            "document_id": doc,
            "law_number": row["law_number"],
            "page_headers_removed": stage["pages"],
            "spaced_s_words_joined": sum(joined_total[doc].values()),
            "chars_before": len(stage["before"]),
            "chars_after": len(final),
            "lines_before": stage["before"].count("\n") + 1,
            "lines_after": final.count("\n"),
            "text_sha256": sha256_text(final),
        })
        print(
            f"{stage['stem']}: {stage['pages']} başlık, "
            f"{sum(joined_total[doc].values())} kırık kelime"
        )

    write_json(
        path_of(config["paths"]["reports"], "quality/legislation_cleaning_v1.0.json"),
        {"documents": summary},
    )


if __name__ == "__main__":
    main()
