using DbConnection;

namespace AssuranceMap.Business;

public class AppSettingsRepository(IDataAccess db)
{
    public Task<AppSetting> GetAsync(string key) =>
        db.GetSingleRow<AppSetting, object>("usp_AssuranceMap_Settings_Get", new { Key = key });

    public Task UpsertAsync(string key, string value) =>
        db.SaveData("usp_AssuranceMap_Settings_Upsert", new { Key = key, Value = value });
}
