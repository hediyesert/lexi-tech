# Kısa literatür taraması (taslak)

**Durum:** 31.10.2026 tarihli web taramasından çıkarılan taslaktır. Aşağıdaki özetler arama sonuçlarındaki
özetlere ve kayıt sayfalarına dayanır, makalelerin tamamı okunmadı. Sunumda veya tezde kullanmadan önce
grup üyeleri birincil kaynağı okuyup sayıları doğrulamalıdır.

## Neden bu proje gerekli: hukukta uydurma bilgi

- **Dahl, Magesh, Suzgun, Ho (2024), Large Legal Fictions.** Kamuya açık dil modellerinin hukuki sorularda en az
  %58 oranında uydurma bilgi ürettiğini, kendi hatalarını öngöremediğini ve kullanıcının yanlış varsayımlarını
  sorgusuz kabul edebildiğini raporlar. ABD hukuku üzerindedir.
- **Magesh ve diğerleri (2025), Hallucination-Free?** RAG kullanan ticari hukuk araştırma araçlarında da %17-33
  oranında uydurma bilgi bulur. Yani RAG riski azaltır ama ortadan kaldırmaz.

**Projeye etkisi:** `bilgi_yetersizligi` örnekleri ve atıf doğruluğu ölçütü doğrudan bu probleme yöneliktir.
Yanlış varsayımı kabul etme bulgusu, olmayan madde örneklerinin neden gerekli olduğunu da destekler.

## Alan uyarlaması: CPT ile SFT gerçekten işe yarıyor mu

- **Chen ve diğerleri, Continual Pre-Training is (not) What You Need in Domain Adaptation.** Hukuk alanında
  continued pretraining alan bilgisini artırıyor, ancak hukuki muhakeme görevlerinde her zaman iyileşme sağlamıyor.
- **İtalyan hukuku çalışması (Bari Üniversitesi kaydı).** Normattiva mevzuat sitesinden kurulan corpus ile
  Llama-3.1-8B, continued pretraining ve LoRA ile uyarlanmış ve özgün modele göre daha iyi sonuç raporlanmış.
  Mevzuattan corpus kurma yöntemi bizimkine en yakın çalışmadır.

**Projeye etkisi:** Finaldeki üçlü karşılaştırma gerekli, çünkü CPT'nin her görevde fark yaratacağı varsayılamaz.
Bu yüzden değerlendirme yalnızca bilgi sorularıyla değil, görev türü bazında yapılmalıdır.

## Türkçe hukuk NLP çalışmaları ve benzer veri setleri

| Çalışma | Tür | İçerik | Bize göre farkı |
|---|---|---|---|
| Mumcuoğlu ve diğerleri (2021) | Karar tahmini | Türk yüksek mahkeme kararlarının sonucunu olay anlatımından tahmin eder | Soru cevaplama değil, sınıflandırma. Kod: `koc-lab/law-turk` |
| LEXTREME (Türkçe bölümü) | Benchmark | 1.290 karar metni, ikili etiket | Küçük. Kaynak tanımı tutarsız görünüyor, kullanmadan kontrol edilmeli |
| HukukBERT (arXiv 2604.04790) | Encoder model | Mevzuat, karar ve doktrinden corpus; boşluk doldurma testi | Metin üretmez, cevap vermez |
| TurkishLegalBench (Zenodo, ODTÜ) | Benchmark | Yüksek mahkemelerden 38.009 belge, 7 görev | Yargı kararı ağırlıklı. Değerlendirme için aday |
| Cam ve diğerleri | Karşılaştırma | Kira hukuku üzerine 1.446 soru-cevap ile dil modeli karşılaştırması | Tek alan |
| Mecellem-Qwen3-1.7B-TR | Decoder model | Türkçe hukuk ve resmî metinlerle continual pretraining, yaklaşık 225 milyar token (model kartı beyanı) | Aynı yönteme en yakın örnek, ölçeği çok büyük |

**Boşluk:** Taramada Türk hukuku için RAG veya soru cevaplama üzerine yerleşik bir çalışma bulunamadı. Bu, öyle bir
çalışma olmadığını göstermez, ayrı bir tarama yapılmalı.

**Projeye etkisi:**

- Mecellem örneği, 1,44 milyon tokenlık corpus'umuzun CPT için ne kadar küçük olduğunu gösteriyor. Proje küçük ölçekli
  bir karşılaştırma olarak konumlandırılmalı.
- TurkishLegalBench ve Mecellem final döneminde karşılaştırma noktası olabilir.
  Kullanmadan önce lisanslarına bakılmalı.

## Kullanım hakkına ilişkin not

FSEK m. 31'in resmen yayımlanan mevzuat ve yargı içtihatlarının kullanımını serbest bıraktığı ikincil kaynaklarda
aktarılıyor. Hukuki görüş değildir, danışmana soruldu: [advisor_questions.md](advisor_questions.md).

## Kaynaklar

- [Large Legal Fictions](https://arxiv.org/pdf/2401.01301)
- [Hallucination-Free?](https://isps.yale.edu/node/26123)
- [Continual Pre-Training is (not) What You Need in Domain Adaptation](https://arxiv.org/pdf/2504.13603)
- [İtalyan hukuku çalışması](https://ricerca.uniba.it/handle/11586/556661)
- [Natural language processing in law](https://repository.bilkent.edu.tr/items/93edbe0f-f0bc-4f91-84aa-e38fa0b0a720)
- [HukukBERT](https://arxiv.org/pdf/2604.04790)
- [TurkishLegalBench](https://avesis.metu.edu.tr/bilimsel-veri-paylasimi/7ca94eb8-f8de-4d5a-a954-e063c02359e3/turkishlegalbench-a-comprehensive-multi-task-benchmark-suite-for-turkish-legal-nlp)
- [Turkish Rent Law QA çalışması](https://avesis.mcbu.edu.tr/yayin/bbbf3f5e-773a-47ec-a7f4-f2b9cf689868/computational-intelligence-in-legal-nlp-evaluating-language-models-on-turkish-legal-texts)
- [Mecellem-Qwen3-1.7B-TR model kartı](https://featherless.ai/models/newmindai/Mecellem-Qwen3-1.7B-TR)
- [LEXTREME Türkçe bölümü](https://huggingface.co/datasets/joelniklaus/lextreme/commit/1a4cca7d557e8e2573774a71d206b99c8e7e9ca3)
