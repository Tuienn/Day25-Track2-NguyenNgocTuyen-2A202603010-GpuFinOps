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

## CP3 — Extension 4: ngân sách reasoning

M2 phân rã savings cascade → cache → batch, tách request/cost/Wh theo
reasoning, và so sánh cap 10%, 5%, 0%. Dataset có 201/2400 request reasoning
(8,375%), 16,5% cost và 94,0% energy. Cap 10% chưa tác động; cap 5%
giảm 7.842,97 Wh/ngày theo hệ số mô phỏng 80×. Không bịa phụ phí USD:
cùng token, tier và discount thì cap này tiết kiệm $0 tiền token.
Đã kiểm tra cap hoạt động, biên 0, input sai, đối soát cohort và năng lượng.

## CP4 — Extension 5: carbon-aware scheduling

M6 so sánh năm vùng cho ba job training interruptible; có carbon trước/sau
theo từng job. Kịch bản chạy lặp 30 ngày dùng 4.092 kWh/tháng; di chuyển
us-east-1 → europe-north1 giảm 1.432.200 gCO2e (92,11%) và $122,76
tiền điện minh họa. Rẻ nhất và cân bằng theo score chuẩn hóa 50/50:
us-east-wa; sạch nhất: europe-north1. Đây không phải tiết kiệm thêm
trên hóa đơn thuê GPU. `checks/check_carbon.py` pass đối soát tổng.

## CP5 — Tích hợp báo cáo và bộ bài nộp

M5 sinh report chi tiết, writeup tiếng Việt, results.json và waterfall thật
có baseline/optimized cùng bốn lever. Sửa nhãn vùng sạch nhất (không gọi
là rẻ nhất), phân biệt query mẫu 800 token với năng lượng dataset.
Report ghi rõ snapshot giá, kịch bản 30 ngày, điều kiện right-size và
nguy cơ trùng cost buckets do thiếu mapping giữa các nguồn dữ liệu.
run_all chạy cả M6. Bộ tests gốc vẫn giữ nguyên.

## CP6 — Kiểm chứng cuối và sẵn sàng nộp

- `verify.py`: **11/11 checks passed** sau tích hợp.
- `python -m pytest -q`: **15 passed** sau tích hợp.
- `checks/check_reasoning.py`: pass (cap 10%, 5%, 0%, input sai, cohort accounting).
- `checks/check_carbon.py`: pass (5 vùng, totals và per-job reconciliation).
- `checks/check_purchasing.py`: pass (reserved trả đủ giờ cam kết).
- `checks/check_submission.py`: pass (report/JSON đối soát, 50-row FOCUS sample,
  PNG tồn tại, tái tạo report/writeup/JSON không thay đổi).
- `git diff --check`: pass; không sửa bất kỳ file nào trong `tests/`.
- Đã xem savings.png: baseline, bốn lever và optimized đọc được, nhãn không bị cắt.
- `missions/run_all.py` chạy thành công; stdout lưu trong `outputs/missions.log`.

Kết quả cuối: kịch bản tháng $27.133 → $14.950, savings $12.183 (44,9%).
Inference $6.488 → $1.126/1M-token (82,6%). Những con số tổng tháng là
planning scenario với giả định buckets độc lập, không phải savings thực tế đã đo.

Bài nộp: `outputs/report.md`, `outputs/savings.png`, `outputs/focus_export.csv`,
`outputs/writeup.md`. `baseline.json`, `results.json` và `missions.log`
là bằng chứng so sánh và tái tạo. Chưa push lên remote.

## CP7 — Dọn format Markdown sinh tự động

Rà soát diff phát hiện hard line breaks bằng trailing spaces trong report
của starter. Đổi sang đoạn riêng, sinh lại report/log và kiểm tra lại.
Đây chỉ là sửa format; số liệu và logic giữ nguyên.
