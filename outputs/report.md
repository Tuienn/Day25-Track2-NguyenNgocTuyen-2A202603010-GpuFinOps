# NimbusAI — GPU Cost Optimization Report

**Period:** monthly

**Baseline spend:** $27,133

**Optimized spend:** $14,950

**Projected savings:** $12,183  (**45%**)

## Savings by lever

| Lever | Savings (USD) |
|---|---|
| Inference (cascade/cache/batch) | $1,212 |
| Purchasing (spot/reserved) | $9,716 |
| Right-size util-lies | $655 |
| Kill idle GPUs | $600 |

## Sustainability

Illustrative normal query: 800 tokens; energy and carbon are model estimates, not hardware measurements.

- Energy per query: 0.24 Wh
- Carbon per query: 0.091 gCO2e
- Cleanest region: europe-north1

_Figures are June-2026 as-of snapshots; re-baseline before acting._
## Phạm vi và giả định

Dữ liệu tổng hợp seed=25, giá snapshot tháng 6/2026; các con số không phải báo giá cloud hiện tại.
M2 là 2.400 request của một ngày, nhân 30 để dự phóng tháng. M3/M6 lặp hours_per_day trong 30 ngày,
không sử dụng cột days (số ngày chạy thực tế của job). Reserved tính đủ 24h/ngày và giả định có thể cam kết 3 năm.
Tổng M5 là kịch bản lập kế hoạch của lab: cộng token billing với GPU rental, cùng savings từ telemetry.
Các dataset không có mapping request → job → GPU. Nếu API billing và rental cùng phục vụ một workload,
hoặc right-sizing/idle trùng với purchasing, phải đối soát để tránh đếm hai lần. Tổng savings chưa phải hóa đơn đã xác minh.
Không chia chi phí training cho token inference. Chỉ M2 có mẫu số token phù hợp để báo $/1M-token.

## Inference: baseline vs. optimized theo $/1M-token

Tổng token/ngày: **7,533,027**. Baseline **$48.87/ngày**, optimized **$8.48/ngày**; đơn giá **$6.488 → $1.126/1M-token**, giảm **82.6%**.

| Lever theo thứ tự áp dụng | Savings USD/ngày | Savings USD/30 ngày |
|---|---:|---:|
| cascade | 37.3985 | 1121.96 |
| cache | 1.1965 | 35.89 |
| batch | 1.7946 | 53.84 |

Cascade đóng góp lớn nhất trong inference vì đa số traffic được route sang model nhỏ. Cache giảm phần input cache-hit,
batch giảm cả bill của request đủ điều kiện. Đây là marginal savings theo thứ tự cascade → cache → batch;
đổi thứ tự sẽ thay đổi đóng góp từng lever. Chênh lệch cents do tổng M5 làm tròn theo ngày/tháng.
Batch phù hợp eval/offline; không áp dụng cho chat cần phản hồi tức thời. Routing phải kiểm tra chất lượng model nhỏ.

## M1: GPU-Util lie và idle waste

| GPU | GPU-Util % | MFU | MBU |
|---|---:|---:|---:|
| gpu-h100-4 | 98.2 | 0.194 | 0.207 |
| gpu-a10g-1 | 96.9 | 0.268 | 0.302 |

Idle waste **$20.00/ngày**, tức **$600.00/tháng**.
GPU-Util đo thời gian GPU có kernel hoạt động, còn MFU đo FLOPs thực đạt/peak. GPU có thể bận do memory stall
hoặc kernel overhead trong khi FLOPs thấp; telemetry này không xác định được nguyên nhân gốc rễ.
MFU thấp không tự chứng minh có thể hạ GPU: cần profile, đủ VRAM, bandwidth và latency/throughput SLO.
Right-size trong M5 vẫn là đề xuất tier-down minh họa của lab, chưa đo chất lượng dịch vụ sau chuyển.

## M3: lựa chọn purchasing

On-demand **$25,667/tháng** → tối ưu **$15,951/tháng**, giảm **37.9%**. Đã sửa reserved để trả cả giờ idle; chi phí tăng $324/tháng so với code gốc.

| Job | Tier | On-demand USD/tháng | Optimized USD/tháng |
|---|---|---:|---:|
| job-train-llm | spot | 12,000 | 7,596 |
| job-train-embed | spot | 2,148 | 1,393 |
| job-finetune | spot | 900 | 570 |
| job-infer-chat | reserved | 4,320 | 2,592 |
| job-infer-rag | reserved | 3,866 | 2,160 |
| job-infer-search | reserved | 1,728 | 1,296 |
| job-dev-sandbox | spot | 480 | 203 |
| job-batch-eval | spot | 225 | 142 |

Spot phù hợp job interruptible có checkpoint. Effective hours gồm 3% checkpoint overhead và rework kỳ vọng
với interruption rate 0,05/giờ, không phải benchmark thực tế. Reserved cần duty cycle đủ cao và dự báo nhu cầu dài hạn;
ngưỡng 55% là policy gần đúng, giá catalog và thời hạn cam kết thực tế cần được đối chiếu trước mua.

## M4: showback và chargeback

Tag coverage: **91.8%**; chargeback gate: **True** (ngưỡng 80%).

| Team | Optimized USD/ngày |
|---|---:|
| assistant | 2.59 |
| search | 2.49 |
| eval | 1.79 |
| rag | 1.60 |

FOCUS export là sample 50 request với schema tối giản của lab, không phải toàn bộ bill và không chứng nhận FOCUS compliance.
FOCUS-style schema giúp quy về cùng cột khi so sánh nhiều provider. Gate 80% chỉ là quy tắc lab;
cần xử lý phần untagged và xác nhận owner trước chargeback thật.

## Extension 4: ngân sách reasoning

Reasoning: **201/2400 request (8.4%)**, **$1.3965/ngày (16.5% chi phí)**, **29787.74 Wh/ngày (94.0% năng lượng)**.
Normal: **$7.0882/ngày**, **1887.56 Wh/ngày**.
Cùng token reasoning nhưng chạy normal chỉ dùng 372.35 Wh; overhead là **29415.40 Wh/ngày**.
Hệ số 80× là giả định năng lượng trong sustainability.py, không phải số đo GPU; nó đại diện compute bổ sung
của reasoning, dù dataset chưa mô hình hóa hidden reasoning tokens. Chi phí reasoning cohort không phải phụ phí do bật reasoning.

Cap 10%: dataset đã dưới ngưỡng nên savings **$0.00, 0.00 Wh/ngày**. Sensitivity cap 5% giữ 120 request: năng lượng **31675.31 → 23832.34 Wh/ngày**, giảm **7842.97 Wh/ngày**, tiết kiệm token billing **$0**.
Giữ nguyên token/tier/cache/batch nên không có USD premium để cắt. Scenario offline chọn output dài nhất làm proxy;
không thể biết output length trước routing. Khi triển khai, chỉ bật reasoning cho task phức tạp hoặc confidence thấp
dựa trên input classifier, giới hạn budget/ngày, và kiểm tra chất lượng trước thử cap 5%. Không cộng scenario cap vào M5.

## Extension 5: carbon-aware scheduling

Ba job training interruptible dùng **4,092 kWh/30 ngày** ở catalog watts cố định, không gồm PUE.

| Vùng | USD/kWh | gCO2e/kWh | Điện USD/30 ngày | Carbon kgCO2e/30 ngày |
|---|---:|---:|---:|---:|
| us-east-1 | 0.120 | 380 | 491.04 | 1554.96 |
| us-west-2 | 0.070 | 120 | 286.44 | 491.04 |
| europe-north1 | 0.090 | 30 | 368.28 | 122.76 |
| europe-central2 | 0.180 | 660 | 736.56 | 2700.72 |
| us-east-wa | 0.055 | 90 | 225.06 | 368.28 |

| Training job | Carbon us-east-1 (kg) | Carbon cleanest (kg) | Savings (kg) |
|---|---:|---:|---:|
| job-train-llm | 1276.80 | 100.80 | 1176.00 |
| job-train-embed | 182.40 | 14.40 | 168.00 |
| job-finetune | 95.76 | 7.56 | 88.20 |

us-east-1 → europe-north1 giảm **1,432.20 kgCO2e (92.11%)**, tiền điện giảm **$122.76/tháng**.
Sạch nhất: europe-north1; rẻ nhất: us-east-wa. Policy cân bằng dùng trung bình hai score min-max USD và carbon,
trọng số 50/50, chọn **us-east-wa**. Trọng số là quyết định kinh doanh.
Không có dữ liệu carbon theo giờ nên extension chỉ tối ưu vùng. Kiểm tra latency, data residency, egress,
GPU availability và chi phí migration trước chuyển vùng. Điện minh họa không cộng vào savings rental.

## Ba hành động ưu tiên cho NimbusAI

1. Dự báo nhu cầu dài hạn rồi chuyển job checkpointable sang spot; kiểm tra cam kết reserved. Đây là lever USD lớn nhất.
2. Áp cascade có quality gate, cache input lặp và batch tác vụ offline; theo dõi $/1M-token và latency cùng nhau.
3. Tắt GPU idle theo owner/tag, profile GPU-Util lie trước right-size; thêm reasoning budget và chạy training ở vùng phù hợp carbon/residency.

## Tái tạo và kiểm chứng

Chạy `.venv/bin/python missions/run_all.py`, `.venv/bin/python verify.py`, `.venv/bin/python -m pytest -q`,
và `.venv/bin/python checks/check_reasoning.py`, `.venv/bin/python checks/check_carbon.py`,
`.venv/bin/python checks/check_purchasing.py`, `.venv/bin/python checks/check_submission.py`.
Dùng `MPLCONFIGDIR=/tmp/gpufinops-mpl` nếu sandbox không ghi được matplotlib cache mặc định.