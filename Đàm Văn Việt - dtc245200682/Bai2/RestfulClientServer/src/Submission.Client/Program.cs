using System.Net;
using System.Net.Http.Json;
using System.Text.Json;

var address = args.FirstOrDefault() ?? "http://localhost:5000";
if (!Uri.TryCreate(address, UriKind.Absolute, out var baseUri) ||
    (baseUri.Scheme != "http" && baseUri.Scheme != "https"))
{
    Console.WriteLine("URL API phai la dia chi HTTP/HTTPS tuyet doi.");
    Environment.ExitCode = 1;
    return;
}
using var http = new HttpClient { BaseAddress = baseUri, Timeout = TimeSpan.FromSeconds(10) };
try
{
    using var listResponse = await http.GetAsync("/api/assignments");
    if (listResponse.StatusCode != HttpStatusCode.OK) { await PrintApiErrorAsync(listResponse); Environment.ExitCode = 1; return; }
    var assignments = await listResponse.Content.ReadFromJsonAsync<List<AssignmentDto>>();
    if (assignments is null) throw new InvalidOperationException("API tra danh sach null.");
    Console.WriteLine("1. HTTP 200 - Danh sach bai tap dang mo:");
    foreach (var a in assignments?.Where(a => a.IsOpen) ?? []) Console.WriteLine($"- {a.Id}: {a.Title}");
    var selected = assignments?.FirstOrDefault(a => a.IsOpen);
    if (selected is null) { Console.WriteLine("Khong co bai tap dang mo."); return; }
    using var response = await http.PostAsJsonAsync($"/api/assignments/{selected.Id}/submissions",
        new CreateSubmissionRequest("SV001", "https://example.com/sv001/rest-api"));
    if (response.StatusCode != HttpStatusCode.Created) { await PrintApiErrorAsync(response); Environment.ExitCode = 1; return; }
    var created = await response.Content.ReadFromJsonAsync<SubmissionDto>();
    if (created is null || created.Id == Guid.Empty || created.AssignmentId != selected.Id || created.Status != "received")
        throw new InvalidOperationException("Du lieu luot nop khong dung hop dong.");
    Console.WriteLine($"2. HTTP 201 - Da tao luot nop: {created.Id}; trang thai: {created.Status}");
    Console.WriteLine($"Location: {response.Headers.Location}");
    if (response.Headers.Location is not { } location) throw new InvalidOperationException("API khong tra Location.");
    using var detailResponse = await http.GetAsync(location);
    if (detailResponse.StatusCode != HttpStatusCode.OK) { await PrintApiErrorAsync(detailResponse); Environment.ExitCode = 1; return; }
    var detail = await detailResponse.Content.ReadFromJsonAsync<SubmissionDto>();
    if (detail != created) throw new InvalidOperationException("Du lieu doc lai khong khop luot nop vua tao.");
    Console.WriteLine($"3. HTTP 200 - Doc lai luot nop: {detail.StudentCode} - {detail.RepositoryUrl}");
    using var invalidResponse = await http.PostAsJsonAsync($"/api/assignments/{selected.Id}/submissions", new CreateSubmissionRequest("", ""));
    Console.WriteLine("4. Thu gui yeu cau loi:");
    await PrintApiErrorAsync(invalidResponse);
    if (invalidResponse.StatusCode != HttpStatusCode.BadRequest)
        throw new InvalidOperationException("Yeu cau rong phai nhan HTTP 400.");
}
catch (HttpRequestException ex) { Console.WriteLine($"Loi ket noi: {ex.Message}"); Environment.ExitCode = 1; }
catch (TaskCanceledException) { Console.WriteLine("Het thoi gian cho API."); Environment.ExitCode = 1; }
catch (JsonException ex) { Console.WriteLine($"JSON tu API khong dung hop dong: {ex.Message}"); Environment.ExitCode = 1; }
catch (InvalidOperationException ex) { Console.WriteLine($"Loi hop dong API: {ex.Message}"); Environment.ExitCode = 1; }

static async Task PrintApiErrorAsync(HttpResponseMessage response)
{
    Console.WriteLine($"HTTP {(int)response.StatusCode} {response.StatusCode}");
    var body = await response.Content.ReadAsStringAsync();
    try
    {
        var error = JsonSerializer.Deserialize<ApiError>(body, new JsonSerializerOptions(JsonSerializerDefaults.Web));
        Console.WriteLine($"{error?.Code}: {error?.Message}");
    }
    catch (JsonException) { Console.WriteLine(string.IsNullOrWhiteSpace(body) ? "Phan hoi khong co body JSON." : body); }
}
record AssignmentDto(int Id, string Title, string Description, bool IsOpen);
record CreateSubmissionRequest(string StudentCode, string RepositoryUrl);
record SubmissionDto(Guid Id, int AssignmentId, string StudentCode, string RepositoryUrl, string Status, DateTimeOffset ReceivedAt);
record ApiError(string Code, string Message);
