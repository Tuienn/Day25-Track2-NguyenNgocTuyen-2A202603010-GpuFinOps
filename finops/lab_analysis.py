"""Render measured lab findings; values always come from mission results."""
from __future__ import annotations


def analysis_sections(r1: dict, r2: dict, r3: dict, r4: dict, r6: dict, cap5: dict) -> str:
    lines = [
        "\n## Phạm vi và giả định",
        "",
        "Dữ liệu tổng hợp seed=25, giá snapshot tháng 6/2026; các con số không phải báo giá cloud hiện tại.",
        "M2 là 2.400 request của một ngày, nhân 30 để dự phóng tháng. M3/M6 lặp hours_per_day trong 30 ngày,",
        "không sử dụng cột days (số ngày chạy thực tế của job). Reserved tính đủ 24h/ngày và giả định có thể cam kết 3 năm.",
        "Tổng M5 là kịch bản lập kế hoạch của lab: cộng token billing với GPU rental, cùng savings từ telemetry.",
        "Các dataset không có mapping request → job → GPU. Nếu API billing và rental cùng phục vụ một workload,",
        "hoặc right-sizing/idle trùng với purchasing, phải đối soát để tránh đếm hai lần. Tổng savings chưa phải hóa đơn đã xác minh.",
        "Không chia chi phí training cho token inference. Chỉ M2 có mẫu số token phù hợp để báo $/1M-token.",
        "",
        "## Inference: baseline vs. optimized theo $/1M-token",
        "",
        f"Tổng token/ngày: **{r2['total_tokens']:,}**. Baseline **${r2['baseline_daily']:.2f}/ngày**, "
        f"optimized **${r2['optimized_daily']:.2f}/ngày**; đơn giá **${r2['baseline_per_m']:.3f} → "
        f"${r2['optimized_per_m']:.3f}/1M-token**, giảm **{r2['savings_pct']:.1f}%**.",
        "",
        "| Lever theo thứ tự áp dụng | Savings USD/ngày | Savings USD/30 ngày |",
        "|---|---:|---:|",
    ]
    for lever, amount in r2['lever_savings'].items():
        lines.append(f"| {lever} | {amount:.4f} | {amount*30:.2f} |")
    lines += [
        "",
        "Cascade đóng góp lớn nhất trong inference vì đa số traffic được route sang model nhỏ. Cache giảm phần input cache-hit,",
        "batch giảm cả bill của request đủ điều kiện. Đây là marginal savings theo thứ tự cascade → cache → batch;",
        "đổi thứ tự sẽ thay đổi đóng góp từng lever. Chênh lệch cents do tổng M5 làm tròn theo ngày/tháng.",
        "Batch phù hợp eval/offline; không áp dụng cho chat cần phản hồi tức thời. Routing phải kiểm tra chất lượng model nhỏ.",
        "",
        "## M1: GPU-Util lie và idle waste",
        "",
        "| GPU | GPU-Util % | MFU | MBU |",
        "|---|---:|---:|---:|",
    ]
    for gpu in r1['lies']:
        lines.append(f"| {gpu['gpu_id']} | {gpu['gpu_util_pct']} | {gpu['mfu']:.3f} | {gpu['mbu']:.3f} |")
    lines += [
        "",
        f"Idle waste **${r1['idle_waste_daily']:.2f}/ngày**, tức **${r1['idle_waste_daily']*30:.2f}/tháng**.",
        "GPU-Util đo thời gian GPU có kernel hoạt động, còn MFU đo FLOPs thực đạt/peak. GPU có thể bận do memory stall",
        "hoặc kernel overhead trong khi FLOPs thấp; telemetry này không xác định được nguyên nhân gốc rễ.",
        "MFU thấp không tự chứng minh có thể hạ GPU: cần profile, đủ VRAM, bandwidth và latency/throughput SLO.",
        "Right-size trong M5 vẫn là đề xuất tier-down minh họa của lab, chưa đo chất lượng dịch vụ sau chuyển.",
        "",
        "## M3: lựa chọn purchasing",
        "",
        f"On-demand **${r3['on_demand_monthly']:,}/tháng** → tối ưu **${r3['optimized_monthly']:,}/tháng**, "
        f"giảm **{r3['savings_pct']:.1f}%**. Đã sửa reserved để trả cả giờ idle; chi phí tăng $324/tháng so với code gốc.",
        "",
        "| Job | Tier | On-demand USD/tháng | Optimized USD/tháng |",
        "|---|---|---:|---:|",
    ]
    for job in r3['recommendations']:
        lines.append(f"| {job['job_id']} | {job['tier']} | {job['on_demand']:,} | {job['optimized']:,} |")
    lines += [
        "",
        "Spot phù hợp job interruptible có checkpoint. Effective hours gồm 3% checkpoint overhead và rework kỳ vọng",
        "với interruption rate 0,05/giờ, không phải benchmark thực tế. Reserved cần duty cycle đủ cao và dự báo nhu cầu dài hạn;",
        "ngưỡng 55% là policy gần đúng, giá catalog và thời hạn cam kết thực tế cần được đối chiếu trước mua.",
        "",
        "## M4: showback và chargeback",
        "",
        f"Tag coverage: **{r4['tag_coverage']:.1%}**; chargeback gate: **{r4['chargeback_ready']}** (ngưỡng 80%).",
        "",
        "| Team | Optimized USD/ngày |",
        "|---|---:|",
    ]
    for team, cost in sorted(r4['by_team'].items(), key=lambda kv: -kv[1]):
        lines.append(f"| {team} | {cost:.2f} |")
    lines += [
        "",
        "FOCUS export là sample 50 request với schema tối giản của lab, không phải toàn bộ bill và không chứng nhận FOCUS compliance.",
        "FOCUS-style schema giúp quy về cùng cột khi so sánh nhiều provider. Gate 80% chỉ là quy tắc lab;",
        "cần xử lý phần untagged và xác nhận owner trước chargeback thật.",
        "",
        "## Extension 4: ngân sách reasoning",
        "",
        f"Reasoning: **{r2['reasoning_requests']}/{r2['total_requests']} request ({r2['reasoning_traffic_share']:.1%})**, "
        f"**${r2['reasoning_cost']:.4f}/ngày ({r2['reasoning_cost_share']:.1%} chi phí)**, "
        f"**{r2['reasoning_wh']:.2f} Wh/ngày ({r2['reasoning_energy_share']:.1%} năng lượng)**.",
        f"Normal: **${r2['normal_cost']:.4f}/ngày**, **{r2['normal_wh']:.2f} Wh/ngày**.",
        f"Cùng token reasoning nhưng chạy normal chỉ dùng {r2['reasoning_normal_energy_wh']:.2f} Wh; "
        f"overhead là **{r2['reasoning_extra_wh']:.2f} Wh/ngày**.",
        "Hệ số 80× là giả định năng lượng trong sustainability.py, không phải số đo GPU; nó đại diện compute bổ sung",
        "của reasoning, dù dataset chưa mô hình hóa hidden reasoning tokens. Chi phí reasoning cohort không phải phụ phí do bật reasoning.",
        "",
        f"Cap 10%: dataset đã dưới ngưỡng nên savings **${r2['reasoning_cap_saved_usd']:.2f}, "
        f"{r2['reasoning_cap_saved_wh']:.2f} Wh/ngày**. Sensitivity cap 5% giữ {cap5['reasoning_cap_requests']} request: "
        f"năng lượng **{cap5['reasoning_cap_total_wh_before']:.2f} → {cap5['reasoning_cap_total_wh_after']:.2f} Wh/ngày**, "
        f"giảm **{cap5['reasoning_cap_saved_wh']:.2f} Wh/ngày**, tiết kiệm token billing **$0**.",
        "Giữ nguyên token/tier/cache/batch nên không có USD premium để cắt. Scenario offline chọn output dài nhất làm proxy;",
        "không thể biết output length trước routing. Khi triển khai, chỉ bật reasoning cho task phức tạp hoặc confidence thấp",
        "dựa trên input classifier, giới hạn budget/ngày, và kiểm tra chất lượng trước thử cap 5%. Không cộng scenario cap vào M5.",
        "",
        "## Extension 5: carbon-aware scheduling",
        "",
        f"Ba job training interruptible dùng **{r6['monthly_energy_kwh']:,.0f} kWh/30 ngày** ở catalog watts cố định, không gồm PUE.",
        "",
        "| Vùng | USD/kWh | gCO2e/kWh | Điện USD/30 ngày | Carbon kgCO2e/30 ngày |",
        "|---|---:|---:|---:|---:|",
    ]
    for region, v in r6['regions'].items():
        lines.append(f"| {region} | {v['usd_per_kwh']:.3f} | {v['gco2e_per_kwh']} | {v['electricity_usd']:.2f} | {v['carbon_gco2e']/1000:.2f} |")
    lines += ["", "| Training job | Carbon us-east-1 (kg) | Carbon cleanest (kg) | Savings (kg) |",
              "|---|---:|---:|---:|"]
    for job in r6['jobs']:
        lines.append(f"| {job['job_id']} | {job['baseline_carbon_gco2e']/1000:.2f} | {job['cleanest_carbon_gco2e']/1000:.2f} | {job['carbon_gco2e_saved']/1000:.2f} |")
    comparison = r6['comparison']
    lines += [
        "",
        f"us-east-1 → europe-north1 giảm **{comparison['carbon_gco2e_saved']/1000:,.2f} kgCO2e "
        f"({comparison['carbon_savings_pct']:.2f}%)**, tiền điện giảm **${-comparison['electricity_usd_change']:.2f}/tháng**.",
        "Sạch nhất: europe-north1; rẻ nhất: us-east-wa. Policy cân bằng dùng trung bình hai score min-max USD và carbon,",
        f"trọng số 50/50, chọn **{r6['optimal_regions']['balanced']}**. Trọng số là quyết định kinh doanh.",
        "Không có dữ liệu carbon theo giờ nên extension chỉ tối ưu vùng. Kiểm tra latency, data residency, egress,",
        "GPU availability và chi phí migration trước chuyển vùng. Điện minh họa không cộng vào savings rental.",
        "",
        "## Ba hành động ưu tiên cho NimbusAI",
        "",
        "1. Dự báo nhu cầu dài hạn rồi chuyển job checkpointable sang spot; kiểm tra cam kết reserved. Đây là lever USD lớn nhất.",
        "2. Áp cascade có quality gate, cache input lặp và batch tác vụ offline; theo dõi $/1M-token và latency cùng nhau.",
        "3. Tắt GPU idle theo owner/tag, profile GPU-Util lie trước right-size; thêm reasoning budget và chạy training ở vùng phù hợp carbon/residency.",
        "",
        "## Tái tạo và kiểm chứng",
        "",
        "Chạy `.venv/bin/python missions/run_all.py`, `.venv/bin/python verify.py`, `.venv/bin/python -m pytest -q`,",
        "và `.venv/bin/python checks/check_reasoning.py`, `.venv/bin/python checks/check_carbon.py`,",
        "`.venv/bin/python checks/check_purchasing.py`, `.venv/bin/python checks/check_submission.py`.",
        "Dùng `MPLCONFIGDIR=/tmp/gpufinops-mpl` nếu sandbox không ghi được matplotlib cache mặc định.",
    ]
    return '\n'.join(lines)


def short_writeup(r1: dict, r2: dict, r3: dict, r5: dict, r6: dict, cap5: dict) -> str:
    return f"""# Bài phân tích ngắn — Lab 25 GPU FinOps

## Kết quả baseline và optimized

Kịch bản tháng của NimbusAI: **${r5['baseline_monthly']:,} → ${r5['optimized_monthly']:,}**,
giảm **{r5['total_savings_pct']:.1f}%**. Riêng inference dùng cùng {r2['total_tokens']:,} token/ngày:
**${r2['baseline_per_m']:.3f} → ${r2['optimized_per_m']:.3f}/1M-token**, giảm {r2['savings_pct']:.1f}%.
Không dùng token inference để chuẩn hóa phần training. Tổng tháng là planning scenario của lab,
chưa có mapping GPU/job/request để chứng minh các buckets độc lập hay tránh trùng API billing/rental.

## Đòn bẩy và GPU-Util lie

Purchasing đóng góp lớn nhất: **${r5['levers']['Purchasing (spot/reserved)']:,}/tháng**;
interruptible jobs dùng spot với checkpoint, steady inference dùng reserved. Reserved trả cả giờ idle,
nên đã điều chỉnh bill +$324/tháng so với starter. Kịch bản lặp 30 ngày không phản ánh cột days của job.
Trong inference, cascade tiết kiệm **${r2['lever_savings']['cascade']*30:.2f}/tháng**, lớn hơn cache
và batch do traffic model nhỏ có giá thấp. Số đo marginal phụ thuộc thứ tự cascade → cache → batch;
không hy sinh chất lượng hoặc batch chat realtime để đạt con số savings.

GPU-Util lie gồm {', '.join(g['gpu_id'] for g in r1['lies'])}. GPU-Util chỉ phản ánh thời gian kernel
hoạt động; MFU phản ánh FLOPs thực nhận/peak. Memory stall hoặc kernel overhead có thể giải thích
MFU thấp, nhưng telemetry không đủ kết luận nguyên nhân. Idle waste **${r1['idle_waste_daily']*30:.2f}/tháng**;
right-sizing chỉ là ước tính cần kiểm tra VRAM, bandwidth và SLO trước thực hiện.

## Hai extension đã thực hiện

**Reasoning budget:** {r2['reasoning_traffic_share']:.1%} traffic nhưng {r2['reasoning_cost_share']:.1%} cost
và {r2['reasoning_energy_share']:.1%} energy mô phỏng. Extra energy so cùng token normal là
**{r2['reasoning_extra_wh']:.2f} Wh/ngày**. Cap 10% chưa tác động vì traffic hiện tại dưới ngưỡng.
Cap 5% giảm **{cap5['reasoning_cap_saved_wh']:.2f} Wh/ngày**; USD savings bằng 0 vì giữ nguyên
token, model tier và discounts, không có reasoning premium trong tariff. Hệ số 80× là giả định,
không phải số đo phần cứng. Chọn output dài là proxy offline; production cần input classifier,
confidence gate, quality eval và budget theo ngày. Không cộng cap vào tổng savings M5.

**Carbon scheduling:** ba job training interruptible dùng {r6['monthly_energy_kwh']:,.0f} kWh/30 ngày.
Chuyển us-east-1 → europe-north1 giảm **{r6['comparison']['carbon_gco2e_saved']/1000:,.2f} kgCO2e
({r6['comparison']['carbon_savings_pct']:.2f}%)**, tiền điện minh họa giảm
**${-r6['comparison']['electricity_usd_change']:.2f}/tháng**. Vùng sạch nhất là europe-north1;
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
"""
