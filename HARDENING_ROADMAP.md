# KIZIL Asistan – Hardening Roadmap (Post-Stabilization)

> **Oluşturulma:** 2026-05-25  
> **Önceki Aşama:** ROADMAP.md (donduruldu – tüm feature fazları tamamlandı)  
> **Amaç:** Davranış stabilitesi, güvenlik sıkılaştırma, runtime dayanıklılığı ve gözlemlenebilirlik.

---

## FAZ H1 – Davranış Stabilitesi (Behaviour Stability)

| # | Zayıflık | Durum |
|---|----------|-------|
| 1 | Hallucination Guard (sahte başarı raporu) | ✅ Tamamlandı |
| 2 | Yanlış Tool Seçimi / Gereksiz Tool Çağrısı | ✅ Tamamlandı |
| 3 | Retry Spam (aynı tool'u gereksiz tekrar) | ⏳ Bekliyor |
| 4 | Context Drift (uzun oturumda bağlam kayması) | ⏳ Bekliyor |

---

## FAZ H2 – Güvenlik Sertleştirme (Security Hardening)

| # | Zayıflık | Durum |
|---|----------|-------|
| 1 | Plugin izin kaçakları | ⏳ Bekliyor |
| 2 | Path bypass (sandbox aşımı) | ⏳ Bekliyor |
| 3 | Malformed input (JSON injection vb.) | ⏳ Bekliyor |
| 4 | Memory corruption (vektör/delta bozulması) | ⏳ Bekliyor |
| 5 | Infinite task chain / fake workflow completion | ⏳ Bekliyor |

---

## FAZ H3 – Runtime Dayanıklılığı (Runtime Resilience)

| # | Zayıflık | Durum |
|---|----------|-------|
| 1 | Uzun session bellek basıncı | ⏳ Bekliyor |
| 2 | Vector degradation (delta birikimi) | ⏳ Bekliyor |
| 3 | Pruning stability (agresif budama) | ⏳ Bekliyor |
| 4 | Timeout edge-cases (yarım kalan işlem) | ⏳ Bekliyor |

---

## FAZ H4 – Gözlemlenebilirlik (Observability)

| # | Zayıflık | Durum |
|---|----------|-------|
| 1 | Runtime telemetry (araç istatistikleri) | ⏳ Bekliyor |
| 2 | Failure heatmap (hata kümelenme analizi) | ⏳ Bekliyor |
| 3 | Session analytics (kullanım örüntüleri) | ⏳ Bekliyor |
| 4 | Determinizm skoru (tekrar edilebilirlik) | ⏳ Bekliyor |

---

> **Çalışma disiplini:** Her madde için: Zayıflık Analizi → Risk → Minimal Patch → Test → Commit.  
> Yeni özellik, mimari değişiklik, async/threading/enterprise pattern **kesinlikle yasak**.
