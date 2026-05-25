# KIZIL Asistan — Mimari Dokümantasyon

# Mimari Amaç

KIZIL:
yerel çalışan,
modüler,
deterministik,
tool-enabled AI runtime sistemidir.

Amaç:
tek kullanıcı için
kontrollü otonomluk sağlayan
hafif bir AI çalışma ortamı oluşturmaktır.

---

# Runtime Modeli

KIZIL:

* sequential runtime
* synchronous execution
* single process

mantığında çalışır.

Ana akış:

main.py
→ orchestrator
→ chat_module
→ tool_manager
→ tool execution
→ memory update

şeklindedir.

---

# Çekirdek Katmanlar

## core/

Sistemin merkezi kontrol katmanı.

### orchestrator.py

Ana yönetici.
Komut yönlendirme,
modül koordinasyonu,
runtime kontrolü.

İş mantığı burada dağılmamalıdır.

---

### llm_router.py

LLM bağlantısı.
Model çağrıları,
retry sistemi,
temperature kontrolü.

---

### memory_manager.py

Konuşma hafızası,
özetleme,
bağlam yönetimi,
uzun süreli hafıza erişimi.

---

# Modül Katmanı

## modules/chat/

LLM davranış katmanı.
Tool kararları,
planlama,
cevap üretimi.

---

## modules/tools/

Araç kayıt sistemi.
Tool execution merkezi.

Yeni araçlar:
ToolManager üzerinden bağlanmalıdır.

---

## modules/tasks/

Görev sistemi.

Task lifecycle:

pending
→ running
→ done / failed / cancelled

mantığında çalışmalıdır.

Sequential execution zorunludur.

---

## modules/memory/

Vektör hafıza sistemi.

Semantic search,
memory ranking,
context filtering.

---

## modules/plugins/

Dinamik plugin yükleme sistemi.

Pluginler:
sandbox sınırları içinde çalışmalıdır.

---

# Mimari Yasaklar

Aşağıdakiler mimari ihlal sayılır:

* async runtime
* distributed orchestration
* event-driven microservice structure
* uncontrolled background loops
* recursive autonomous execution
* self-modifying runtime

---

# Geliştirme Kuralları

Yeni geliştirmeler:

* minimal patch
* düşük risk
* geri alınabilir değişiklik
* küçük commitler

şeklinde ilerlemelidir.

Her büyük değişiklik:
önce git snapshot ile korunmalıdır.
