using Microsoft.Extensions.DependencyInjection;

namespace AssuranceMap.Business;

/// <summary>
/// Hedef Blazor projesinde Program.cs içine: services.AddAssuranceMap();
/// IDataAccess (Okyanus DbConnection) zaten kayıtlı olmalı.
/// </summary>
public static class AssuranceMapRegistration
{
    public static IServiceCollection AddAssuranceMap(this IServiceCollection services)
    {
        services.AddScoped<UniverseRepository>();
        services.AddScoped<ReviewRepository>();
        services.AddScoped<FieldOptionRepository>();
        services.AddScoped<AppSettingsRepository>();
        services.AddScoped<MapQueryService>();
        services.AddScoped<SettingsService>();
        return services;
    }
}
