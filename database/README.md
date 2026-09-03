# AssuranceMap — Veritabanı (SQL Server)

Bu klasör Okyanus uyumlu şema ve stored procedure scriptlerini içerir.

## Kurulum sırası

1. Hedef SQL Server'da boş bir veritabanı oluşturun (ör. `AssuranceMap`).
2. `01_tables.sql` çalıştırın (tablolar + seed).
3. `02_stored_procedures.sql` çalıştırın.
4. Hedef Blazor / Okyanus bağlantısını kullanın (`IDataAccess`). Lokal stub kullanıyorsanız connection string’i kendi `appsettings` dosyanızda tanımlayın.

---

## Tablolar

### `dbo.Universes`

Evren entity kayıtları (İştirak / Müdürlük / Ürün).

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| Id | INT IDENTITY PK | |
| UniverseType | NVARCHAR(32) | `istirak` / `mudurluk` / `urun` |
| Name | NVARCHAR(255) | Entity adı |
| IsActive | BIT | Soft delete / pasif |
| CreatedAt / UpdatedAt | DATETIME2 | UTC |

- **Unique:** `(UniverseType, Name)`

### `dbo.Reviews`

İnceleme kayıtları.

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| Id | INT IDENTITY PK | |
| UniverseId | INT FK → Universes | |
| ReviewSubject | NVARCHAR(500) | İnceleme konusu |
| CoveredDecisionCount | INT | Kapsama alınan karar sayısı |
| DecisionOwnership | NVARCHAR(255) | Karar sahipliği |
| Unit | NVARCHAR(64) | Birim (KBU/KBD …) |
| ReviewDate | DATE | İnceleme tarihi |
| UnitDecisionCounts | NVARCHAR(MAX) | Birim karar sayıları |
| ReviewStatus | NVARCHAR(64) | Whitelist |
| AssuranceLevel | NVARCHAR(64) | Whitelist |
| RiskLevel | NVARCHAR(64) | Whitelist |
| ExaminationDepth | NVARCHAR(64) | `tam` / `kismi` |
| CreatedAt / UpdatedAt | DATETIME2 | |

- **Index:** UniverseId, Unit, ReviewDate  
- **FK:** UniverseId → Universes(Id) ON DELETE kısıtı (RESTRICT davranışı uygulama + SP)

### `dbo.FieldOptions`

Form / Excel whitelist seçenekleri.

| Kolon | Tip |
|-------|-----|
| Id | INT IDENTITY PK |
| FieldKey | NVARCHAR(64) |
| Value | NVARCHAR(64) |
| Label | NVARCHAR(128) |
| SortOrder | INT |
| IsActive | BIT |
| CreatedAt / UpdatedAt | DATETIME2 |

- **Unique:** `(FieldKey, Value)`  
- Seed FieldKey'ler: `unit`, `review_status`, `assurance_level`, `risk_level`, `examination_depth`

### `dbo.AppSettings`

Anahtar-değer ayarlar.

| Kolon | Tip |
|-------|-----|
| Key | NVARCHAR(128) PK |
| Value | NVARCHAR(MAX) |
| UpdatedAt | DATETIME2 |

Seed:

- `review_validity_years` = `4` (dashboard)
- `unit_activity_map` = `{"KBU":"uyum","KBD":"denetim"}` (harita sembolleri)

---

## Stored Procedures

Önek: `usp_AssuranceMap_*`. Varsayılan `CommandType.StoredProcedure`.

### Universe

| SP | Parametreler | Sonuç | C# |
|----|--------------|-------|-----|
| `usp_AssuranceMap_Universe_ListByType` | `@UniverseType`, `@ActiveOnly` | Universe satırları | `UniverseRepository.ListByTypeAsync` |
| `usp_AssuranceMap_Universe_GetById` | `@Id` | Tek satır | `GetByIdAsync` |
| `usp_AssuranceMap_Universe_FindByName` | `@UniverseType`, `@Name` | Tek satır | `FindByNameAsync` |
| `usp_AssuranceMap_Universe_Insert` | `@UniverseType`, `@Name` | `{ Id }` | `InsertAsync` |
| `usp_AssuranceMap_Universe_UpdateName` | `@Id`, `@Name` | — | `UpdateNameAsync` |
| `usp_AssuranceMap_Universe_SetActive` | `@Id`, `@IsActive` | — | `SetActiveAsync` |
| `usp_AssuranceMap_Universe_DeleteIfNoReviews` | `@Id` | Hata: inceleme varsa | `DeleteIfNoReviewsAsync` |

### Review

| SP | Parametreler | Sonuç | C# |
|----|--------------|-------|-----|
| `usp_AssuranceMap_Review_ListByUniverse` | `@UniverseId` | Review listesi (tarih desc) | `ReviewRepository.ListByUniverseAsync` |
| `usp_AssuranceMap_Review_GetById` | `@Id` | Tek satır | `GetByIdAsync` |
| `usp_AssuranceMap_Review_FindDuplicate` | `@UniverseId`, `@ReviewSubject`, `@ReviewDate` | Tek satır / boş | `FindDuplicateAsync` |
| `usp_AssuranceMap_Review_Insert` | tüm review alanları | `{ Id }` | `InsertAsync` |
| `usp_AssuranceMap_Review_Update` | `@Id` + alanlar | — | `UpdateAsync` |
| `usp_AssuranceMap_Review_Delete` | `@Id` | — | `DeleteAsync` |
| `usp_AssuranceMap_Review_MaxReviewDate` | `@UniverseId` | `{ MaxReviewDate }` | `MaxReviewDateAsync` |

### FieldOption

| SP | Parametreler | Sonuç | C# |
|----|--------------|-------|-----|
| `usp_AssuranceMap_FieldOption_ListByKey` | `@FieldKey` | Tüm seçenekler | `FieldOptionRepository.ListByKeyAsync` |
| `usp_AssuranceMap_FieldOption_ListActiveByKey` | `@FieldKey` | Aktifler | `ListActiveByKeyAsync` |
| `usp_AssuranceMap_FieldOption_Insert` | `@FieldKey`, `@Value`, `@Label`, `@SortOrder` | `{ Id }` | `InsertAsync` |
| `usp_AssuranceMap_FieldOption_SetActive` | `@Id`, `@IsActive` | — | `SetActiveAsync` |
| `usp_AssuranceMap_FieldOption_IsInUse` | `@FieldKey`, `@Value` | `{ IsInUse }` | `IsInUseAsync` |

### Settings

| SP | Parametreler | Sonuç | C# |
|----|--------------|-------|-----|
| `usp_AssuranceMap_Settings_Get` | `@Key` | Tek satır | `AppSettingsRepository.GetAsync` |
| `usp_AssuranceMap_Settings_Upsert` | `@Key`, `@Value` | MERGE | `UpsertAsync` |

### Map / Dashboard aggregate

| SP | Parametreler | Sonuç | C# |
|----|--------------|-------|-----|
| `usp_AssuranceMap_Map_ListActiveWithReviews` | `@UniverseType` (nullable) | 1) Universes 2) Reviews | `MapQueryService.LoadActiveWithReviewsAsync` |

---

## İş kuralları (uygulama + SP)

- Harita renk penceresi: **sabit 3 yıl** (kod: `FieldKeys.MapWindowYears`).
- Dashboard geçerlilik: `review_validity_years` ayarı.
- Birim filtresi: Hepsi / KBD / KBU / KBD-KBU (Core `MapRules.FilterReviewsByUnit`).
- Entity hard-delete yalnızca inceleme yoksa (`DeleteIfNoReviews`).
