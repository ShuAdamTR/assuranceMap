# assuranceMap

Blazor’a tek klasör olarak aktarılacak iç denetim inceleme haritası modülü.

## Kopyalanacaklar

```
Pages/          → sayfalar (+ sayfa CSS); her biri AssuranceMapShell sarar
Components/     → AssuranceMapShell (nav), EntityDetailModal
Business/       → modeller, kurallar, repository, servisler, DI
Database/       → SQL
_Imports.razor
```

Host layout’a dokunulmaz; nav sayfa bileşeninde. Detay: [`AKTARIM.md`](AKTARIM.md)
