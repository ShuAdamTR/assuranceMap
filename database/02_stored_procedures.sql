-- AssuranceMap stored procedures
-- Prefix: usp_AssuranceMap_*

CREATE OR ALTER PROCEDURE dbo.usp_AssuranceMap_Universe_ListByType
    @UniverseType NVARCHAR(32),
    @ActiveOnly BIT = 1
AS
BEGIN
    SET NOCOUNT ON;
    SELECT Id, UniverseType, Name, IsActive, CreatedAt, UpdatedAt
    FROM dbo.Universes
    WHERE UniverseType = @UniverseType
      AND (@ActiveOnly = 0 OR IsActive = 1)
    ORDER BY Name;
END
GO

CREATE OR ALTER PROCEDURE dbo.usp_AssuranceMap_Universe_GetById
    @Id INT
AS
BEGIN
    SET NOCOUNT ON;
    SELECT Id, UniverseType, Name, IsActive, CreatedAt, UpdatedAt
    FROM dbo.Universes WHERE Id = @Id;
END
GO

CREATE OR ALTER PROCEDURE dbo.usp_AssuranceMap_Universe_FindByName
    @UniverseType NVARCHAR(32),
    @Name NVARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;
    SELECT Id, UniverseType, Name, IsActive, CreatedAt, UpdatedAt
    FROM dbo.Universes
    WHERE UniverseType = @UniverseType AND Name = @Name;
END
GO

CREATE OR ALTER PROCEDURE dbo.usp_AssuranceMap_Universe_Insert
    @UniverseType NVARCHAR(32),
    @Name NVARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO dbo.Universes (UniverseType, Name, IsActive)
    VALUES (@UniverseType, @Name, 1);
    SELECT CAST(SCOPE_IDENTITY() AS INT) AS Id;
END
GO

CREATE OR ALTER PROCEDURE dbo.usp_AssuranceMap_Universe_UpdateName
    @Id INT,
    @Name NVARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.Universes
    SET Name = @Name, UpdatedAt = SYSUTCDATETIME()
    WHERE Id = @Id;
END
GO

CREATE OR ALTER PROCEDURE dbo.usp_AssuranceMap_Universe_SetActive
    @Id INT,
    @IsActive BIT
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.Universes
    SET IsActive = @IsActive, UpdatedAt = SYSUTCDATETIME()
    WHERE Id = @Id;
END
GO

CREATE OR ALTER PROCEDURE dbo.usp_AssuranceMap_Universe_DeleteIfNoReviews
    @Id INT
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (SELECT 1 FROM dbo.Reviews WHERE UniverseId = @Id)
    BEGIN
        RAISERROR(N'İnceleme kaydı olan entity silinemez.', 16, 1);
        RETURN;
    END
    DELETE FROM dbo.Universes WHERE Id = @Id;
END
GO

CREATE OR ALTER PROCEDURE dbo.usp_AssuranceMap_Review_ListByUniverse
    @UniverseId INT
AS
BEGIN
    SET NOCOUNT ON;
    SELECT Id, UniverseId, ReviewSubject, CoveredDecisionCount, DecisionOwnership,
           Unit, ReviewDate, UnitDecisionCounts, ReviewStatus, AssuranceLevel,
           RiskLevel, ExaminationDepth, CreatedAt, UpdatedAt
    FROM dbo.Reviews
    WHERE UniverseId = @UniverseId
    ORDER BY ReviewDate DESC, Id DESC;
END
GO

CREATE OR ALTER PROCEDURE dbo.usp_AssuranceMap_Review_GetById
    @Id INT
AS
BEGIN
    SET NOCOUNT ON;
    SELECT Id, UniverseId, ReviewSubject, CoveredDecisionCount, DecisionOwnership,
           Unit, ReviewDate, UnitDecisionCounts, ReviewStatus, AssuranceLevel,
           RiskLevel, ExaminationDepth, CreatedAt, UpdatedAt
    FROM dbo.Reviews WHERE Id = @Id;
END
GO

CREATE OR ALTER PROCEDURE dbo.usp_AssuranceMap_Review_FindDuplicate
    @UniverseId INT,
    @ReviewSubject NVARCHAR(500),
    @ReviewDate DATE
AS
BEGIN
    SET NOCOUNT ON;
    SELECT TOP 1 Id, UniverseId, ReviewSubject, CoveredDecisionCount, DecisionOwnership,
           Unit, ReviewDate, UnitDecisionCounts, ReviewStatus, AssuranceLevel,
           RiskLevel, ExaminationDepth, CreatedAt, UpdatedAt
    FROM dbo.Reviews
    WHERE UniverseId = @UniverseId
      AND ReviewSubject = @ReviewSubject
      AND ReviewDate = @ReviewDate;
END
GO

CREATE OR ALTER PROCEDURE dbo.usp_AssuranceMap_Review_Insert
    @UniverseId INT,
    @ReviewSubject NVARCHAR(500),
    @CoveredDecisionCount INT,
    @DecisionOwnership NVARCHAR(255),
    @Unit NVARCHAR(64),
    @ReviewDate DATE,
    @UnitDecisionCounts NVARCHAR(MAX),
    @ReviewStatus NVARCHAR(64),
    @AssuranceLevel NVARCHAR(64),
    @RiskLevel NVARCHAR(64),
    @ExaminationDepth NVARCHAR(64)
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO dbo.Reviews
    (UniverseId, ReviewSubject, CoveredDecisionCount, DecisionOwnership, Unit, ReviewDate,
     UnitDecisionCounts, ReviewStatus, AssuranceLevel, RiskLevel, ExaminationDepth)
    VALUES
    (@UniverseId, @ReviewSubject, @CoveredDecisionCount, @DecisionOwnership, @Unit, @ReviewDate,
     @UnitDecisionCounts, @ReviewStatus, @AssuranceLevel, @RiskLevel, @ExaminationDepth);
    SELECT CAST(SCOPE_IDENTITY() AS INT) AS Id;
END
GO

CREATE OR ALTER PROCEDURE dbo.usp_AssuranceMap_Review_Update
    @Id INT,
    @ReviewSubject NVARCHAR(500),
    @CoveredDecisionCount INT,
    @DecisionOwnership NVARCHAR(255),
    @Unit NVARCHAR(64),
    @ReviewDate DATE,
    @UnitDecisionCounts NVARCHAR(MAX),
    @ReviewStatus NVARCHAR(64),
    @AssuranceLevel NVARCHAR(64),
    @RiskLevel NVARCHAR(64),
    @ExaminationDepth NVARCHAR(64)
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.Reviews SET
        ReviewSubject = @ReviewSubject,
        CoveredDecisionCount = @CoveredDecisionCount,
        DecisionOwnership = @DecisionOwnership,
        Unit = @Unit,
        ReviewDate = @ReviewDate,
        UnitDecisionCounts = @UnitDecisionCounts,
        ReviewStatus = @ReviewStatus,
        AssuranceLevel = @AssuranceLevel,
        RiskLevel = @RiskLevel,
        ExaminationDepth = @ExaminationDepth,
        UpdatedAt = SYSUTCDATETIME()
    WHERE Id = @Id;
END
GO

CREATE OR ALTER PROCEDURE dbo.usp_AssuranceMap_Review_Delete
    @Id INT
AS
BEGIN
    SET NOCOUNT ON;
    DELETE FROM dbo.Reviews WHERE Id = @Id;
END
GO

CREATE OR ALTER PROCEDURE dbo.usp_AssuranceMap_Review_MaxReviewDate
    @UniverseId INT
AS
BEGIN
    SET NOCOUNT ON;
    SELECT MAX(ReviewDate) AS MaxReviewDate FROM dbo.Reviews WHERE UniverseId = @UniverseId;
END
GO

CREATE OR ALTER PROCEDURE dbo.usp_AssuranceMap_FieldOption_ListByKey
    @FieldKey NVARCHAR(64)
AS
BEGIN
    SET NOCOUNT ON;
    SELECT Id, FieldKey, Value, Label, SortOrder, IsActive
    FROM dbo.FieldOptions
    WHERE FieldKey = @FieldKey
    ORDER BY SortOrder, Label;
END
GO

CREATE OR ALTER PROCEDURE dbo.usp_AssuranceMap_FieldOption_ListActiveByKey
    @FieldKey NVARCHAR(64)
AS
BEGIN
    SET NOCOUNT ON;
    SELECT Id, FieldKey, Value, Label, SortOrder, IsActive
    FROM dbo.FieldOptions
    WHERE FieldKey = @FieldKey AND IsActive = 1
    ORDER BY SortOrder, Label;
END
GO

CREATE OR ALTER PROCEDURE dbo.usp_AssuranceMap_FieldOption_Insert
    @FieldKey NVARCHAR(64),
    @Value NVARCHAR(64),
    @Label NVARCHAR(128),
    @SortOrder INT
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO dbo.FieldOptions (FieldKey, Value, Label, SortOrder, IsActive)
    VALUES (@FieldKey, @Value, @Label, @SortOrder, 1);
    SELECT CAST(SCOPE_IDENTITY() AS INT) AS Id;
END
GO

CREATE OR ALTER PROCEDURE dbo.usp_AssuranceMap_FieldOption_SetActive
    @Id INT,
    @IsActive BIT
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.FieldOptions
    SET IsActive = @IsActive, UpdatedAt = SYSUTCDATETIME()
    WHERE Id = @Id;
END
GO

CREATE OR ALTER PROCEDURE dbo.usp_AssuranceMap_FieldOption_IsInUse
    @FieldKey NVARCHAR(64),
    @Value NVARCHAR(64)
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @Used BIT = 0;
    IF @FieldKey = N'unit' AND EXISTS (SELECT 1 FROM dbo.Reviews WHERE Unit = @Value) SET @Used = 1;
    IF @FieldKey = N'review_status' AND EXISTS (SELECT 1 FROM dbo.Reviews WHERE ReviewStatus = @Value) SET @Used = 1;
    IF @FieldKey = N'assurance_level' AND EXISTS (SELECT 1 FROM dbo.Reviews WHERE AssuranceLevel = @Value) SET @Used = 1;
    IF @FieldKey = N'risk_level' AND EXISTS (SELECT 1 FROM dbo.Reviews WHERE RiskLevel = @Value) SET @Used = 1;
    IF @FieldKey = N'examination_depth' AND EXISTS (SELECT 1 FROM dbo.Reviews WHERE ExaminationDepth = @Value) SET @Used = 1;
    SELECT @Used AS IsInUse;
END
GO

CREATE OR ALTER PROCEDURE dbo.usp_AssuranceMap_Settings_Get
    @Key NVARCHAR(128)
AS
BEGIN
    SET NOCOUNT ON;
    SELECT [Key], Value, UpdatedAt FROM dbo.AppSettings WHERE [Key] = @Key;
END
GO

CREATE OR ALTER PROCEDURE dbo.usp_AssuranceMap_Settings_Upsert
    @Key NVARCHAR(128),
    @Value NVARCHAR(MAX)
AS
BEGIN
    SET NOCOUNT ON;
    MERGE dbo.AppSettings AS t
    USING (SELECT @Key AS [Key], @Value AS Value) AS s
    ON t.[Key] = s.[Key]
    WHEN MATCHED THEN UPDATE SET Value = s.Value, UpdatedAt = SYSUTCDATETIME()
    WHEN NOT MATCHED THEN INSERT ([Key], Value) VALUES (s.[Key], s.Value);
END
GO

CREATE OR ALTER PROCEDURE dbo.usp_AssuranceMap_Map_ListActiveWithReviews
    @UniverseType NVARCHAR(32) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    -- Result set 1: universes
    SELECT Id, UniverseType, Name, IsActive, CreatedAt, UpdatedAt
    FROM dbo.Universes
    WHERE IsActive = 1
      AND (@UniverseType IS NULL OR UniverseType = @UniverseType)
    ORDER BY UniverseType, Name;

    -- Result set 2: reviews for those universes
    SELECT r.Id, r.UniverseId, r.ReviewSubject, r.CoveredDecisionCount, r.DecisionOwnership,
           r.Unit, r.ReviewDate, r.UnitDecisionCounts, r.ReviewStatus, r.AssuranceLevel,
           r.RiskLevel, r.ExaminationDepth, r.CreatedAt, r.UpdatedAt
    FROM dbo.Reviews r
    INNER JOIN dbo.Universes u ON u.Id = r.UniverseId
    WHERE u.IsActive = 1
      AND (@UniverseType IS NULL OR u.UniverseType = @UniverseType);
END
GO
