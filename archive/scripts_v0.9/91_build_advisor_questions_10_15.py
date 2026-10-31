import json
from pathlib import Path

STATS = Path("reports/statistics")
QUALITY = Path("reports/quality")

LANG_PATH = STATS / "language_quality_report_v0.9.1.json"
TASK_PATH = STATS / "instruction_task_quality_v0.9_2.json"
OUT = QUALITY / "advisor_questions_10_15_v0.9.md"

if OUT.exists():
    raise SystemExit("Rapor zaten mevcut; üzerine yazılmadı.")

language = json.loads(LANG_PATH.read_text(encoding="utf-8"))
task = json.loads(TASK_PATH.read_text(encoding="utf-8"))

assert language["advisor_question"] == 10
assert language["instruction_total_qa"] == 124510
assert language["independent_human_approved"] == 0

question = language["instruction"]["question"]
answer = language["instruction"]["answer"]

assert question["combined_tr"] == 124510
assert question["unresolved"] == 0
assert answer["combined_tr"] == 124509
assert answer["unresolved"] == 1
assert language["flagged_texts_reviewed"] == 123

domain = language["domain_sample"]
assert domain["documents"] == 12
assert domain["passages"] == 60
assert domain["automatic_categories"]["tr"] == 60

assert task["question"] == 15
assert task["dataset_records"] == 124510
assert task["classification_status"] == "experimental"

distribution = task["task_distribution"]

assert sum(
    item["count"] for item in distribution.values()
) == 124510

assert distribution["other"]["count"] == 61125

development = task["development_sample"]
test = task["held_out_from_development_sample"]

assert development["size"] == 70
assert development["agreement"] == 30
assert test["size"] == 50
assert test["agreement"] == 37
assert test["independent_human_verified"] is False

lines = [
    "# LexiTech TR — Danışman Soruları 10 ve 15",
    "",
    "**Proje:** LexiTech TR",
    "",
    "**Analiz edilen Instruction sürümü:** "
    "124.510 QA; 14 kayıtlık kalite bekletmesi öncesi.",
    "",
    "## 10. Veri setinin dil dağılımını nasıl belirledim?",
    "",
    "Instruction Dataset'teki 124.510 soru-cevap "
    "kaydının soru ve cevap alanlarını ayrı ayrı "
    "otomatik dil tespitinden geçirdim. Otomatik "
    "sınıflandırmanın kesinleştiremediği işaretli "
    "metinler için asistan destekli ön değerlendirme "
    "yaptım.",
    "",
    "| Dil değerlendirmesi | Soru | Cevap |",
    "|---|---:|---:|",
    (
        f"| Otomatik Türkçe | "
        f"{question['automatic_tr']:,} | "
        f"{answer['automatic_tr']:,} |"
    ),
    (
        f"| Asistanın Türkçe ön değerlendirmesi | "
        f"{question['assistant_preliminary_tr']:,} | "
        f"{answer['assistant_preliminary_tr']:,} |"
    ),
    (
        f"| Birleşik Türkçe sonucu | "
        f"{question['combined_tr']:,} | "
        f"{answer['combined_tr']:,} |"
    ),
    (
        f"| Sınıflandırılamayan | "
        f"{question['unresolved']:,} | "
        f"{answer['unresolved']:,} |"
    ),
    "",
    "Toplam 123 işaretli metin için asistan ön "
    "değerlendirmesi yapıldı. Bunların 122'si "
    "Türkçe olarak ön değerlendirildi; bir cevap "
    "dil açısından sınıflandırılamadı.",
    "",
    "Domain Corpus tarafında ise 12 kanun "
    "belgesinden alınmış 60 metin parçasını "
    "inceledim. Otomatik dil tespiti 60 parçanın "
    "tamamını Türkçe olarak sınıflandırdı.",
    "",
    "**Sınırlılık:** Bu sonuçlar bağımsız insan "
    "onayından geçmedi. Özellikle Domain Corpus "
    "değerlendirmesi bütün metinler yerine "
    "60 örnek parçayı kapsamaktadır. "
    "Dil analizi hukuki doğruluğu göstermez.",
    "",
    "## 15. Veri setinde hangi görev türleri var "
    "ve bunların kalitesini nasıl değerlendirdim?",
    "",
    "124.510 soru-cevap kaydını kural ve anahtar "
    "kelime tabanlı deneysel bir görev sınıflandırıcısı "
    "ile kategorilere ayırdım. Sınıflandırıcıyı "
    "geliştirmek için 70 örnek kullandım; "
    "geliştirme aşamasından ayrı tutulan "
    "50 örnek üzerinde ön değerlendirme yaptım.",
    "",
    "### Görev türü dağılımı",
    "",
    "| Görev türü | Kayıt | Oran |",
    "|---|---:|---:|",
]

for category, values in sorted(
    distribution.items(),
    key=lambda item: item[1]["count"],
    reverse=True
):
    lines.append(
        f"| `{category}` | {values['count']:,} | "
        f"%{values['percent']:.2f} |"
    )

lines += [
    "",
    "### Ön kalite değerlendirmesi",
    "",
    f"- Geliştirme örnekleri: **{development['size']}**",
    f"- Geliştirme uyumu: "
    f"**{development['agreement']}/{development['size']}**",
    f"- Ayrı tutulan test örnekleri: **{test['size']}**",
    f"- Test uyumu: **{test['agreement']}/{test['size']} "
    f"(%{test['unweighted_agreement_percent']:.2f})**",
    "- Bağımsız insan uzman doğrulaması: **Yok**",
    "",
    "Test örnekleri tahmin edilen görev kategorilerine "
    "göre dengeli seçildi. Etiketler bağımsız "
    "uzmanlardan değil, asistanın önerdiği "
    "ön etiketlerden geldi. Dolayısıyla %74 "
    "uyumu, gerçek sınıflandırma doğruluğu veya "
    "tüm veri setinin kalitesi olarak yorumlamıyorum.",
    "",
    f"`other` kategorisinde **{distribution['other']['count']:,}** "
    f"kayıt (**%{distribution['other']['percent']:.2f}**) "
    "bulunması, sınıflandırıcının geliştirilmesi "
    "gerektiğine işaret etmektedir.",
    "",
    "## Sürüm farkı ve tamamlanmamış çalışmalar",
    "",
    "Bu iki analiz 124.510 QA üzerinde yapıldı. "
    "Sonraki kalite aşamasında 14 kayıt geçici "
    "olarak bekletildi ve 124.496 QA içeren "
    "ayrı bir çalışma kopyası oluşturuldu. "
    "Buradaki dil ve görev dağılımı sonuçlarını "
    "124.496 QA için yeniden hesaplanmış "
    "sonuçlar gibi sunmuyorum.",
    "",
    "Bağımsız insan doğrulaması, görev sınıflandırıcısının "
    "iyileştirilmesi ve güncel çalışma kopyasındaki "
    "dağılımların yeniden değerlendirilmesi "
    "tamamlanmamıştır.",
    "",
    "## Veri kullanım ve eğitim onayı",
    "",
    "- `training_approved = false`",
    "- `rights_status = pending_review`",
    "",
    "## Kanıt dosyaları",
    "",
    f"- `{LANG_PATH}`",
    f"- `{TASK_PATH}`",
    "- `reports/statistics/language_quality_report_v0.9.1.md`",
    "- `reports/statistics/instruction_task_quality_v0.9_2.md`",
    "- `reports/quality/instruction_end_to_end_accounting_v0.9.json`",
    "",
]

QUALITY.mkdir(parents=True, exist_ok=True)

OUT.write_text("\n".join(lines), encoding="utf-8")

print("LEXITECH TR - DANISMAN SORULARI 10 VE 15")
print("=" * 60)
print("Dil analizi kayit sayisi:", 124510)
print("Gorev analizi kayit sayisi:", 124510)
print("Dil inceleme raporu: PASS")
print("Gorev dagilimi toplami: PASS")
print("Test uyumu: 37/50 (%74)")
print("Bagimsiz insan onayi: YOK")
print("Rapor olusturuldu:", OUT)
print("Egitim onayi: HAYIR")
print("Ana veri setleri degistirilmedi.")
