using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading.Tasks;

namespace Vatlog
{
    public record LogEntry(
        [property: JsonPropertyName("fir")]     string Fir,
        [property: JsonPropertyName("time")]    string Time,
        [property: JsonPropertyName("average")] double Average,
        [property: JsonPropertyName("count")]   int    Count
    );

    public record LogPayload(
        [property: JsonPropertyName("fir")]   string Fir,
        [property: JsonPropertyName("time")]  string Time,
        [property: JsonPropertyName("value")] int    Value
    );

    public class VatlogApiClient : IDisposable
    {
        private const string BaseUrl = "https://vatlog-api-production.up.railway.app";
        private static readonly TimeSpan CacheTtl = TimeSpan.FromMinutes(5);

        private static readonly JsonSerializerOptions JsonOpts = new()
        {
            PropertyNameCaseInsensitive = true
        };

        private readonly HttpClient _http;
        private List<LogEntry>? _cache;
        private DateTime _cacheExpiry = DateTime.MinValue;

        public VatlogApiClient(string readKey)
        {
            if (string.IsNullOrWhiteSpace(readKey))
                throw new ArgumentException("Read API key must not be empty.", nameof(readKey));

            _http = new HttpClient();
            _http.DefaultRequestHeaders.Add("X-API-Key", readKey);
        }
        
        // Public API

        public async Task<List<LogEntry>> GetAllLogsAsync()
        {
            if (_cache != null && DateTime.UtcNow < _cacheExpiry)
                return _cache;

            var response = await _http.GetAsync($"{BaseUrl}/logs");
            response.EnsureSuccessStatusCode();

            var json = await response.Content.ReadAsStringAsync();
            _cache = JsonSerializer.Deserialize<List<LogEntry>>(json, JsonOpts)
                     ?? throw new InvalidOperationException("API returned null log list.");

            _cacheExpiry = DateTime.UtcNow.Add(CacheTtl);
            return _cache;
        }

        public async Task<IEnumerable<LogEntry>> GetLogsByFirAsync(string fir)
        {
            if (string.IsNullOrWhiteSpace(fir))
                throw new ArgumentException("FIR identifier must not be empty.", nameof(fir));

            var all = await GetAllLogsAsync();
            return all.Where(e => e.Fir.Equals(fir, StringComparison.OrdinalIgnoreCase));
        }

        public async Task<IEnumerable<LogEntry>> GetLogsByTimeAsync(string time)
        {
            if (string.IsNullOrWhiteSpace(time))
                throw new ArgumentException("Time string must not be empty.", nameof(time));

            var all = await GetAllLogsAsync();
            return all.Where(e => e.Time == time);
        }

        public async Task<LogEntry?> GetSingleEntryAsync(string fir, string time)
        {
            var all = await GetAllLogsAsync();
            return all.FirstOrDefault(e =>
                e.Fir.Equals(fir, StringComparison.OrdinalIgnoreCase) &&
                e.Time == time);
        }

        public async Task PostLogsAsync(List<LogPayload> batch, string writeKey)
        {
            if (batch == null || batch.Count == 0)
                throw new ArgumentException("Batch must contain at least one entry.", nameof(batch));
            if (string.IsNullOrWhiteSpace(writeKey))
                throw new ArgumentException("Write API key must not be empty.", nameof(writeKey));

            using var request = new HttpRequestMessage(HttpMethod.Post, $"{BaseUrl}/logs");
            request.Headers.Add("X-API-Key", writeKey);

            var json = JsonSerializer.Serialize(batch, JsonOpts);
            request.Content = new StringContent(json, Encoding.UTF8, "application/json");

            var response = await _http.SendAsync(request);
            response.EnsureSuccessStatusCode();
        }

        public void InvalidateCache()
        {
            _cache = null;
            _cacheExpiry = DateTime.MinValue;
        }

        public void Dispose()
        {
            _http.Dispose();
            GC.SuppressFinalize(this);
        }
    }
}
