"""Standalone, deterministic acceptance checks for the M2 reasoning extension.

Run from the repository root: python checks/check_reasoning.py
"""
from __future__ import annotations
import math
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from missions.m2_inference_levers import run
from finops.sustainability import REASONING_ENERGY_MULTIPLIER


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS {message}")


def main() -> None:
    result = run(verbose=False)
    active_cap = run(verbose=False, reasoning_cap=0.05)
    zero_cap = run(verbose=False, reasoning_cap=0.0)
    check(result["total_requests"] == result["reasoning_requests"] + result["normal_requests"],
          "reasoning and normal request counts partition traffic")
    check(math.isclose(result["reasoning_cost"] + result["normal_cost"],
                       result["optimized_daily"], abs_tol=0.005),
          "cohort costs reconcile to optimized total")
    check(math.isclose(result["reasoning_wh"] / result["reasoning_normal_energy_wh"],
                       REASONING_ENERGY_MULTIPLIER, rel_tol=1e-9),
          "reasoning energy uses the sustainability multiplier on observed tokens")
    check(math.isclose(result["reasoning_extra_wh"],
                       result["reasoning_wh"] - result["reasoning_normal_energy_wh"], rel_tol=1e-9),
          "extra reasoning energy is measured against same-token normal energy")
    check(result["reasoning_cap_requests"] <= int(result["total_requests"] * 0.10),
          "default reasoning cap stays within ten percent of request traffic")
    check(result["reasoning_cap_saved_usd"] == 0,
          "cap does not claim an unsupported dollar premium under equal pricing assumptions")
    check(result["reasoning_cap_saved_wh"] >= 0,
          "cap energy savings are nonnegative")
    check(active_cap["reasoning_cap_requests"] <= int(active_cap["total_requests"] * 0.05),
          "active five percent cap respects its request limit")
    check(active_cap["reasoning_cap_saved_wh"] > 0,
          "five percent cap reduces reasoning energy when traffic exceeds the cap")
    check(math.isclose(active_cap["reasoning_cap_total_wh_before"] - active_cap["reasoning_cap_total_wh_after"],
                       active_cap["reasoning_cap_saved_wh"], abs_tol=1e-6),
          "five percent counterfactual energy delta exactly matches reported savings")
    check(zero_cap["reasoning_cap_requests"] == 0,
          "zero cap routes no requests to reasoning")
    check(math.isclose(zero_cap["reasoning_cap_saved_wh"], zero_cap["reasoning_extra_wh"], abs_tol=1e-6),
          "zero cap saves exactly the measured reasoning energy overhead")
    check(math.isclose(zero_cap["reasoning_cap_total_wh_after"],
                       zero_cap["normal_wh"] + zero_cap["reasoning_normal_energy_wh"], abs_tol=1e-6),
          "zero-cap counterfactual equals normal energy for all observed tokens")
    try:
        run(verbose=False, reasoning_cap=1.01)
    except ValueError:
        invalid_rejected = True
    else:
        invalid_rejected = False
    check(invalid_rejected, "out-of-range cap is rejected")
    check(set(result["lever_savings"]) == {"cascade", "cache", "batch"},
          "sequential lever savings are exposed")
    print("== measured reasoning budget ==")
    print(f"traffic {result['reasoning_traffic_share']:.1%}; cost {result['reasoning_cost_share']:.1%}; "
          f"energy {result['reasoning_energy_share']:.1%}; extra {result['reasoning_extra_wh']:,.2f} Wh")
    print(f"10% cap: saved ${result['reasoning_cap_saved_usd']:.2f}, {result['reasoning_cap_saved_wh']:,.2f} Wh")
    print(f"5% sensitivity: saved {active_cap['reasoning_cap_saved_wh']:,.2f} Wh; "
          f"zero cap: saved {zero_cap['reasoning_cap_saved_wh']:,.2f} Wh")


if __name__ == "__main__":
    main()
