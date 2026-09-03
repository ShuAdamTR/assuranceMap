namespace AssuranceMap.Business;

public static class MapColors
{
    public const string MultiFull = "#70AD47";
    public const string MultiMixed = "#A9D08E";
    public const string OnceFull = "#C6E0B4";
    public const string OncePartial = "#E2EFDA";
    public const string OldOnly = "#FFD966";
    public const string Never = "#D9D9D9";

    public static readonly IReadOnlyDictionary<string, string> Labels = new Dictionary<string, string>
    {
        [MultiFull] = "Son 3 yılda birden fazla ve tam incelendi",
        [MultiMixed] = "Son 3 yılda birden fazla; tam + kısmi karışık",
        [OnceFull] = "Son 3 yılda bir defa ve tam incelendi",
        [OncePartial] = "Son 3 yılda bir defa ve kısmi incelendi",
        [OldOnly] = "Yalnızca son 3 yıl dışında incelendi",
        [Never] = "Hiç inceleme kapsamına alınmadı",
    };
}

public static class MapSymbols
{
    public const string BothRecent = "◆";
    public const string BothOld = "◇";
    public const string UyumRecent = "■";
    public const string UyumOld = "□";
    public const string DenetimRecent = "▲";
    public const string DenetimOld = "△";

    public static readonly IReadOnlyDictionary<string, string> Labels = new Dictionary<string, string>
    {
        [BothRecent] = "Son 3 yılda hem Uyum hem Denetim (örtüşme)",
        [BothOld] = "Son 3 yıldan önce hem Uyum hem Denetim (örtüşme)",
        [UyumRecent] = "Son 3 yılda Uyum",
        [UyumOld] = "Son 3 yıldan önce Uyum",
        [DenetimRecent] = "Son 3 yılda Denetim",
        [DenetimOld] = "Son 3 yıldan önce Denetim",
    };
}

public static class MapRules
{
    public static IReadOnlyList<Review> FilterReviewsByUnit(
        IEnumerable<Review> reviews,
        string? unitFilter)
    {
        var list = reviews.ToList();
        if (string.IsNullOrWhiteSpace(unitFilter)
            || unitFilter is "all" or "hepsi" or "tumu")
            return list;

        var key = unitFilter.Trim().ToLowerInvariant().Replace(" ", "").Replace("_", "-");
        if (key is "both" or "kbd-kbu" or "kbu-kbd" or "kbdkbu" or "kbukbd")
        {
            var kbu = list.Where(r => r.Unit.Equals("KBU", StringComparison.OrdinalIgnoreCase)).ToList();
            var kbd = list.Where(r => r.Unit.Equals("KBD", StringComparison.OrdinalIgnoreCase)).ToList();
            if (kbu.Count > 0 && kbd.Count > 0)
                return kbu.Concat(kbd).ToList();
            return Array.Empty<Review>();
        }

        return list.Where(r => r.Unit.Equals(unitFilter.Trim(), StringComparison.OrdinalIgnoreCase)).ToList();
    }

    public static string ResolveColor(
        IEnumerable<Review> reviews,
        DateTime? asOf = null,
        string? unitFilter = null)
    {
        var day = (asOf ?? DateTime.Today).Date;
        var scoped = FilterReviewsByUnit(reviews, unitFilter);
        if (scoped.Count == 0) return MapColors.Never;

        var recent = scoped.Where(r => DateRules.InMapWindow(r.ReviewDate, day)).ToList();
        if (recent.Count == 0) return MapColors.OldOnly;

        var depths = recent.Select(r => r.ExaminationDepth ?? "").ToList();
        var allFull = depths.All(d => d == FieldKeys.DepthTam);
        var anyFull = depths.Any(d => d == FieldKeys.DepthTam);
        var anyPartial = depths.Any(d => d == FieldKeys.DepthKismi);

        if (recent.Count >= 2)
        {
            if (allFull) return MapColors.MultiFull;
            if (anyFull && anyPartial) return MapColors.MultiMixed;
            return MapColors.MultiMixed;
        }

        return depths[0] == FieldKeys.DepthTam ? MapColors.OnceFull : MapColors.OncePartial;
    }

    public static string ResolveSymbol(
        IEnumerable<Review> reviews,
        IReadOnlyDictionary<string, string> unitActivityMap,
        DateTime? asOf = null,
        string? unitFilter = null)
    {
        var day = (asOf ?? DateTime.Today).Date;
        var scoped = FilterReviewsByUnit(reviews, unitFilter);
        if (scoped.Count == 0) return "";

        string? Activity(string unit)
        {
            if (unitActivityMap.TryGetValue(unit, out var a)) return a;
            foreach (var kv in unitActivityMap)
            {
                if (kv.Key.Equals(unit, StringComparison.OrdinalIgnoreCase))
                    return kv.Value;
            }
            return null;
        }

        var recentUyum = false;
        var recentDenetim = false;
        var oldUyum = false;
        var oldDenetim = false;

        foreach (var r in scoped)
        {
            var act = Activity(r.Unit);
            if (act is null) continue;
            if (DateRules.InMapWindow(r.ReviewDate, day))
            {
                if (act == FieldKeys.ActivityUyum) recentUyum = true;
                else if (act == FieldKeys.ActivityDenetim) recentDenetim = true;
            }
            else
            {
                if (act == FieldKeys.ActivityUyum) oldUyum = true;
                else if (act == FieldKeys.ActivityDenetim) oldDenetim = true;
            }
        }

        if (recentUyum && recentDenetim) return MapSymbols.BothRecent;
        if (recentUyum) return MapSymbols.UyumRecent;
        if (recentDenetim) return MapSymbols.DenetimRecent;
        if (oldUyum && oldDenetim) return MapSymbols.BothOld;
        if (oldUyum) return MapSymbols.UyumOld;
        if (oldDenetim) return MapSymbols.DenetimOld;
        return "";
    }
}

public static class DashboardStatus
{
    public const string Gray = "GRAY";
    public const string Green = "GREEN";
    public const string Orange = "ORANGE";

    public static string Resolve(DateTime? lastAuditDate, DateTime asOf, int validityYears)
    {
        if (lastAuditDate is null) return Gray;
        return DateRules.IsExpired(lastAuditDate.Value, asOf, validityYears) ? Orange : Green;
    }

    public static string Hex(string status) => status switch
    {
        Green => "#16a34a",
        Orange => "#ea580c",
        _ => "#9ca3af",
    };
}
