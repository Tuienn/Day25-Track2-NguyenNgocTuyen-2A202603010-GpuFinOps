"""Standalone checks for M6. Run: python checks/check_carbon.py"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from missions import m6_carbon_scheduling


def main() -> None:
    result = m6_carbon_scheduling.run(verbose=False)
    assert {job["job_id"] for job in result["jobs"]} == {
        "job-train-llm", "job-train-embed", "job-finetune"
    }, "only interruptible training jobs should be included"
    assert result["monthly_energy_kwh"] == 4092.0
    assert len(result["regions"]) == 5
    assert result["optimal_regions"] == {
        "cheapest": "us-east-wa",
        "cleanest": "europe-north1",
        "balanced": "us-east-wa",
    }
    assert result["comparison"]["carbon_gco2e_saved"] == 1432200.0
    assert result["comparison"]["before"]["carbon_gco2e"] == 1554960.0
    assert result["comparison"]["after"]["carbon_gco2e"] == 122760.0
    assert result["comparison"]["carbon_savings_pct"] == 92.11
    jobs = result["jobs"]
    assert all(job["baseline_region"] == "us-east-1" for job in jobs)
    assert all(job["cleanest_region"] == "europe-north1" for job in jobs)
    assert round(sum(job["baseline_carbon_gco2e"] for job in jobs), 2) == result["comparison"]["before"]["carbon_gco2e"]
    assert round(sum(job["cleanest_carbon_gco2e"] for job in jobs), 2) == result["comparison"]["after"]["carbon_gco2e"]
    assert round(sum(job["carbon_gco2e_saved"] for job in jobs), 2) == result["comparison"]["carbon_gco2e_saved"]
    assert round(sum(job["baseline_electricity_usd"] for job in jobs), 2) == result["comparison"]["before"]["electricity_usd"]
    assert round(sum(job["cleanest_electricity_usd"] for job in jobs), 2) == result["comparison"]["after"]["electricity_usd"]
    assert result["assumptions"]["month_days"] == 30
    assert "days column" in result["assumptions"]["basis"]
    assert "rental cost" in result["assumptions"]["electricity_cost_note"]
    assert "residency" in result["caveat"] and "latency" in result["caveat"]
    assert len(result["balanced_scores"]) == 5
    assert all(0 <= score <= 1 for score in result["balanced_scores"].values())
    print("M6 carbon scheduling checks passed.")


if __name__ == "__main__":
    main()
