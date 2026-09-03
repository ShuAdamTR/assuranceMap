using DbConnection;

namespace AssuranceMap.Business;

public class FieldOptionRepository(IDataAccess db)
{
    public Task<IEnumerable<FieldOption>> ListByKeyAsync(string fieldKey) =>
        db.GetAllData<FieldOption, object>("usp_AssuranceMap_FieldOption_ListByKey", new { FieldKey = fieldKey });

    public Task<IEnumerable<FieldOption>> ListActiveByKeyAsync(string fieldKey) =>
        db.GetAllData<FieldOption, object>("usp_AssuranceMap_FieldOption_ListActiveByKey", new { FieldKey = fieldKey });

    public async Task<int> InsertAsync(string fieldKey, string value, string label, int sortOrder)
    {
        var row = await db.GetSingleRow<IdRow, object>(
            "usp_AssuranceMap_FieldOption_Insert",
            new { FieldKey = fieldKey, Value = value, Label = label, SortOrder = sortOrder });
        return row.Id;
    }

    public Task SetActiveAsync(int id, bool isActive) =>
        db.SaveData("usp_AssuranceMap_FieldOption_SetActive", new { Id = id, IsActive = isActive });

    public async Task<bool> IsInUseAsync(string fieldKey, string value)
    {
        var row = await db.GetSingleRow<InUseRow, object>(
            "usp_AssuranceMap_FieldOption_IsInUse",
            new { FieldKey = fieldKey, Value = value });
        return row?.IsInUse ?? false;
    }

    private sealed class IdRow { public int Id { get; set; } }
    private sealed class InUseRow { public bool IsInUse { get; set; } }
}
