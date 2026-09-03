namespace AssuranceMap.Business;

public static class FieldKeys
{
    public const string Unit = "unit";
    public const string ReviewStatus = "review_status";
    public const string AssuranceLevel = "assurance_level";
    public const string RiskLevel = "risk_level";
    public const string ExaminationDepth = "examination_depth";

    public const string DepthTam = "tam";
    public const string DepthKismi = "kismi";

    public const string ActivityUyum = "uyum";
    public const string ActivityDenetim = "denetim";

    public const string SettingValidityYears = "review_validity_years";
    public const string SettingUnitActivityMap = "unit_activity_map";

    public const int MapWindowYears = 3;
    public const int DefaultValidityYears = 4;

    public static readonly IReadOnlyDictionary<string, string> DefaultUnitActivityMap =
        new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase)
        {
            ["KBU"] = ActivityUyum,
            ["KBD"] = ActivityDenetim,
        };
}
