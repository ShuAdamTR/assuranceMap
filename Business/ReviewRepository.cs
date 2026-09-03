using DbConnection;

namespace AssuranceMap.Business;

public class ReviewRepository(IDataAccess db)
{
    public Task<IEnumerable<Review>> ListByUniverseAsync(int universeId) =>
        db.GetAllData<Review, object>("usp_AssuranceMap_Review_ListByUniverse", new { UniverseId = universeId });

    public Task<Review> GetByIdAsync(int id) =>
        db.GetSingleRow<Review, object>("usp_AssuranceMap_Review_GetById", new { Id = id });

    public Task<Review> FindDuplicateAsync(int universeId, string subject, DateTime reviewDate) =>
        db.GetSingleRow<Review, object>(
            "usp_AssuranceMap_Review_FindDuplicate",
            new { UniverseId = universeId, ReviewSubject = subject, ReviewDate = reviewDate.Date });

    public async Task<int> InsertAsync(Review review)
    {
        var row = await db.GetSingleRow<IdRow, object>("usp_AssuranceMap_Review_Insert", new
        {
            review.UniverseId,
            review.ReviewSubject,
            review.CoveredDecisionCount,
            review.DecisionOwnership,
            review.Unit,
            ReviewDate = review.ReviewDate.Date,
            review.UnitDecisionCounts,
            review.ReviewStatus,
            review.AssuranceLevel,
            review.RiskLevel,
            review.ExaminationDepth
        });
        return row.Id;
    }

    public Task UpdateAsync(Review review) =>
        db.SaveData("usp_AssuranceMap_Review_Update", new
        {
            review.Id,
            review.ReviewSubject,
            review.CoveredDecisionCount,
            review.DecisionOwnership,
            review.Unit,
            ReviewDate = review.ReviewDate.Date,
            review.UnitDecisionCounts,
            review.ReviewStatus,
            review.AssuranceLevel,
            review.RiskLevel,
            review.ExaminationDepth
        });

    public Task DeleteAsync(int id) =>
        db.SaveData("usp_AssuranceMap_Review_Delete", new { Id = id });

    public async Task<DateTime?> MaxReviewDateAsync(int universeId)
    {
        var row = await db.GetSingleRow<MaxDateRow, object>(
            "usp_AssuranceMap_Review_MaxReviewDate", new { UniverseId = universeId });
        return row?.MaxReviewDate;
    }

    private sealed class IdRow { public int Id { get; set; } }
    private sealed class MaxDateRow { public DateTime? MaxReviewDate { get; set; } }
}
