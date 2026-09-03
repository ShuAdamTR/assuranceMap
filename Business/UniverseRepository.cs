using DbConnection;

namespace AssuranceMap.Business;

public class UniverseRepository(IDataAccess db)
{
    public Task<IEnumerable<Universe>> ListByTypeAsync(string universeType, bool activeOnly = true) =>
        db.GetAllData<Universe, object>(
            "usp_AssuranceMap_Universe_ListByType",
            new { UniverseType = universeType, ActiveOnly = activeOnly });

    public Task<Universe> GetByIdAsync(int id) =>
        db.GetSingleRow<Universe, object>("usp_AssuranceMap_Universe_GetById", new { Id = id });

    public Task<Universe> FindByNameAsync(string universeType, string name) =>
        db.GetSingleRow<Universe, object>(
            "usp_AssuranceMap_Universe_FindByName",
            new { UniverseType = universeType, Name = name });

    public async Task<int> InsertAsync(string universeType, string name)
    {
        var row = await db.GetSingleRow<IdRow, object>(
            "usp_AssuranceMap_Universe_Insert",
            new { UniverseType = universeType, Name = name });
        return row.Id;
    }

    public Task UpdateNameAsync(int id, string name) =>
        db.SaveData("usp_AssuranceMap_Universe_UpdateName", new { Id = id, Name = name });

    public Task SetActiveAsync(int id, bool isActive) =>
        db.SaveData("usp_AssuranceMap_Universe_SetActive", new { Id = id, IsActive = isActive });

    public Task DeleteIfNoReviewsAsync(int id) =>
        db.SaveData("usp_AssuranceMap_Universe_DeleteIfNoReviews", new { Id = id });

    private sealed class IdRow { public int Id { get; set; } }
}
