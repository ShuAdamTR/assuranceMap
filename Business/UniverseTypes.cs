namespace AssuranceMap.Business;

public static class UniverseTypes
{
    public const string Istirak = "istirak";
    public const string Mudurluk = "mudurluk";
    public const string Urun = "urun";

    public static readonly IReadOnlyDictionary<string, string> Labels = new Dictionary<string, string>
    {
        [Istirak] = "İştirak",
        [Mudurluk] = "Müdürlük",
        [Urun] = "Ürün",
    };

    public static IEnumerable<string> All => Labels.Keys;
}
