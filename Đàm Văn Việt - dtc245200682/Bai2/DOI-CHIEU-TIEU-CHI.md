# Đối chiếu tiêu chí chấm Bài 2 – dtc245200682

Đàm Văn Việt · cập nhật 18/11/2026. Đây là bảng đối chiếu minh chứng, không tự thay thế điểm giảng viên.

## Căn cứ và điểm hiện có

- [Đề PDF của lớp](https://github.com/PTUDPTK23/CNTTK23E/blob/main/L%C3%BD%20A%20Vinh%20-%20dtc245200194/Bai2/Bai2_RESTful-API_Send.pdf), đặc biệt trang 63 và 90; bản đã đọc ở workspace là `bai2/Bai2_RESTful-API_Send.pdf`.
- [Thông báo sửa Bài 1, Bài 2 ngày 17/11](https://github.com/PTUDPTK23/CNTTK23E#readme): push trước 17h00 ngày 18/11, giữ nhánh/PR cũ, README có lệnh chạy, ảnh/kết quả, bảng phá thử, ba câu hỏi.
- [Bảng điểm giảng viên](https://github.com/PTUDPTK23/CNTTK23E/blob/main/_BangTheoDoi/DiemGV_Bai2.csv): dòng dtc245200682 đang là API 3, client 1, HTTP 1.5, README 0, Git/PR 1, trừ quá hạn 0, tổng **6.5**. Ghi chú: `Bai da merge truoc do, cham tinh tu main; chua chay dotnet`.
- [Conversation PR #4](https://github.com/PTUDPTK23/CNTTK23E/pull/4): review APPROVED và merged ngày 12/11. Không có yêu cầu sửa riêng trong nhận xét này.

## Đối chiếu từng hạng mục

| Tiêu chí | Tối đa | Điểm đang ghi | Phần đã làm và kiểm chứng trong bản bổ sung | Bằng chứng |
|---|---:|---:|---|---|
| Máy chủ API | 3 | 3 | Đủ 4 endpoint nghiệp vụ EduSubmit; DTO vào/ra riêng; POST kiểm tra tồn tại → còn mở → đủ dữ liệu; 201 + Location; GET lại đúng tài nguyên; 400/404 ApiError. Catalog cũng đã build và chạy. | [Mã API](RestfulClientServer/src/Submission.Api/Program.cs), [59 phản hồi gốc](evidence/http-responses.json) |
| Máy khách | 2 | 1 | Hai console client ở tiến trình riêng; in HTTP 200/201/200/400; đọc theo Location và so sánh DTO; xử lý lỗi nghiệp vụ, HTTP rỗng/500, mất kết nối, sai cổng, URL sai, JSON hỏng/null. Mỗi client chạy hai lần đều đủ bốn bước. | [Client EduSubmit](RestfulClientServer/src/Submission.Client/Program.cs), [ảnh client](evidence/clients.png), [log đầy đủ](verification-results.txt) |
| requests.http | 1.5 | 1.5 | Gốc bài đủ 7 ca có 200/201/400/404; EduSubmit chi tiết 14 ca; Catalog 8 ca. Đã đọc và gửi cả 29 request từ chính các tệp, có named response và JSON file. | [7 ca](requests.http), [14 ca](RestfulClientServer/requests.http), [8 ca](CatalogApi/requests.http), [ảnh HTTP](evidence/http.png) |
| README | 2.5 | 0 | Đủ họ tên/MSSV, điều kiện chạy, cấu trúc, lệnh build/chạy cả API và client từ repo vừa clone, luồng/giao thức, hợp đồng, bảng dự đoán/thực tế/giải thích, bốn thí nghiệm phân tán, ba câu hỏi trang 90, nhật ký, ảnh và log tái kiểm chứng. | [README](README.md), [build](evidence/build.png), [lỗi](evidence/errors.png), [log build](evidence/build-edusubmit.txt) |
| Git/PR | 1 | 1 | Đúng tài khoản Viet0810, email dtc245200682@ictu.edu.vn, nhánh bài cũ. Chỉ bổ sung dưới thư mục cá nhân/Bai2; có .gitignore; không theo dõi bin/obj. Commit mới ghi nhận đúng việc bổ sung thực tế. | [PR cũ #4](https://github.com/PTUDPTK23/CNTTK23E/pull/4), lịch sử nhánh và ghi chú bên dưới |
| Quá hạn | Theo thông báo | 0 | Hạn sửa được thông báo là 17h00 18/11/2026. Thời điểm kiểm chứng 11:12:54 UTC+7; thời điểm push cần đối chiếu lịch sử GitHub. | Thông báo lớp và metadata commit trên nhánh |

Điểm ghi ở bảng là **trước khi giảng viên xem bản bổ sung**, không suy ra chắc chắn được tăng lên 10/10.

## Phiếu kiểm tra Catalog trang 63

| # | Yêu cầu | Kết quả thực tế |
|---|---|---|
| 1 | GET / | 200 |
| 2 | GET /api/products khi mới mở API | 200, đúng 3 sản phẩm |
| 3 | GET /api/products/1 | 200 |
| 4 | GET /api/products/999 | 404 PRODUCT_NOT_FOUND |
| 5 | GET /api/products/abc | 404 body rỗng |
| 6 | POST hợp lệ | 201 + Location; GET Location bằng DTO vừa tạo |
| 7 | POST giá âm/tên rỗng | 400 INVALID_PRODUCT |
| 8 | POST không có Content-Type JSON (curl -d dùng form) | 415 |
| 9 | Client đủ bốn bước | Đạt ở hai lần chạy |
| 10 | Tắt API rồi chạy client | Lỗi kết nối, exit 1 |

## Phạm vi và phần còn phụ thuộc giảng viên

- PR #4 **đã merge**. Push thêm lên nhánh `bai2-dtc245200682` không cập nhật main repo lớp hay diff của PR đã merge. Giữ PR cũ theo thông báo; dẫn bản bổ sung trong Conversation để cô xem. Không mở PR thay thế.
- Lịch sử ban đầu chỉ có commit nộp toàn bài `a97e847`; gợi ý commit theo từng bước ở trang 63 không thể bổ sung ngược thời gian. Các commit sửa hiện tại là công việc thực tế, không dựng lại lịch sử cũ.
- Timeout 10 giây có xử lý trong client nhưng chưa được mô phỏng riêng. Các ca HTTP/JSON lỗi dùng server kiểm thử cục bộ; các mã nghiệp vụ lấy từ API thật.
- 409/204 và đổi miền ở phụ lục là phần mở rộng; không nằm trong bốn endpoint cơ bản trang 90. Bản hiện tại cho phép nộp lại.
- Việc xem lại bản bổ sung, gộp vào repo lớp và cập nhật điểm phải do giảng viên thực hiện.
