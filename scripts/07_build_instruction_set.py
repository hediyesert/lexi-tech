"""Instruction Dataset v1.0 adayını kurar.

1. Adayları görev türüne ayırır.
2. Kaynak dosya ve kanun maddesi kümeler arasında ortak olmayacak şekilde böler.
3. Görev türü ve kanun tavanlarına uyarak en güçlü kanıtlı örnekleri seçer.
4. Kaynağı kanun metni olan madde bulma örneklerini ekler.
5. Modelin sınırını söylemesini öğreten örnekleri ekler.
"""
import hashlib
import random
import re
from collections import Counter, defaultdict

from langdetect import DetectorFactory, detect

from common import (
    build_article_index,
    load_config,
    path_of,
    read_jsonl,
    write_json,
    write_jsonl,
)

DetectorFactory.seed = 42

LAW_SHORT = {
    "2709": ("Anayasa", "Anayasa'da", "Anayasa'nın"),
    "4721": ("TMK", "TMK'da", "TMK'nın"),
    "6098": ("TBK", "TBK'da", "TBK'nın"),
    "5237": ("TCK", "TCK'da", "TCK'nın"),
    "5271": ("CMK", "CMK'da", "CMK'nın"),
    "4857": ("İş Kanunu", "İş Kanunu'nda", "İş Kanunu'nun"),
    "6102": ("TTK", "TTK'da", "TTK'nın"),
    "6502": ("6502 sayılı Kanun", "6502 sayılı Kanun'da", "6502 sayılı Kanun'un"),
    "2577": ("İYUK", "İYUK'ta", "İYUK'un"),
    "213": ("VUK", "VUK'ta", "VUK'un"),
    "2004": ("İİK", "İİK'da", "İİK'nın"),
    "5510": ("5510 sayılı Kanun", "5510 sayılı Kanun'da", "5510 sayılı Kanun'un"),
}

TASK_RULES = [
    ("karsilastirma", r"\bkarşılaştır\w*|\bfark(?:ı|lar|ları|lılıkları)?\b(?!\s+(?:eder|et))|\bfarklılık\w*|\barasında\s+ne\s+fark"),
    ("olay_uygulama", r"\bsomut\s+olay\b|\bbir\s+(?:sanık|hükümlü|mükellef|kişi|işçi|kiracı|alıcı|satıcı|borçlu|alacaklı|şirket|müvekkil|tüketici)\w*\b.*\b(?:uygulan\w*|sorumlu\w*|talep\w*|yapabilir|edebilir|mi\b|mı\b|mu\b|mü\b)"),
    ("hukuki_sonuc", r"\bhukuki\s+sonuç\w*|\bsonuçları\s+nelerdir|\bsonucu\s+nedir|\bnasıl\s+etkiler\b|\betkisi\s+nedir"),
    ("yaptirim", r"\bcezası\s+(?:nedir|ne\s+kadar)|\bkaç\s+(?:yıl|ay|ceza)|\bne\s+kadar\s+ceza\b|\byaptırım\w*|\bcezada\s+artırım|\bcezasında\s+artırım|\bcezalandırılır"),
    ("usul_sure", r"\bzamanaşımı\b|\bkaç\s+gün\b|\bne\s+kadar\s+sürede\b|\bsüresi\b|\bsüre\b|\bne\s+zaman\b|\btemyiz\b|\bistinaf\b|\bbaşvur\w*|\bitiraz\b|\busul\w*|\bdava\s+aç\w*|\byetkili\s+mahkeme\b|\bgörevli\s+mahkeme\b|\bnasıl\s+(?:yapılır|talep|gerçekleş\w*|işler)\b|\bprosedür\w*"),
    ("kosul_unsur", r"\bşart\w*|\bkoşul\w*|\bunsur\w*|\bhangi\s+(?:hallerde|hâllerde|durumlarda)\b|\bistisna\w*|\bkim(?:ler)?\s+(?:olabilir|yapabilir|tarafından)\b|\bgerekir\s+mi\b|\bgereklidir\b|\bnelerdir\b"),
    ("neden_sonuc", r"^(?:.*\s)?neden\b(?!\s+ol)|\bniçin\b|\bamacı\s+(?:nedir|ne)\b"),
    ("madde_aciklama", r"\bmadde(?:si|yi|nin)?\s+(?:neyi|ne)\s+düzenle\w*|\bmadde\w*\s+açıklayınız|\bneyi\s+düzenler\b|\bne\s+öngörür\b|\bhükmüne\s+göre\b"),
    ("tanim_aciklama", r"\btanımı\s+nedir\b|\bne\s+demektir\b|\bne\s+anlama\s+gelir\b|\bnedir\b|\bkavramı\w*|\baçıklayınız\b|\baçıklayın\b|\bne\s+ifade\s+eder\b"),
]
TASK_RULES = [(name, re.compile(rule, re.IGNORECASE)) for name, rule in TASK_RULES]

OUT_OF_DOMAIN = [
    ("ekonomi", "Dolar kuru önümüzdeki ay kaç lira olur?"),
    ("ekonomi", "Bu yıl altın almak mantıklı mı?"),
    ("ekonomi", "Enflasyon yıl sonunda yüzde kaça iner?"),
    ("ekonomi", "Hangi hisse senedine yatırım yapmalıyım?"),
    ("ekonomi", "Konut fiyatları gelecek yıl düşer mi?"),
    ("ekonomi", "Kripto para almak için doğru zaman mı?"),
    ("saglik", "Başım üç gündür ağrıyor, hangi ilacı almalıyım?"),
    ("saglik", "Tansiyonum yüksek çıktı, ne yapmalıyım?"),
    ("saglik", "Çocuğumun ateşi düşmüyor, doktora gitmeli miyim?"),
    ("saglik", "Hangi vitaminleri düzenli kullanmalıyım?"),
    ("saglik", "Bel fıtığı için en iyi egzersizler hangileri?"),
    ("saglik", "Uykusuzluk için hangi bitki çayı iyi gelir?"),
    ("yemek", "Mantı hamuru nasıl açılır?"),
    ("yemek", "Karnıyarık tarifini verir misin?"),
    ("yemek", "Kek neden ortası çökük pişer?"),
    ("yemek", "Evde yoğurt nasıl mayalanır?"),
    ("spor", "Bu hafta sonu maçı kim kazanır?"),
    ("spor", "Şampiyonlar Ligi'ni hangi takım alır?"),
    ("spor", "Yarı maraton için nasıl antrenman yapmalıyım?"),
    ("spor", "Yeni başlayanlar için en iyi spor hangisi?"),
    ("teknoloji", "Python'da liste nasıl sıralanır?"),
    ("teknoloji", "Bilgisayarım neden yavaşladı?"),
    ("teknoloji", "En iyi telefon modeli hangisi?"),
    ("teknoloji", "Wi-Fi şifremi nasıl değiştiririm?"),
    ("teknoloji", "Excel'de düşeyara formülü nasıl yazılır?"),
    ("tarih_bilim", "Fotosentez nasıl gerçekleşir?"),
    ("tarih_bilim", "Malazgirt Savaşı hangi yılda oldu?"),
    ("tarih_bilim", "Ay'ın Dünya'ya uzaklığı ne kadardır?"),
    ("tarih_bilim", "İkinci Dünya Savaşı neden çıktı?"),
    ("tarih_bilim", "Su neden 100 derecede kaynar?"),
    ("gunluk", "Yarın İstanbul'da hava nasıl olacak?"),
    ("gunluk", "Tatil için Antalya mı Muğla mı daha iyi?"),
    ("gunluk", "Kediler neden mırıldanır?"),
    ("gunluk", "Bana bir aşk şiiri yazar mısın?"),
    ("gunluk", "İngilizce öğrenmek için hangi kitabı önerirsin?"),
    ("gunluk", "Evimi hangi renge boyamalıyım?"),
    ("yabanci_hukuk", "Almanya'da kira sözleşmesi nasıl feshedilir?"),
    ("yabanci_hukuk", "ABD'de şirket kurmak için hangi eyaleti seçmeliyim?"),
    ("yabanci_hukuk", "Fransa'da boşanma davası ne kadar sürer?"),
    ("yabanci_hukuk", "İngiltere'de vize reddine nasıl itiraz edilir?"),
    ("yabanci_hukuk", "Kanada'da oturum izni şartları nelerdir?"),
    ("yabanci_hukuk", "Hollanda'da iş sözleşmesi feshinde ihbar süresi nedir?"),
]
OUT_OF_DOMAIN_ANSWERS = {
    "ekonomi": "Bu soruya cevap veremem. Türk hukuku ve mevzuatı konusunda yardımcı olmak üzere hazırlandım; piyasa tahmini veya yatırım önerisi yapmak için gereken veriye sahip değilim. Hukuki bir sorunuz olursa yardımcı olabilirim.",
    "saglik": "Bu konuda yardımcı olamam, çünkü sağlık alanı uzmanlığımın dışında. Sağlığınızla ilgili soruları bir hekime danışmanız en doğrusu olur. Türk hukukuyla ilgili bir sorunuz varsa memnuniyetle bakarım.",
    "yemek": "Bu benim alanımın dışında kalıyor. Türk hukuku ve mevzuatıyla ilgili sorularda yardımcı olmak için hazırlandım, yemek tarifleri konusunda güvenilir bilgi veremem.",
    "spor": "Bu soruyu cevaplayamam. Uzmanlığım Türk hukuku ve mevzuatıyla sınırlı; spor konularında güvenilir bilgi vermem mümkün değil.",
    "teknoloji": "Bu soru alanımın dışında. Türk hukuku ve mevzuatı üzerine çalışan bir asistanım, teknik destek veya programlama konularında güvenilir yardım sunamam. Hukuki bir sorunuz olursa yardımcı olabilirim.",
    "tarih_bilim": "Bu soru hukuk alanının dışında kaldığı için cevap vermeyeceğim; yalnızca Türk hukuku ve mevzuatı konularında yardımcı olmak üzere hazırlandım.",
    "gunluk": "Bu konuda yardımcı olamam. Türk hukuku ve mevzuatıyla ilgili soruları cevaplamak için hazırlandım. Hukuki bir konuda desteğe ihtiyacınız olursa buradayım.",
    "yabanci_hukuk": "Bu soruyu cevaplayamam, çünkü kapsamım Türk hukukuyla sınırlı ve yabancı ülke mevzuatı hakkında doğrulanmış kaynağım yok. Yanlış yönlendirmemek için ilgili ülkede yetkili bir hukukçuya danışmanızı öneririm.",
}
UNKNOWN_LAWS = [
    ("6100 sayılı Hukuk Muhakemeleri Kanunu", ["119", "27", "316", "341", "107"]),
    ("6698 sayılı Kişisel Verilerin Korunması Kanunu", ["5", "6", "11", "12", "18"]),
    ("5846 sayılı Fikir ve Sanat Eserleri Kanunu", ["1/B", "22", "25", "48", "71"]),
    ("2918 sayılı Karayolları Trafik Kanunu", ["48", "85", "91", "97", "109"]),
    ("634 sayılı Kat Mülkiyeti Kanunu", ["18", "20", "24", "33", "38"]),
    ("5275 sayılı Ceza ve Güvenlik Tedbirlerinin İnfazı Hakkında Kanun", ["25", "49", "105/A", "107"]),
]
PREDICTIONS = [
    "Boşanma davamı kazanır mıyım?",
    "Komşumla davam var, mahkeme kimin lehine karar verir?",
    "Hâkim bana kesin olarak kaç yıl ceza verir?",
    "İşverenime dava açarsam kaç lira tazminat alırım?",
    "Tapu iptal davam kaç ay sürer?",
    "Ev sahibimi mahkemeye versem sonuç ne olur?",
    "Velayeti kesin olarak ben alabilir miyim?",
    "Şirketim konkordato alırsa alacaklılar nasıl davranır?",
    "Temyize gidersem karar bozulur mu?",
    "İstinaf başvurum kabul edilir mi?",
    "Vergi cezamı mahkeme kesin iptal eder mi?",
    "Bu sözleşmeyi imzalarsam başım derde girer mi?",
    "Bana ne kadar nafaka bağlanır?",
    "Kazada kusurum yüzde kaç çıkar?",
    "Davayı hangi avukatla kazanırım?",
    "Bir arkadaşım bana borcunu ödemedi, ne yapmam lazım?",
    "Eşimden ayrılmak istiyorum, ne yapmalıyım?",
    "İşten çıkarıldım, haklarım neler?",
    "Kiracım çıkmıyor, ne yapabilirim?",
    "Bana dava açıldı, şimdi ne olacak?",
]
PREDICTION_ANSWERS = [
    "Bu soruya kesin bir cevap veremem. Bir davanın sonucu somut olayın delillerine, tarafların beyanlarına ve mahkemenin değerlendirmesine bağlıdır ve bu bilgiler elimde yok. Dosyanızı bir avukata incelettirmeniz en sağlıklı yol olur; dilerseniz konuyla ilgili kanun hükümlerini anlatabilirim.",
    "Elimdeki bilgilerle güvenilir bir tahmin yapamam. Sonucu belirleyen olay ayrıntıları, deliller ve yargı merciinin takdiri burada bilinmiyor. Olayın tarihini, taraflarını ve elinizdeki belgeleri paylaşırsanız ilgili mevzuatı açıklayabilirim, ancak bu bir hukuki görüş yerine geçmez.",
    "Bu konuda kesin konuşmak yanıltıcı olur, çünkü sonuç olayın ayrıntılarına ve delillere göre değişir. Ben genel mevzuat bilgisi verebilirim; size özel değerlendirme için bir avukata danışmanız gerekir.",
]
CHAMBERS = [
    "Yargıtay 9. Hukuk Dairesi", "Yargıtay 3. Hukuk Dairesi", "Yargıtay 12. Hukuk Dairesi",
    "Yargıtay Ceza Genel Kurulu", "Yargıtay Hukuk Genel Kurulu", "Yargıtay 1. Ceza Dairesi",
    "Danıştay 10. Dairesi", "Danıştay 4. Dairesi", "Anayasa Mahkemesi Genel Kurulu",
]
DECISION_QUESTIONS = [
    "{court} {year}/{no} E. sayılı kararında ne söylemiştir?",
    "{court}'nin {year}/{no} Esas numaralı kararını özetler misin?",
    "{court} {year}/{no} sayılı kararının gerekçesi nedir?",
]
DECISION_ANSWERS = [
    "Bu kararı doğrulayabileceğim bir kaynağa sahip değilim, bu yüzden içeriği hakkında bilgi vermeyeceğim. Veri kapsamımda yargı kararı metinleri yok; uydurma bir özet sizi yanıltabilir. Kararın metnini ilgili yüksek mahkemenin resmî karar arama sisteminden kontrol etmenizi öneririm.",
    "Bu esas numarasına ait bir karar metnine erişimim yok. Kararı doğrulayamadığım için içeriğini tahmin etmek doğru olmaz. Resmî karar arama sisteminden kararın varlığını ve metnini teyit etmeniz gerekir.",
]
MISSING_ARTICLE_QUESTIONS = [
    "{short} m. {n} neyi düzenler?",
    "{gen} {n}. maddesinde ne yazıyor?",
    "{loc} {n}. madde hangi konuya ilişkindir?",
    "{short} {n}. maddesini açıklar mısın?",
]
MISSING_ARTICLE_ANSWERS = [
    "{short} metninde {n} numaralı bir madde bulamadım; numaralı maddeler {last}. maddede bitiyor. Atıfta numara veya kanun adı hatalı olabilir, kontrol etmenizi öneririm. Olmayan bir madde hakkında içerik üretmem doğru olmaz.",
    "Böyle bir madde görünmüyor: {gen} numaralı maddeleri {last}. maddeyle sona eriyor. Kaynağınızdaki atıfı yeniden kontrol ederseniz doğru maddeyi birlikte bulabiliriz.",
]
LOOKUP_QUESTIONS = [
    "{loc} \"{c}\" konusu hangi maddede düzenlenmiştir?",
    "\"{c}\" hükmü {gen} kaçıncı maddesinde yer alır?",
    "{short} kapsamında \"{c}\" için hangi maddeye bakmalıyım?",
    "\"{c}\" başlıklı hüküm {loc} nerede?",
]
LOOKUP_ANSWERS = [
    "Bu konu {short} m. {n} kapsamında \"{c}\" başlığıyla düzenlenmiştir.",
    "Bakmanız gereken hüküm {short} m. {n}. Madde başlığı \"{c}\" şeklindedir.",
]


ANSWER_PREFIX = re.compile(r"^\s*(?:Cevap|Yanıt)\s*:\s*", re.IGNORECASE)


def classify(question):
    text = " ".join(question.split())
    for name, rule in TASK_RULES:
        if rule.search(text):
            return name
    return "diger"


def stable_hash(*parts):
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def split_groups(keys, ratios, seed):
    """Grup anahtarlarını sabit tohumla kümelere dağıtır."""
    ordered = sorted(keys, key=lambda k: stable_hash(str(seed), k))
    size = len(ordered)
    validation = max(1, round(size * ratios["validation"]))
    test = max(1, round(size * ratios["test"]))
    return {
        key: "validation" if i < validation else "test" if i < validation + test else "train"
        for i, key in enumerate(ordered)
    }


def assign_candidate_splits(candidates, ratios, seed):
    """Kaynak dosya ve kanun maddesi kümeler arasında paylaşılmaz.

    Tek başına %5'ten büyük kaynak dosyalar train'de tutulur. Her madde, adayları
    orantısal olarak en çok hangi kümedeyse oraya gider. Dosyası ile maddesi
    aynı kümeye düşmeyen aday elenir.
    """
    per_file = Counter(r["source_file"] for r in candidates if r["source_file"])
    total = sum(per_file.values())
    limit = total * ratios["validation"]
    small = [name for name, count in per_file.items() if count < limit]
    ordered = sorted(small, key=lambda k: stable_hash(str(seed), k))

    file_split = {name: "train" for name in per_file}
    filled = {"validation": 0, "test": 0}
    for name in ordered:
        for split in ("validation", "test"):
            if filled[split] + per_file[name] <= total * ratios[split]:
                file_split[name] = split
                filled[split] += per_file[name]
                break

    split_totals = Counter()
    article_counts = defaultdict(Counter)
    for record in candidates:
        split = file_split.get(record["source_file"])
        if split:
            split_totals[split] += 1
            for citation in record["citations"]:
                article_counts[citation][split] += 1

    article_split = {}
    for citation, counts in article_counts.items():
        article_split[citation] = max(
            sorted(counts), key=lambda s: counts[s] / split_totals[s]
        )

    kept = []
    dropped = 0
    for record in candidates:
        wanted = {article_split.get(c) for c in record["citations"]} - {None}
        file_choice = file_split.get(record["source_file"])
        if file_choice:
            wanted.add(file_choice)
        if len(wanted) == 1:
            record["split"] = wanted.pop()
            kept.append(record)
        else:
            dropped += 1

    return kept, article_split, dropped


def select(pool, quota, task_limit, law_limit, rng):
    """Görev × kanun hücrelerinden sırayla, en güçlü kanıtlı örnekleri alır."""
    cells = defaultdict(list)
    for record in pool:
        cells[(record["task_type"], record["law"])].append(record)
    for records in cells.values():
        rng.shuffle(records)
        records.sort(key=lambda r: -r["evidence_score"])

    chosen = []
    task_counts = Counter()
    law_counts = Counter()
    keys = sorted(cells)

    while len(chosen) < quota:
        progressed = False
        for key in keys:
            task, law = key
            if len(chosen) >= quota:
                break
            if task_counts[task] >= task_limit or law_counts[law] >= law_limit:
                continue
            if cells[key]:
                chosen.append(cells[key].pop(0))
                task_counts[task] += 1
                law_counts[law] += 1
                progressed = True
        if not progressed:
            break

    return chosen


def make_example(task, question, answer, split, source_document, articles, method, origin):
    return {
        "task_type": task,
        "split": split,
        "messages": [
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ],
        "instruction": question,
        "response": answer,
        "source_document": source_document,
        "source_articles": articles,
        "generation_method": method,
        "origin": origin,
    }


def lookup_examples(index, law_documents, article_split, quota, rng):
    records = []
    for law, articles in index.items():
        short, loc, gen = LAW_SHORT[law]
        captions = Counter(a["caption"] for a in articles.values())
        for key, article in articles.items():
            caption = re.sub(r"^(?:[A-ZÇĞİÖŞÜ]{1,4}|\d+|[a-zçğıöşü])\s*[.\-)–]+\s*", "", article["caption"]).rstrip(": .")
            if (
                not key.isdigit()
                or captions[article["caption"]] > 1
                or not 6 <= len(caption) <= 70
                or caption[0].islower()
                or caption.isupper()
                or re.search(r"(?i)madde|mülga|bölüm|kısım|kitap|\d", caption)
                or len(article["text"]) < 150
                or "Mülga" in article["text"][:80]
            ):
                continue
            citation = f"{law}:{key}"
            rng_question = rng.choice(LOOKUP_QUESTIONS)
            rng_answer = rng.choice(LOOKUP_ANSWERS)
            fill = {"short": short, "loc": loc, "gen": gen, "c": caption, "n": key}
            records.append(make_example(
                "madde_bulma",
                rng_question.format(**fill),
                rng_answer.format(**fill),
                article_split.get(citation, "train"),
                law_documents[law],
                [citation],
                "kural_tabanli_kanun_metninden",
                {"dataset": "mevzuat"},
            ))
    rng.shuffle(records)
    selected = []
    limits = {"train": quota * 0.9, "validation": quota * 0.05, "test": quota * 0.05}
    counts = Counter()
    for record in records:
        if counts[record["split"]] < limits[record["split"]]:
            counts[record["split"]] += 1
            selected.append(record)
    return selected


def boundary_examples(index, law_documents, ratios, rng, seed):
    """Modelin 'bilmiyorum / alanım dışında' demesini öğreten örnekler."""
    records = []

    groups = sorted({topic for topic, _ in OUT_OF_DOMAIN})
    topic_split = split_groups(groups, ratios, seed)
    for topic, question in OUT_OF_DOMAIN:
        records.append(make_example(
            "alan_disi", question, OUT_OF_DOMAIN_ANSWERS[topic], topic_split[topic],
            None, [], "elle_yazilan_sablon", {"dataset": "lexitech", "family": topic},
        ))

    law_split = split_groups(sorted(index), ratios, seed)
    for law, articles in index.items():
        short, loc, gen = LAW_SHORT[law]
        last = max(int(k) for k in articles if k.isdigit())
        for offset in rng.sample(range(5, 200), 9):
            number = last + offset
            fill = {"short": short, "loc": loc, "gen": gen, "n": number, "last": last}
            records.append(make_example(
                "bilgi_yetersizligi",
                rng.choice(MISSING_ARTICLE_QUESTIONS).format(**fill),
                rng.choice(MISSING_ARTICLE_ANSWERS).format(**fill),
                law_split[law], law_documents[law], [],
                "kural_tabanli_kanun_metninden",
                {"dataset": "lexitech", "family": f"olmayan_madde_{law}"},
            ))

    court_split = split_groups(CHAMBERS, ratios, seed)
    for court in CHAMBERS:
        for _ in range(8):
            fill = {"court": court, "year": rng.randint(2009, 2024), "no": rng.randint(1000, 39000)}
            records.append(make_example(
                "bilgi_yetersizligi",
                rng.choice(DECISION_QUESTIONS).format(**fill),
                rng.choice(DECISION_ANSWERS),
                court_split[court], None, [], "elle_yazilan_sablon",
                {"dataset": "lexitech", "family": "dogrulanamayan_karar"},
            ))

    unknown_split = split_groups([name for name, _ in UNKNOWN_LAWS], ratios, seed)
    for name, numbers in UNKNOWN_LAWS:
        for number in numbers:
            records.append(make_example(
                "bilgi_yetersizligi",
                f"{name} madde {number} ne diyor?",
                f"{name} doğrulanmış veri kapsamımda bulunmuyor, bu yüzden {number}. maddenin içeriğini aktarmam yanıltıcı olur. Güncel metni Mevzuat Bilgi Sistemi'nden kontrol etmenizi öneririm.",
                unknown_split[name], None, [], "elle_yazilan_sablon",
                {"dataset": "lexitech", "family": "kapsam_disi_kanun"},
            ))

    question_split = split_groups(PREDICTIONS, ratios, seed)
    for question in PREDICTIONS:
        records.append(make_example(
            "bilgi_yetersizligi", question, rng.choice(PREDICTION_ANSWERS),
            question_split[question], None, [], "elle_yazilan_sablon",
            {"dataset": "lexitech", "family": "kisiye_ozel_tahmin"},
        ))

    return records


def main():
    config = load_config()
    settings = config["instruction"]
    ratios = config["split"]
    seed = config["project"]["random_seed"]
    version = config["project"]["version"]
    rng = random.Random(seed)

    documents = list(read_jsonl(path_of(config["paths"]["final"], "domain_corpus_v1.0.jsonl")))
    index = {d["law_number"]: build_article_index(d) for d in documents}
    law_documents = {d["law_number"]: d["document_id"] for d in documents}

    rejected_path = path_of(config["paths"]["reports"], "quality/qc_rejected_ids_v1.0.txt")
    rejected = set()
    if rejected_path.exists():
        rejected = {
            line.split()[0]
            for line in rejected_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")
        }

    candidates = []
    task_pool = Counter()
    for record in read_jsonl(path_of("data/interim/instruction_candidates_v1.0.jsonl")):
        record["task_type"] = classify(record["question"])
        record["answer"] = ANSWER_PREFIX.sub("", record["answer"])
        record["law"] = record["citations"][0].split(":")[0]
        task_pool[record["task_type"]] += 1
        if record["task_type"] != "diger" and record["id"] not in rejected:
            candidates.append(record)

    candidates, article_split, dropped = assign_candidate_splits(candidates, ratios, seed)

    boundary = boundary_examples(index, law_documents, ratios, rng, seed)
    lookup = lookup_examples(index, law_documents, article_split, 350, rng)
    qa_target = settings["target_examples"] - len(boundary) - len(lookup)

    selected = []
    for split in ("train", "validation", "test"):
        pool = [r for r in candidates if r["split"] == split]
        quota = round(qa_target * ratios[split])
        share = settings["target_examples"] * ratios[split]
        chosen = select(
            pool,
            quota,
            round(share * settings["max_task_share"]),
            round(share * settings["max_law_share"]),
            rng,
        )
        selected.extend(chosen)
        print(split, "havuz:", len(pool), "seçilen:", len(chosen))

    examples = list(boundary) + list(lookup)
    for record in selected:
        method = (
            "llm_uretimi_kaynak_veri_seti"
            if record["source"] == "sinanelms/hukukisorular"
            else "kaynak_veri_seti_yontem_bilinmiyor"
        )
        example = make_example(
            record["task_type"], record["question"], record["answer"], record["split"],
            law_documents[record["law"]], record["citations"], method,
            {
                "dataset": record["source"],
                "file": record["source_file"],
                "record_id": record["id"],
            },
        )
        example["evidence_score"] = record["evidence_score"]
        examples.append(example)

    non_turkish = 0
    final = []
    for example in examples:
        language = detect(example["response"])
        if language != "tr":
            non_turkish += 1
        example["language"] = language
        final.append(example)

    final.sort(key=lambda e: stable_hash(str(seed), e["instruction"]))
    for number, example in enumerate(final, start=1):
        example["id"] = f"INS_{number:05d}"
        example["dataset_version"] = version
        example["verified"] = False
        example["verified_by"] = None
        example["rights_status"] = "pending_review"
        example["training_approved"] = False

    field_order = [
        "id", "split", "task_type", "messages", "instruction", "response",
        "source_document", "source_articles", "generation_method", "origin",
        "evidence_score", "language", "verified", "verified_by",
        "rights_status", "training_approved", "dataset_version",
    ]
    final = [{k: e.get(k) for k in field_order} for e in final]

    final_dir = path_of(config["paths"]["final"])
    write_jsonl(final_dir / "instruction_v1.0.jsonl", final)
    for split in ("train", "validation", "test"):
        write_jsonl(
            final_dir / "instruction_v1.0" / f"{split}.jsonl",
            [e for e in final if e["split"] == split],
        )

    write_json(path_of(config["paths"]["reports"], "statistics/instruction_build_v1.0.json"), {
        "target": settings["target_examples"],
        "examples": len(final),
        "by_split": dict(Counter(e["split"] for e in final)),
        "by_task": dict(Counter(e["task_type"] for e in final).most_common()),
        "by_task_and_split": {
            task: dict(Counter(e["split"] for e in final if e["task_type"] == task))
            for task in sorted({e["task_type"] for e in final})
        },
        "by_method": dict(Counter(e["generation_method"] for e in final).most_common()),
        "by_origin": dict(Counter(e["origin"]["dataset"] for e in final).most_common()),
        "by_law": dict(Counter(
            e["source_articles"][0].split(":")[0] for e in final if e["source_articles"]
        ).most_common()),
        "candidate_task_pool": dict(task_pool.most_common()),
        "dropped_for_split_conflict": dropped,
        "rejected_after_quality_review": len(rejected),
        "non_turkish_responses": non_turkish,
    })
    print(Counter(e["task_type"] for e in final).most_common())
    print(Counter(e["split"] for e in final))
    print("Örnek:", len(final), "Türkçe olmayan:", non_turkish)


if __name__ == "__main__":
    main()
