# Değerlendirme planı

Vizede evaluation dataset teslimi istenmiyor. Bu plan final döneminde "modelin başarılı olduğunu nasıl
göstereceğiz?" sorusunun cevabıdır.

**Karşılaştırılacak sistemler.** (1) Hazır instruct model, (2) `data/final/train.jsonl` ile CPT yapılmış model,
(3) CPT + `data/final/instruction_v1.0/train.jsonl` ile SFT yapılmış model.

**Ayrılan veri.** Instruction `test` kümesi (216 örnek) eğitimde kullanılmaz. Kaynak dosyası ve kanun maddesi
train ile ortak değildir, yani model test maddelerini eğitimde soru-cevap olarak görmez.

**Ölçütler.**

| Ölçüt | Nasıl ölçülür | Projedeki karşılığı |
|---|---|---|
| Atıf doğruluğu | Cevaptaki kanun ve madde gerçekte var mı (`build_article_index`) | Uydurma madde riskini azaltmak |
| Madde bulma doğruluğu | `madde_bulma` test örneklerinde doğru madde oranı | İlgili maddeyi bulmak |
| Sınır davranışı | `bilgi_yetersizligi` ve `alan_disi` örneklerinde reddetme oranı | Sahte karar üretmemek |
| Cevap kalitesi | En az iki kişinin kör puanladığı örnekler; hukukçu örneği | Hukuki doğruluk |

**Önemli sınır.** Test kümesi hukukçu onaylı değildir, otomatik doğrulanan etiketler taşır. Hukuki doğruluk
iddiası ancak hukukçu puanlamasıyla yapılabilir.
