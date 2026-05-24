# KIZIL Asistan - Sistem Kuralları

## Amaç

KIZIL Asistan:

* stabil
* modüler
* geliştirilebilir
* yerel çalışan
  bir kişisel AI sistemi olacak.

---

# Temel Kurallar

1. Mevcut mimari korunacak.
2. Gereksiz refactor yapılmayacak.
3. Orchestrator.py aşırı büyütülmeyecek.
4. Yeni özellik mevcut modüle ait değilse yeni modül açılacak.
5. Mevcut dosyaların sorumlulukları karıştırılmayacak.
6. Kod stabilitesi yeni özellikten önemlidir.
7. Gereksiz abstraction yasaktır.
8. Gereksiz design pattern yasaktır.
9. Enterprise mimari yasaktır.
10. Distributed system yasaktır.
11. Microservice yasaktır.
12. Docker/Kubernetes yasaktır.
13. Kodlar küçük ve okunabilir tutulacak.
14. Her değişiklik geri alınabilir olmalı.
15. Büyük değişiklik öncesi git commit önerilecek.

---

# Modül Kuralları

* core/ = sistem yönetimi
* modules/ = özellikler
* utils/ = yardımcı sistemler
* storage/ = veriler

Modüller birbirinin içine iş mantığı gömmemeli.

---

# Geliştirme Önceliği

1. Stabilite
2. Güvenlik
3. Modülerlik
4. Performans
5. Yeni özellik

---

# Yasaklar

* Gizli refactor
* Kendi kendine mimari değiştirme
* Gereksiz klasör oluşturma
* Mevcut sistemi yeniden yazma
* Devasa framework kurma
