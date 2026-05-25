Önce proje kökündeki şu dosyalara uy:

* SYSTEM_RULES.md
* DEVELOPMENT_PROTOCOL.md
* ARCHITECTURE.md
* ROADMAP.md
* HARDENING_FINAL_RAPOR.md

Bu dosyalar proje anayasasıdır.

KIZIL:

* sequential runtime çalışır
* deterministik davranır
* minimal bağımlılık kullanır
* mevcut mimariyi korur
* enterprise mimariye dönüşemez
* async/thread/distributed/event bus mimarileri yasaktır

Yeni özellik önermeden önce:

1. risk analizi
2. mevcut mimariye etkisi
3. regression riski
4. memory etkisi
5. determinism etkisi
6. hallucination riski

analiz edilmelidir.

Amaç:
“Capability expansion” değil,
“Behavioral precision ve runtime reliability” geliştirmesidir.

Yeni görev:
INTELLIGENCE_REFINEMENT_ROADMAP.md oluştur.
Sadece mevcut sistemi daha güvenilir, daha kararlı, daha açıklanabilir ve daha deterministik hale getirecek geliştirmeler öner.

Şunlardan kaçın:

* yeni framework
* async runtime
* distributed yapı
* multi-agent
* websocket
* streaming architecture
* cloud dependency
* self-modifying code
* gereksiz abstraction
* enterprise patterns

Her öneri:

* minimal patch
* replace yöntemi
* test stratejisi
* rollback güvenliği
* telemetry doğrulaması

ile birlikte gelmelidir.
