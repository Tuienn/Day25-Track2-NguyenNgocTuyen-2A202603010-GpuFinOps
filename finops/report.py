"""Report assembly — the lab's deliverable: baseline vs optimized + savings chart."""
from __future__ import annotations


def build_report(baseline_usd: float, optimized_usd: float, levers: dict,
                 sustainability: dict | None = None, period: str = "monthly") -> str:
    """Return a markdown cost-optimization report."""
    savings = baseline_usd - optimized_usd
    pct = (savings / baseline_usd * 100.0) if baseline_usd > 0 else 0.0
    lines = [
        "# NimbusAI — GPU Cost Optimization Report",
        "",
        f"**Period:** {period}  ",
        f"**Baseline spend:** ${baseline_usd:,.0f}  ",
        f"**Optimized spend:** ${optimized_usd:,.0f}  ",
        f"**Projected savings:** ${savings:,.0f}  (**{pct:.0f}%**)",
        "",
        "## Savings by lever",
        "",
        "| Lever | Savings (USD) |",
        "|---|---|",
    ]
    for name, amount in levers.items():
        lines.append(f"| {name} | ${amount:,.0f} |")
    if sustainability:
        lines += [
            "",
            "## Sustainability",
            "",
            "Illustrative normal query: 800 tokens; energy and carbon are model estimates, not hardware measurements.",
            "",
            f"- Energy per query: {sustainability.get('wh_per_query', 0):.2f} Wh",
            f"- Carbon per query: {sustainability.get('carbon_g', 0):.3f} gCO2e",
            f"- Cleanest region: {sustainability.get('best_region', 'n/a')}",
        ]
    lines += ["", "_Figures are June-2026 as-of snapshots; re-baseline before acting._"]
    return "\n".join(lines)


def savings_waterfall(levers: dict, path: str, baseline_usd: float | None = None) -> str:
    """Write sequential reductions with optional baseline/optimized totals."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return ""
    baseline = baseline_usd if baseline_usd is not None else sum(levers.values())
    names = ["Baseline", *levers, "Optimized"]
    heights = [baseline]
    bottoms = [0.0]
    running = baseline
    labels = [f"${baseline:,.0f}"]
    for amount in levers.values():
        running -= amount
        heights.append(amount)
        bottoms.append(running)
        labels.append(f"-${amount:,.0f}")
    heights.append(running)
    bottoms.append(0.0)
    labels.append(f"${running:,.0f}")
    fig, ax = plt.subplots(figsize=(11, 5.5))
    bars = ax.bar(names, heights, bottom=bottoms,
                  color=["#2e548a"] + ["#427c61"] * len(levers) + ["#2e548a"])
    for bar, label in zip(bars, labels):
        ax.annotate(label, (bar.get_x() + bar.get_width()/2, bar.get_y() + bar.get_height()),
                    xytext=(0, 5), textcoords="offset points", ha="center", fontsize=9)
    ax.set_ylabel("Scenario spend (USD / month)")
    ax.set_xlabel("Sequential savings lever")
    ax.set_title("NimbusAI: baseline to optimized monthly planning scenario")
    ax.set_ylim(0, baseline * 1.15)
    plt.xticks(rotation=18, ha="right", fontsize=9)
    fig.text(0.02, 0.01, "Source: synthetic seed=25 / June-2026 catalog / repeated 30-day scenario; savings require independent scopes.", fontsize=8)
    plt.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path
