"""Kalite kontrol raporunu üretir: reports/quality/quality_control_report_v1.0.md

Asistan ön incelemesi ile insan incelemesi ayrı sayılır. İnsan sütunları boşsa
rapor bunu açıkça söyler; asistan sonucu insan onayı yerine geçmez.
"""
import csv
import json
from collections import Counter

from common import load_config, path_of

DOMAIN_CHECKS = [
    ("readable", "Okunabilir metin"),
    ("in_domain", "Doğru domain"),
    ("extraction_ok", "Extraction doğru"),
    ("header_footer_clean", "Header/footer temiz"),
    ("no_broken_chars", "Bozuk karakter yok"),
    ("metadata_ok", "Metadata doğru"),
]


def read_csv(path):
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def rate(rows, column):
    filled = [r for r in rows if r.get(column)]
    if not filled:
        return "yapılmadı"
    passed = sum(r[column] == "yes" for r in filled)
    return f"{passed}/{len(filled)} (%{100 * passed / len(filled):.1f})".replace(".", ",")


def main():
    config = load_config()
    quality = path_of(config["paths"]["reports"], "quality")
    domain = read_csv(quality / "qc_domain_sample_v1.0.csv")
    domain_round_one = read_csv(quality / "qc_domain_assistant_round1_v1.0.csv")
    instruction = read_csv(quality / "qc_instruction_sample_v1.0.csv")
    round_one = read_csv(quality / "qc_assistant_round1_v1.0.csv")
    round_two = read_csv(quality / "qc_assistant_round2_v1.0.csv")
    filtering = json.loads((quality / "instruction_filter_v1.0.json").read_text(encoding="utf-8"))

    verdicts = Counter(r["assistant_verdict"] for r in round_one)
    human_domain = sum(bool(r["human_reviewer"]) for r in domain)
    human_instruction = sum(bool(r["human_reviewer"]) for r in instruction)
    task_ok = sum(r["assistant_task_ok"] == "yes" for r in round_one)

    lines = [
        "# LexiTech TR — Kalite Kontrol Raporu v1.0-rc1",
        "",
        "Bu dosya `scripts/11_quality_report.py` ile üretilir.",
        "",
        "## İnceleme durumu",
        "",
        "| İnceleme | Örnek | Durum |",
        "|---|---|---|",
        f"| Domain, asistan ön incelemesi | {len(domain_round_one)} | Tamamlandı. Yalnızca chunk başı ve sonu görüldü |",
        f"| Domain, insan incelemesi | {len(domain)} | {human_domain} tamamlandı |",
        f"| Instruction, asistan ön incelemesi | {len(round_one)} | Tamamlandı. Kaynaklı kayıtlar, ilk 230 karakter |",
        f"| Instruction, insan incelemesi | {len(instruction)} | {human_instruction} tamamlandı |",
        "",
        "**Asistan ön incelemesi insan veya hukukçu onayı değildir.** "
        "Bu yüzden tüm kayıtlarda `verified=false` ve `training_approved=false` kalır.",
        "",
        "## Domain Corpus: ilk tur sonuçları",
        "",
        "Asistan turu temizleme düzeltilmeden önceki 150 chunk üzerindedir "
        "(`qc_domain_assistant_round1_v1.0.csv`). İnsan incelemesi güncel veriden çekilen ayrı 150 chunk içindir.",
        "",
        "| Kontrol | Asistan | İnsan |",
        "|---|---|---|",
    ]
    for key, label in DOMAIN_CHECKS:
        lines.append(f"| {label} | {rate(domain_round_one, 'assistant_' + key)} | {rate(domain, 'human_' + key)} |")

    lines += [
        "",
        "### Bulunan hata türleri ve yapılan düzeltme",
        "",
        "| Hata | Sonuç |",
        "|---|---|",
        "| Harf aralıklı metin, kopuk baş harf (`B u K a n u n`, `Y aşlılığı`) | Düzeltildi: `join_fragments`, `collapse_letter_spacing` |",
        "| Kısmi harf aralığı (`p a r ç a l a r a`, `olunmamı şsa`) | Düzeltildi: `join_impossible_onset` ve genişletilmiş `collapse_letter_spacing` |",
        "| Boşluklu işaret (`( 1 )`, `IV .`) | Düzeltildi: `normalize_whitespace` |",
        "| Metne yapışık dipnot rakamı (`Belirlenmesi2`) | Düzeltilmedi. Rakam silmek karakter değiştirmektir; bilinen sorun |",
        "| Tablo yapısının kaybı | Düzeltilmedi; bilinen sorun |",
        "",
        "## Instruction Dataset: ilk tur sonuçları",
        "",
        f"Rastgele 200 örneklemdeki kaynaklı kayıtlardan {len(round_one)} tanesi madde metniyle karşılaştırıldı.",
        "",
        "| Sonuç | Kayıt |",
        "|---|---|",
    ]
    for verdict, count in verdicts.most_common():
        lines.append(f"| {verdict} | {count} |")
    if round_one:
        lines += [
            "",
            f"Görev türü uyumu: {task_ok}/{len(round_one)}.",
            "",
            "### Hatadan türetilen kurallar",
            "",
            "| Bulgu | Eklenen kural | Elenen kayıt |",
            "|---|---|---|",
            f"| Cevapta site adresi | `source_artifact` | {filtering['exclusion_reasons'].get('source_artifact', 0)} |",
            "| Soruda karar numarası (YCGK) | `unverifiable_case_law` genişletildi | sayıma dahil |",
            "| LLM notu (`metindeki`, `sehven`) | `context_dependent` genişletildi | sayıma dahil |",
            "| `nedeni`, `sebebi` görev türünü yanıltıyor | `neden_sonuc` kuralı daraltıldı | yeniden sınıflandırıldı |",
        ]

    lines += [
        "",
        "## Instruction Dataset: ikinci tur sonuçları",
        "",
        "200 rastgele örneğin 170'i okundu. Kısa maddelerde tam metin, uzun maddelerde cevaba en yakın satırlar "
        "karşılaştırıldı, 750 karakteri aşan cevapların sonu her zaman görülmedi. Kural ve şablon örnekleri tek tek "
        "okunmadı. Örneklerin bir bölümü önceki yapımdan geldiği için aşağıdaki sayılar temizlik sırasındaki "
        "durumu gösterir, son setin hata oranı değildir. Son yapımda örnekleme giren 14 kayıt okunmadı.",
        "",
        "| Sonuç | Kayıt |",
        "|---|---|",
        *[f"| {verdict} | {count} |" for verdict, count in Counter(r["assistant_verdict"] for r in round_two).most_common()],
        "",
        "Reddedilen kayıtlar `qc_rejected_ids_v1.0.txt` dosyasındadır. Bulunan ve kurala çevrilen hatalar: ekli süre "
        "ifadeleri (`iki yıldan beş yıla`) kontrol dışı kalıyordu; `(Kaynak: gaiplik-nedir.html)` izleri; Terörle Mücadele "
        "Kanunu'nun `TMK` kısaltmasıyla Medeni Kanun sanılması; Tebligat Kanunu atıflarının İİK maddesi sanılması.",
        "",
        "## Otomatik kontroller",
        "",
        "`pytest tests` her pipeline çalışmasında şunları doğrular: metadata eksiksizliği, benzersiz ID,",
        "boş olmayan alanlar, bozuk karakter, chunk token sınırı, kümeler arası doküman, kaynak dosya, kanun",
        "maddesi ve yakın tekrar sızıntısı, atıf yapılan maddenin varlığı, görev dengesi ve onay bayraklarının",
        "yanlışlıkla açılmaması.",
        "",
        "## İnsan incelemesi nasıl yapılır",
        "",
        "`kalite_inceleme_v1.0.xlsx` dosyasındaki sarı sütunları doldurun, ardından",
        "`python scripts/qc_review_sheet.py import` ve `python scripts/11_quality_report.py` çalıştırın.",
        "Kaynakla tutarsız kayıtların kimlikleri ekrana yazılır; bunları `qc_rejected_ids_v1.0.txt` dosyasına",
        "ekleyip pipeline'ı 07. adımdan çalıştırın.",
        "",
    ]
    (quality / "quality_control_report_v1.0.md").write_text("\n".join(lines), encoding="utf-8")
    print("Kalite raporu yazıldı.")


if __name__ == "__main__":
    main()
