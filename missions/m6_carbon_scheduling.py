"""M6 — Carbon-aware scheduling for interruptible training jobs.

Run: python missions/m6_carbon_scheduling.py

Monthly energy assumes each qualifying job runs its configured hours_per_day
every day of a 30-day month. The workload CSV's ``days`` column describes a
shorter job horizon and is intentionally not used for this monthly scenario.
GPU catalog watts are treated as constant draw; facility overhead is excluded.
Electricity cost is illustrative facility cost, separate from GPU rental cost.
"""
from __future__ import annotations

import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

from missions._common import catalog_by_type, load_csv, num
from finops import sustainability

DAYS_PER_MONTH = 30


def _score_regions(region_totals: dict) -> tuple[str, dict]:
    """Return equal-weight, min-max normalized electricity/carbon winner."""
    costs = [v["electricity_usd"] for v in region_totals.values()]
    carbons = [v["carbon_gco2e"] for v in region_totals.values()]
    cmin, cmax = min(costs), max(costs)
    gmin, gmax = min(carbons), max(carbons)
    scores = {}
    for region, values in region_totals.items():
        cost_score = (values["electricity_usd"] - cmin) / (cmax - cmin) if cmax > cmin else 0.0
        carbon_score = (values["carbon_gco2e"] - gmin) / (gmax - gmin) if gmax > gmin else 0.0
        scores[region] = round((cost_score + carbon_score) / 2, 6)
    return min(scores, key=lambda r: (scores[r], r)), scores


def run(verbose: bool = True) -> dict:
    catalog = catalog_by_type()
    jobs = []
    total_kwh = 0.0
    cleanest = min(sustainability.REGION_CARBON,
                   key=lambda region: (sustainability.REGION_CARBON[region], region))
    baseline_region = "us-east-1"
    for row in load_csv("workloads.csv"):
        if int(num(row.get("interruptible"))) != 1 or row.get("kind") != "train":
            continue
        gpu = row["gpu_type"]
        watts = num(catalog[gpu]["watts"])
        hours = num(row["hours_per_day"]) * DAYS_PER_MONTH
        kwh = watts * int(num(row["num_gpus"])) * hours / 1000.0
        baseline_carbon = kwh * sustainability.REGION_CARBON[baseline_region]
        clean_carbon = kwh * sustainability.REGION_CARBON[cleanest]
        jobs.append({"job_id": row["job_id"], "gpu_type": gpu,
                     "num_gpus": int(num(row["num_gpus"])),
                     "hours_per_day": num(row["hours_per_day"]),
                     "monthly_kwh": round(kwh, 3),
                     "baseline_region": baseline_region,
                     "baseline_electricity_usd": round(kwh * sustainability.REGION_PRICE_KWH[baseline_region], 2),
                     "baseline_carbon_gco2e": round(baseline_carbon, 2),
                     "cleanest_region": cleanest,
                     "cleanest_electricity_usd": round(kwh * sustainability.REGION_PRICE_KWH[cleanest], 2),
                     "cleanest_carbon_gco2e": round(clean_carbon, 2),
                     "carbon_gco2e_saved": round(baseline_carbon - clean_carbon, 2)})
        total_kwh += kwh

    region_totals = {}
    for region in sustainability.REGION_CARBON:
        price = sustainability.REGION_PRICE_KWH[region]
        intensity = sustainability.REGION_CARBON[region]
        region_totals[region] = {
            "usd_per_kwh": price,
            "gco2e_per_kwh": intensity,
            "electricity_usd": round(total_kwh * price, 2),
            "carbon_gco2e": round(total_kwh * intensity, 2),
        }

    baseline = region_totals["us-east-1"]
    cheapest = min(sustainability.REGION_PRICE_KWH,
                   key=lambda region: (sustainability.REGION_PRICE_KWH[region], region))
    balanced, scores = _score_regions(region_totals)
    after = region_totals[cleanest]
    result = {
        "assumptions": {
            "month_days": DAYS_PER_MONTH,
            "basis": "hours_per_day * 30 days; workload days column is a shorter horizon and is not applied",
            "power_model": "catalog GPU watts * GPU count; constant draw, facility overhead excluded",
            "electricity_cost_note": "illustrative facility electricity cost; separate from rental cost and not counted as rental savings",
        },
        "jobs": jobs,
        "monthly_energy_kwh": round(total_kwh, 3),
        "regions": region_totals,
        "comparison": {
            "baseline_region": "us-east-1",
            "cleanest_region": cleanest,
            "before": baseline,
            "after": after,
            "electricity_usd_change": round(after["electricity_usd"] - baseline["electricity_usd"], 2),
            "carbon_gco2e_saved": round(baseline["carbon_gco2e"] - after["carbon_gco2e"], 2),
            "carbon_savings_pct": round(
                (baseline["carbon_gco2e"] - after["carbon_gco2e"]) / baseline["carbon_gco2e"] * 100,
                2,
            ) if baseline["carbon_gco2e"] else 0.0,
        },
        "optimal_regions": {"cheapest": cheapest, "cleanest": cleanest, "balanced": balanced},
        "balanced_scores": scores,
        "balanced_policy": "minimize the mean of min-max normalized monthly electricity USD and carbon gCO2e; equal weights, lower is better",
        "caveat": "Carbon-optimal placement may increase user latency or conflict with data residency; validate both before scheduling across regions. No external APIs are used.",
    }

    if verbose:
        print("== M6 Carbon-aware Scheduling ==")
        print("Interruptible training jobs; 30-day monthly estimate (see assumptions).")
        print("job                     GPUs  kWh/month  baseline gCO2e  cleanest gCO2e  saved gCO2e")
        for job in jobs:
            print(f"{job['job_id']:23} {job['num_gpus']:>4}  {job['monthly_kwh']:>10.3f}"
                  f" {job['baseline_carbon_gco2e']:>14.2f} {job['cleanest_carbon_gco2e']:>15.2f}"
                  f" {job['carbon_gco2e_saved']:>12.2f}")
        print(f"Total energy: {total_kwh:.3f} kWh/month")
        print("region             $/kWh  gCO2e/kWh  electricity $  carbon gCO2e")
        for region, values in region_totals.items():
            print(f"{region:18} {values['usd_per_kwh']:>6.3f} {values['gco2e_per_kwh']:>11} {values['electricity_usd']:>14.2f} {values['carbon_gco2e']:>14.2f}")
        print(f"Baseline us-east-1 -> cleanest {cleanest}: save {result['comparison']['carbon_gco2e_saved']:.2f} gCO2e/month ({result['comparison']['carbon_savings_pct']:.2f}%); electricity change ${result['comparison']['electricity_usd_change']:.2f}/month.")
        print(f"Cheapest: {cheapest}; cleanest: {cleanest}; balanced: {balanced} (equal-weight normalized score).")
        print(result["caveat"])
    return result


if __name__ == "__main__":
    run()
