-- AssuranceMap SQL Server schema
-- Run against target database before deploying the Blazor app.

IF OBJECT_ID(N'dbo.Universes', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Universes
    (
        Id            INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_Universes PRIMARY KEY,
        UniverseType  NVARCHAR(32)  NOT NULL,
        Name          NVARCHAR(255) NOT NULL,
        IsActive      BIT           NOT NULL CONSTRAINT DF_Universes_IsActive DEFAULT (1),
        CreatedAt     DATETIME2(0)  NOT NULL CONSTRAINT DF_Universes_CreatedAt DEFAULT (SYSUTCDATETIME()),
        UpdatedAt     DATETIME2(0)  NOT NULL CONSTRAINT DF_Universes_UpdatedAt DEFAULT (SYSUTCDATETIME()),
        CONSTRAINT UQ_Universes_Type_Name UNIQUE (UniverseType, Name)
    );
END
GO

IF OBJECT_ID(N'dbo.Reviews', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Reviews
    (
        Id                     INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_Reviews PRIMARY KEY,
        UniverseId             INT           NOT NULL,
        ReviewSubject          NVARCHAR(500) NOT NULL,
        CoveredDecisionCount   INT           NOT NULL CONSTRAINT DF_Reviews_Covered DEFAULT (0),
        DecisionOwnership      NVARCHAR(255) NOT NULL CONSTRAINT DF_Reviews_Ownership DEFAULT (N''),
        Unit                   NVARCHAR(64)  NOT NULL,
        ReviewDate             DATE          NOT NULL,
        UnitDecisionCounts     NVARCHAR(MAX) NOT NULL CONSTRAINT DF_Reviews_UnitCounts DEFAULT (N''),
        ReviewStatus           NVARCHAR(64)  NOT NULL,
        AssuranceLevel         NVARCHAR(64)  NOT NULL,
        RiskLevel              NVARCHAR(64)  NOT NULL,
        ExaminationDepth       NVARCHAR(64)  NOT NULL CONSTRAINT DF_Reviews_Depth DEFAULT (N'tam'),
        CreatedAt              DATETIME2(0)  NOT NULL CONSTRAINT DF_Reviews_CreatedAt DEFAULT (SYSUTCDATETIME()),
        UpdatedAt              DATETIME2(0)  NOT NULL CONSTRAINT DF_Reviews_UpdatedAt DEFAULT (SYSUTCDATETIME()),
        CONSTRAINT FK_Reviews_Universes FOREIGN KEY (UniverseId) REFERENCES dbo.Universes(Id)
    );

    CREATE INDEX IX_Reviews_UniverseId ON dbo.Reviews(UniverseId);
    CREATE INDEX IX_Reviews_Unit ON dbo.Reviews(Unit);
    CREATE INDEX IX_Reviews_ReviewDate ON dbo.Reviews(ReviewDate);
END
GO

IF OBJECT_ID(N'dbo.FieldOptions', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.FieldOptions
    (
        Id         INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_FieldOptions PRIMARY KEY,
        FieldKey   NVARCHAR(64)  NOT NULL,
        Value      NVARCHAR(64)  NOT NULL,
        Label      NVARCHAR(128) NOT NULL,
        SortOrder  INT           NOT NULL CONSTRAINT DF_FieldOptions_Sort DEFAULT (0),
        IsActive   BIT           NOT NULL CONSTRAINT DF_FieldOptions_IsActive DEFAULT (1),
        CreatedAt  DATETIME2(0)  NOT NULL CONSTRAINT DF_FieldOptions_CreatedAt DEFAULT (SYSUTCDATETIME()),
        UpdatedAt  DATETIME2(0)  NOT NULL CONSTRAINT DF_FieldOptions_UpdatedAt DEFAULT (SYSUTCDATETIME()),
        CONSTRAINT UQ_FieldOptions_Key_Value UNIQUE (FieldKey, Value)
    );
END
GO

IF OBJECT_ID(N'dbo.AppSettings', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.AppSettings
    (
        [Key]     NVARCHAR(128) NOT NULL CONSTRAINT PK_AppSettings PRIMARY KEY,
        Value     NVARCHAR(MAX) NOT NULL,
        UpdatedAt DATETIME2(0)  NOT NULL CONSTRAINT DF_AppSettings_UpdatedAt DEFAULT (SYSUTCDATETIME())
    );
END
GO

MERGE dbo.AppSettings AS t
USING (VALUES
    (N'review_validity_years', N'4'),
    (N'unit_activity_map', N'{"KBU":"uyum","KBD":"denetim"}')
) AS s([Key], Value)
ON t.[Key] = s.[Key]
WHEN NOT MATCHED THEN INSERT ([Key], Value) VALUES (s.[Key], s.Value);
GO

MERGE dbo.FieldOptions AS t
USING (VALUES
    (N'unit', N'KBU', N'KBU', 1),
    (N'unit', N'KBD', N'KBD', 2),
    (N'review_status', N'planlandi', N'Planlandı', 1),
    (N'review_status', N'devam_ediyor', N'Devam Ediyor', 2),
    (N'review_status', N'tamamlandi', N'Tamamlandı', 3),
    (N'review_status', N'askida', N'Askıda', 4),
    (N'assurance_level', N'yuksek', N'Yüksek', 1),
    (N'assurance_level', N'makul', N'Makul', 2),
    (N'assurance_level', N'sinirli', N'Sınırlı', 3),
    (N'assurance_level', N'yetersiz', N'Yetersiz', 4),
    (N'risk_level', N'kritik', N'Kritik', 1),
    (N'risk_level', N'yuksek', N'Yüksek', 2),
    (N'risk_level', N'orta', N'Orta', 3),
    (N'risk_level', N'dusuk', N'Düşük', 4),
    (N'examination_depth', N'tam', N'Tam', 1),
    (N'examination_depth', N'kismi', N'Kısmi', 2)
) AS s(FieldKey, Value, Label, SortOrder)
ON t.FieldKey = s.FieldKey AND t.Value = s.Value
WHEN NOT MATCHED THEN
    INSERT (FieldKey, Value, Label, SortOrder, IsActive) VALUES (s.FieldKey, s.Value, s.Label, s.SortOrder, 1);
GO
