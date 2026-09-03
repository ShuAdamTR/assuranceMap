namespace AssuranceMap.Business;

public static class DateRules
{
    public static DateTime AddYears(DateTime d, int years)
    {
        try
        {
            return d.AddYears(years);
        }
        catch (ArgumentOutOfRangeException)
        {
            return new DateTime(d.Year + years, 2, 28);
        }
    }

    public static bool IsExpired(DateTime lastDate, DateTime asOf, int validityYears)
    {
        var threshold = AddYears(lastDate.Date, validityYears);
        return asOf.Date >= threshold;
    }

    public static bool InMapWindow(DateTime reviewDate, DateTime asOf) =>
        !IsExpired(reviewDate.Date, asOf.Date, FieldKeys.MapWindowYears);
}
