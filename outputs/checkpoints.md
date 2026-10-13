# Nhật ký checkpoint — Lab 25 GPU FinOps

## CP1 — Đọc tài liệu và kiểm tra baseline

Đã đọc README.md, README_en.md, Guide.md, CODELAB.md, Rubric.md,
báo cáo mẫu và README của ba bonus. Phạm vi nộp bài: M1–M5,
hai extension có đo lường, report.md, savings.png, focus_export.csv,
và bài phân tích ngắn. Bonus Docker/local model không bắt buộc.

Môi trường đã cài sẵn trong `.venv`; dùng `.venv/bin/python`.
Baseline: verify.py **11/11**, pytest **15 passed**.
Kết quả gốc được lưu ở `outputs/baseline.json` để so sánh trước/sau.
Dữ liệu tổng hợp seed=25; giá minh họa snapshot tháng 6/2026.

Chọn extension 4 (ngân sách reasoning) và 5 (carbon-aware scheduling).
Các file kiểm tra bổ sung đặt ở `checks/`; giữ nguyên bộ `tests/` của lab.

Các checkpoint tiếp theo sẽ ghi nhận riêng code extension, cải thiện báo cáo,
và kiểm chứng bộ đầu ra cuối cùng. Mỗi checkpoint có một commit riêng.

## CP2 — Kiểm toán chi phí purchasing

Đã sửa reserved để tính đủ 24 giờ/ngày, kể cả giờ idle, phù hợp với
logic điểm hòa vốn của policy. Với job-infer-search 18 giờ/ngày,
chi phí reserved tăng $324/tháng so với mô hình gốc. Đây là điều chỉnh
kế toán, không phải extension tier-policy. `checks/check_purchasing.py`
kiểm tra trường hợp GPU giả lập có duty cycle 75%.
