# Bài phân tích ngắn — Lab 25 GPU FinOps

## Kết quả baseline và optimized

Kịch bản tháng của NimbusAI: **$27,133 → $14,950**,
giảm **44.9%**. Riêng inference dùng cùng 7,533,027 token/ngày:
**$6.488 → $1.126/1M-token**, giảm 82.6%.
Không dùng token inference để chuẩn hóa phần training. Tổng tháng là planning scenario của lab,
chưa có mapping GPU/job/request để chứng minh các buckets độc lập hay tránh trùng API billing/rental.

## Đòn bẩy và GPU-Util lie

Purchasing đóng góp lớn nhất: **$9,716/tháng**;
interruptible jobs dùng spot với checkpoint, steady inference dùng reserved. Reserved trả cả giờ idle,
nên đã điều chỉnh bill +$324/tháng so với starter. Kịch bản lặp 30 ngày không phản ánh cột days của job.
Trong inference, cascade tiết kiệm **$1121.96/tháng**, lớn hơn cache
và batch do traffic model nhỏ có giá thấp. Số đo marginal phụ thuộc thứ tự cascade → cache → batch;
không hy sinh chất lượng hoặc batch chat realtime để đạt con số savings.

GPU-Util lie gồm gpu-h100-4, gpu-a10g-1. GPU-Util chỉ phản ánh thời gian kernel
hoạt động; MFU phản ánh FLOPs thực nhận/peak. Memory stall hoặc kernel overhead có thể giải thích
MFU thấp, nhưng telemetry không đủ kết luận nguyên nhân. Idle waste **$600.00/tháng**;
right-sizing chỉ là ước tính cần kiểm tra VRAM, bandwidth và SLO trước thực hiện.

## Hai extension đã thực hiện

**Reasoning budget:** 8.4% traffic nhưng 16.5% cost
và 94.0% energy mô phỏng. Extra energy so cùng token normal là
**29415.40 Wh/ngày**. Cap 10% chưa tác động vì traffic hiện tại dưới ngưỡng.
Cap 5% giảm **7842.97 Wh/ngày**; USD savings bằng 0 vì giữ nguyên
token, model tier và discounts, không có reasoning premium trong tariff. Hệ số 80× là giả định,
không phải số đo phần cứng. Chọn output dài là proxy offline; production cần input classifier,
confidence gate, quality eval và budget theo ngày. Không cộng cap vào tổng savings M5.

**Carbon scheduling:** ba job training interruptible dùng 4,092 kWh/30 ngày.
Chuyển us-east-1 → europe-north1 giảm **1,432.20 kgCO2e
(92.11%)**, tiền điện minh họa giảm
**$122.76/tháng**. Vùng sạch nhất là europe-north1;
rẻ nhất và cân bằng score chuẩn hóa 50/50 là us-east-wa. Công suất catalog cố định, bỏ PUE;
chưa có time-of-day data. Cần xét latency/residency/egress trước chuyển vùng.
Tiền điện của provider không cộng thêm vào tiết kiệm rental của khách hàng.

## Ba hành động đầu tiên

1. Đối soát buckets hóa đơn, owner/tag và thời hạn nhu cầu; chọn spot cho job có checkpoint,
   reserved khi dự báo dài hạn bảo đảm đủ utilization. Đặt mục tiêu purchasing trước vì ROI lớn nhất.
2. Triển khai cascade có quality gate, cache input lặp, batch offline; giám sát $/1M-token cùng SLO.
3. Tắt GPU idle, profile trước right-size, thêm budget reasoning và policy vùng chạy training theo carbon.

Giá/dữ liệu là snapshot minh họa tháng 6/2026, seed=25. Mã extension và kiểm tra bổ sung ở
`missions/m2_inference_levers.py`, `missions/m6_carbon_scheduling.py`, `checks/`.
Các số liệu chi tiết và cách tái tạo nằm trong `outputs/report.md` và `outputs/results.json`.
