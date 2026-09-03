using System.Text.Json;
using DbConnection;

namespace AssuranceMap.Business;

public class SettingsService(AppSettingsRepository repo)
{
    public async Task<int> GetValidityYearsAsync()
    {
        var s = await repo.GetAsync(FieldKeys.SettingValidityYears);
        if (s is null || !int.TryParse(s.Value, out var y) || y < 1) return FieldKeys.DefaultValidityYears;
        return y;
    }

    public Task SetValidityYearsAsync(int years) =>
        repo.UpsertAsync(FieldKeys.SettingValidityYears, years.ToString());

    public async Task<Dictionary<string, string>> GetUnitActivityMapAsync()
    {
        var s = await repo.GetAsync(FieldKeys.SettingUnitActivityMap);
        if (s?.Value is null) return new Dictionary<string, string>(FieldKeys.DefaultUnitActivityMap);
        try
        {
            var map = JsonSerializer.Deserialize<Dictionary<string, string>>(s.Value);
            return map ?? new Dictionary<string, string>(FieldKeys.DefaultUnitActivityMap);
        }
        catch
        {
            return new Dictionary<string, string>(FieldKeys.DefaultUnitActivityMap);
        }
    }

    public Task SetUnitActivityMapAsync(Dictionary<string, string> map) =>
        repo.UpsertAsync(FieldKeys.SettingUnitActivityMap, JsonSerializer.Serialize(map));
}

public class MapQueryService(IDataAccess db)
{
    public async Task<(IReadOnlyList<Universe> Universes, IReadOnlyList<Review> Reviews)> LoadActiveWithReviewsAsync(string? universeType = null)
    {
        var multi = await db.GetMultiData<object>(
            "usp_AssuranceMap_Map_ListActiveWithReviews",
            new { UniverseType = universeType });
        try
        {
            var universes = (await multi.ReadAsync<Universe>()).ToList();
            var reviews = (await multi.ReadAsync<Review>()).ToList();
            return (universes, reviews);
        }
        finally
        {
            multi.Dispose();
        }
    }
}
