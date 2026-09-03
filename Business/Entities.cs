namespace AssuranceMap.Business;

public class Universe
{
    public int Id { get; set; }
    public string UniverseType { get; set; } = "";
    public string Name { get; set; } = "";
    public bool IsActive { get; set; } = true;
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
}

public class Review
{
    public int Id { get; set; }
    public int UniverseId { get; set; }
    public string ReviewSubject { get; set; } = "";
    public int CoveredDecisionCount { get; set; }
    public string DecisionOwnership { get; set; } = "";
    public string Unit { get; set; } = "";
    public DateTime ReviewDate { get; set; }
    public string UnitDecisionCounts { get; set; } = "";
    public string ReviewStatus { get; set; } = "";
    public string AssuranceLevel { get; set; } = "";
    public string RiskLevel { get; set; } = "";
    public string ExaminationDepth { get; set; } = FieldKeys.DepthTam;
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
}

public class FieldOption
{
    public int Id { get; set; }
    public string FieldKey { get; set; } = "";
    public string Value { get; set; } = "";
    public string Label { get; set; } = "";
    public int SortOrder { get; set; }
    public bool IsActive { get; set; } = true;
}

public class AppSetting
{
    public string Key { get; set; } = "";
    public string Value { get; set; } = "";
}
