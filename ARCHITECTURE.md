# KIZIL Asistan - Mimari

## Çekirdek Sistem

### core/orchestrator.py

Ana yönetici.
Komut yönlendirme merkezi.

### core/llm_router.py

LLM bağlantısı.
Ollama iletişimi.

### core/memory_manager.py

Hafıza sistemi.
Konuşma geçmişi ve özetleme.

---

# Modüller

## modules/chat/

Sohbet sistemi.

## modules/tools/

Araç sistemi.

## modules/tasks/

Görev sistemi.

## modules/browser/

Web araçları.

## modules/files/

Dosya sistemi.

## modules/automation/

Bilgisayar otomasyonu.

## modules/profile/

Kullanıcı tercihleri.

## modules/session/

Oturum sistemi.

## modules/plugins/

Eklenti sistemi.

---

# Veri Deposu

## storage/

Tüm veriler burada tutulur.

* config.json
* tasks.json
* profile.json
* vectors.json
* sessions.json

---

# Mimari Kurallar

1. Orchestrator sadece yönlendirme yapmalı.
2. İş mantığı modüllerde olmalı.
3. Modüller birbirine aşırı bağımlı olmamalı.
4. Tool sistemi merkezi olmalı.
5. Config merkezi kullanılmalı.
6. Güvenlik kontrolleri bypass edilmemeli.
