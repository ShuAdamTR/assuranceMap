# assuranceMap — Blazor aktarım paketi

## Tam olarak nereyi kopyalayacaksın?

Bu repoda (`C:\Users\ozgur\AuditAI\assuranceMap`) şu **5 öğeyi** al:

| Bu makinedeki yol | Hedefte nereye |
|-------------------|----------------|
| `C:\Users\ozgur\AuditAI\assuranceMap\Pages\` | `...\SeninBlazorProjen\assuranceMap\Pages\` |
| `C:\Users\ozgur\AuditAI\assuranceMap\Components\` | `...\SeninBlazorProjen\assuranceMap\Components\` |
| `C:\Users\ozgur\AuditAI\assuranceMap\Business\` | `...\SeninBlazorProjen\assuranceMap\Business\` |
| `C:\Users\ozgur\AuditAI\assuranceMap\Database\` | `...\SeninBlazorProjen\assuranceMap\Database\` |
| `C:\Users\ozgur\AuditAI\assuranceMap\_Imports.razor` | `...\SeninBlazorProjen\assuranceMap\_Imports.razor` |

```
SeninBlazorProjen/
  assuranceMap/
    Pages/
    Components/
    Business/
    Database/
    _Imports.razor
```

**Kopyalamayın:** `app\`, `src\`, `wwwroot\`, `assets\`, `.venv\`, `requirements.txt`

## Layout — host layout’una dokunma

Modülde **ayrı MainLayout yok**. Nav + shell sayfa içinde:

`Components/AssuranceMapShell.razor` — sidebar + `NavLink` + `@ChildContent`

Her sayfa kendi içeriğini sarar:

```razor
<AssuranceMapShell>
    ... sayfa içeriği ...
</AssuranceMapShell>
```

Hedef projedeki empty / mevcut layout’u olduğu gibi kullan; Router `DefaultLayout`’unu değiştirmen gerekmez.

## CSS — host `app.css` dokunulmaz

| Dosya | Ne stiller |
|-------|------------|
| `Components/AssuranceMapShell.razor.css` | Shell + ortak `.am-*` |
| `Components/EntityDetailModal.razor.css` | Detay modal |
| `Pages/*.razor.css` | Sayfa özel |

## Aktarım adımları

1. Yukarıdaki 5 öğeyi kopyala  
2. ClosedXML NuGet (Excel import)  
3. `Program.cs`: `builder.Services.AddAssuranceMap();` (`IDataAccess` kayıtlı olsun)  
4. Rotalar: `/`, `/harita`, `/veri-girisi`, `/evren`, `/excel-import`, `/ayarlar`  
   - Hedefte `/` doluysa `Home.razor` + shell içindeki Dashboard `NavLink` href’ini birlikte değiştir  
5. SQL: `Database/01_tables.sql` → `02_stored_procedures.sql`

## Namespace’ler

- `AssuranceMap.Business` · `AssuranceMap.Pages` · `AssuranceMap.Components`
