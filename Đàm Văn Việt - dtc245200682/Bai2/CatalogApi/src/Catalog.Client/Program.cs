using System.Net;
using System.Net.Http.Json;

var address = args.FirstOrDefault() ?? "http://localhost:5100";
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
    using var listResponse = await http.GetAsync("/api/products");
    if (listResponse.StatusCode != HttpStatusCode.OK) { await PrintErrorAsync(listResponse); Environment.ExitCode = 1; return; }
    var products = await listResponse.Content.ReadFromJsonAsync<List<ProductDto>>();
    if (products is null) throw new InvalidOperationException("API tra danh sach null.");
    Console.WriteLine("1. HTTP 200 - Danh sach san pham:");
    foreach (var p in products ?? []) Console.WriteLine($"[{p.Id}] {p.Name} - {p.Price:N0} VND");
    using var response = await http.PostAsJsonAsync("/api/products", new CreateProductRequest("Nhap mon REST API", "Sach tham khao", 120000));
    if (response.StatusCode != HttpStatusCode.Created) { await PrintErrorAsync(response); Environment.ExitCode = 1; return; }
    var created = await response.Content.ReadFromJsonAsync<ProductDto>();
    if (created is null || created.Id <= 0) throw new InvalidOperationException("Du lieu san pham khong dung hop dong.");
    Console.WriteLine($"2. HTTP 201 - Da tao: [{created.Id}] {created.Name}; Location: {response.Headers.Location}");
    if (response.Headers.Location is not { } location) throw new InvalidOperationException("API khong tra Location.");
    using var detailResponse = await http.GetAsync(location);
    if (detailResponse.StatusCode != HttpStatusCode.OK) { await PrintErrorAsync(detailResponse); Environment.ExitCode = 1; return; }
    var detail = await detailResponse.Content.ReadFromJsonAsync<ProductDto>();
    if (detail != created) throw new InvalidOperationException("Du lieu doc lai khong khop san pham vua tao.");
    Console.WriteLine($"3. HTTP 200 - Doc lai: [{detail.Id}] {detail.Name}");
    using var invalidResponse = await http.PostAsJsonAsync("/api/products", new CreateProductRequest("", "", -1));
    Console.WriteLine("4. Thu gui du lieu sai:");
    await PrintErrorAsync(invalidResponse);
    if (invalidResponse.StatusCode != HttpStatusCode.BadRequest)
        throw new InvalidOperationException("Yeu cau sai phai nhan HTTP 400.");
}
catch (HttpRequestException ex) { Console.WriteLine($"Loi ket noi: {ex.Message}"); Environment.ExitCode = 1; }
catch (TaskCanceledException) { Console.WriteLine("Het thoi gian cho API."); Environment.ExitCode = 1; }
catch (System.Text.Json.JsonException ex) { Console.WriteLine($"JSON tu API khong dung hop dong: {ex.Message}"); Environment.ExitCode = 1; }
catch (InvalidOperationException ex) { Console.WriteLine($"Loi hop dong API: {ex.Message}"); Environment.ExitCode = 1; }

static async Task PrintErrorAsync(HttpResponseMessage response)
{
    Console.WriteLine($"HTTP {(int)response.StatusCode} {response.StatusCode}");
    var body = await response.Content.ReadAsStringAsync();
    try
    {
        var error = System.Text.Json.JsonSerializer.Deserialize<ApiError>(body, new System.Text.Json.JsonSerializerOptions(System.Text.Json.JsonSerializerDefaults.Web));
        Console.WriteLine($"{error?.Code}: {error?.Message}");
    }
    catch (System.Text.Json.JsonException) { Console.WriteLine(string.IsNullOrWhiteSpace(body) ? "Phan hoi khong co body JSON." : body); }
}

record ProductDto(int Id, string Name, string Description, decimal Price);
record CreateProductRequest(string Name, string? Description, decimal Price);
record ApiError(string Code, string Message);
