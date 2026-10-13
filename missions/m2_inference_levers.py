"""M2 — Inference cost levers and reasoning budget (deck §7 / rubric D.4).

Run: python missions/m2_inference_levers.py
"""
from __future__ import annotations
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from missions._common import load_csv, num
from finops import pricing, sustainability

# $/1M tokens (input, output) — illustrative 2026.
MODEL_PRICES = {"small": (0.20, 0.40), "large": (3.00, 15.00)}
REASONING_CAP = 0.10


def run(verbose: bool = True, reasoning_cap: float = REASONING_CAP) -> dict:
    if not isinstance(reasoning_cap, (int, float)) or not 0.0 <= reasoning_cap <= 1.0:
        raise ValueError("reasoning_cap must be between 0 and 1")
    rows = load_csv("token_usage.csv")
    base_cost = 0.0
    total_tokens = 0
    cascade_cost = cache_cost = opt_cost = 0.0
    reasoning_cost = normal_cost = 0.0
    reasoning_wh = normal_wh = 0.0
    reasoning_tokens = normal_tokens = 0
    reasoning_count = normal_count = 0
    reasoning_items = []

    for idx, r in enumerate(rows):
        inp, out = int(num(r["input_tokens"])), int(num(r["output_tokens"]))
        cached = int(num(r["cached_input_tokens"]))
        is_batch = bool(int(num(r["is_batch"])))
        reasoning = bool(int(num(r["is_reasoning"])))
        tokens = inp + out
        total_tokens += tokens

        # Baseline: every request uses large, without cache or batch discounts.
        lin, lout = MODEL_PRICES["large"]
        base_cost += pricing.request_cost(inp, out, lin, lout)

        # Sequential stages make each lever's marginal savings measurable.
        pin, pout = MODEL_PRICES[r["route_tier"]]
        cascade = pricing.request_cost(inp, out, pin, pout)
        cached_stage = pricing.request_cost(inp, out, pin, pout, cached_in=cached)
        optimized = pricing.request_cost(inp, out, pin, pout, cached_in=cached, batch=is_batch)
        cascade_cost += cascade
        cache_cost += cached_stage
        opt_cost += optimized

        wh = sustainability.wh_per_query(tokens, is_reasoning=reasoning)
        if reasoning:
            reasoning_count += 1
            reasoning_tokens += tokens
            reasoning_cost += optimized
            reasoning_wh += wh
            # Output length is used as a deterministic proxy for task complexity.
            normal_wh_for_tokens = sustainability.wh_per_query(tokens)
            reasoning_items.append((out, idx, tokens, wh, normal_wh_for_tokens))
        else:
            normal_count += 1
            normal_tokens += tokens
            normal_cost += optimized
            normal_wh += wh

    base_pm = pricing.dollars_per_million(base_cost, total_tokens)
    opt_pm = pricing.dollars_per_million(opt_cost, total_tokens)
    savings_pct = (1 - opt_cost / base_cost) * 100 if base_cost else 0.0
    count = len(rows)
    reason_share_cost = reasoning_cost / opt_cost if opt_cost else 0.0
    reason_share_traffic = reasoning_count / count if count else 0.0
    reason_share_energy = reasoning_wh / (reasoning_wh + normal_wh) if reasoning_wh + normal_wh else 0.0

    # Retain the configured share of requests, ordered by observed output length.
    # This is an offline proxy only; no quality or input-time complexity labels exist.
    cap_count = min(reasoning_count, int(count * reasoning_cap))
    retained = {item[1] for item in sorted(reasoning_items, key=lambda x: (-x[0], x[1]))[:cap_count]}
    downgraded = [item for item in reasoning_items if item[1] not in retained]
    cap_saved_wh = sum(normal_wh * (sustainability.REASONING_ENERGY_MULTIPLIER - 1.0)
                       for _, _, _, _, normal_wh in downgraded)
    total_wh = reasoning_wh + normal_wh
    cap_after_wh = total_wh - cap_saved_wh
    cap_reason_count = cap_count
    cap_reason_traffic_pct = (cap_reason_count / count * 100) if count else 0.0
    # Explicit scenario assumption: same token counts, tier, prices, cache and
    # batch behavior after routing. Thus there is no invented $ premium to save.
    cap_saved_usd = 0.0

    lever_savings = {
        "cascade": round(base_cost - cascade_cost, 6),
        "cache": round(cascade_cost - cache_cost, 6),
        "batch": round(cache_cost - opt_cost, 6),
    }
    if verbose:
        print("== M2 Inference Cost Levers ==")
        print(f"requests={count}  tokens={total_tokens:,}")
        print(f"baseline  : ${base_cost:,.2f}/day   ${base_pm:.3f}/1M-token")
        print(f"optimized : ${opt_cost:,.2f}/day   ${opt_pm:.3f}/1M-token")
        print(f"savings   : {savings_pct:.1f}%  (cascade + caching + batch)")
        print("lever savings: " + ", ".join(f"{k} ${v:,.2f}" for k, v in lever_savings.items()))
        print(f"discount stack (batch + 100% cache): {pricing.discount_stack(batch=True, cache_hit_frac=1.0):.3f} of naive")
        print("== Reasoning budget ==")
        print(f"reasoning: {reasoning_count}/{count} requests ({reason_share_traffic:.1%}), "
              f"${reasoning_cost:,.2f} ({reason_share_cost:.1%} of optimized cost), {reasoning_wh:,.2f} Wh ({reason_share_energy:.1%} of energy)")
        print(f"normal   : {normal_count}/{count} requests, ${normal_cost:,.2f}, {normal_wh:,.2f} Wh")
        print(f"same tokens at normal energy: reasoning would use {sustainability.wh_per_query(reasoning_tokens):,.2f} Wh; "
              f"reasoning overhead is {reasoning_wh - sustainability.wh_per_query(reasoning_tokens):,.2f} Wh")
        print(f"{reasoning_cap:.0%} cap: keep {cap_reason_count} highest-output reasoning requests ({cap_reason_traffic_pct:.1f}% of all); "
              f"estimated savings ${cap_saved_usd:.2f}, {cap_saved_wh:,.2f} Wh")
        print(f"energy after cap: {cap_after_wh:,.2f} Wh (before: {total_wh:,.2f} Wh)")
        print("offline scenario only: observed output length proxies complexity; production routing needs an input-side task classifier, confidence gate, and quality validation.")
        print("cap assumption: same token volume, tier, prices, caching and batching; no dollar premium is assigned to reasoning.")

    return {
        "baseline_daily": round(base_cost, 2), "optimized_daily": round(opt_cost, 2),
        "baseline_per_m": round(base_pm, 3), "optimized_per_m": round(opt_pm, 3),
        "savings_pct": round(savings_pct, 1), "total_tokens": total_tokens,
        "lever_savings": lever_savings,
        "cascade_daily": round(cascade_cost, 6), "cache_daily": round(cache_cost, 6),
        "reasoning_requests": reasoning_count, "normal_requests": normal_count,
        "total_requests": count, "reasoning_tokens": reasoning_tokens, "normal_tokens": normal_tokens,
        "reasoning_cost": round(reasoning_cost, 6), "normal_cost": round(normal_cost, 6),
        "reasoning_wh": round(reasoning_wh, 6), "normal_wh": round(normal_wh, 6),
        "reasoning_cost_share": round(reason_share_cost, 6),
        "reasoning_traffic_share": round(reason_share_traffic, 6),
        "reasoning_energy_share": round(reason_share_energy, 6),
        "reasoning_normal_energy_wh": round(sustainability.wh_per_query(reasoning_tokens), 6),
        "reasoning_extra_wh": round(reasoning_wh - sustainability.wh_per_query(reasoning_tokens), 6),
        "reasoning_cap_fraction": reasoning_cap, "reasoning_cap_requests": cap_reason_count,
        "reasoning_cap_traffic_pct": round(cap_reason_traffic_pct, 3),
        "reasoning_cap_saved_usd": round(cap_saved_usd, 6),
        "reasoning_cap_saved_wh": round(cap_saved_wh, 6),
        "reasoning_cap_total_wh_before": round(total_wh, 6),
        "reasoning_cap_total_wh_after": round(cap_after_wh, 6),
        "reasoning_cap_assumption": "same tokens, tier, prices, caching and batching; no dollar premium assigned",
        "reasoning_routing_rule": "offline output-length scenario proxy only; production requires an input-side task classifier, confidence gate, and quality validation",
    }


if __name__ == "__main__":
    run()
