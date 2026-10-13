"""Cross-check submitted artifacts and independent cohort/lever accounting."""
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from missions import m5_report

m5_report.run(False)
out = ROOT / 'outputs'
result_bytes = (out / 'results.json').read_bytes()
report_bytes = (out / 'report.md').read_bytes()
writeup_bytes = (out / 'writeup.md').read_bytes()
r = json.loads(result_bytes)
assert r['m5']['baseline_monthly'] - r['m5']['optimized_monthly'] == sum(r['m5']['levers'].values())
assert abs(sum(r['m2']['lever_savings'].values()) -
           (r['m2']['baseline_daily'] - r['m2']['optimized_daily'])) < .01
text = report_bytes.decode()
for term in ('$/1M-token', 'Extension 4', 'Extension 5', 'Cleanest region',
             f"${r['m5']['baseline_monthly']:,}", f"${r['m5']['optimized_monthly']:,}",
             f"${r['m2']['baseline_per_m']:.3f}", f"${r['m2']['optimized_per_m']:.3f}"):
    assert term in text, f'Missing report content: {term}'
with open(out / 'focus_export.csv', newline='') as f:
    focus = list(csv.DictReader(f))
assert len(focus) == 50 and all(row['BillingCurrency'] == 'USD' for row in focus)
assert (out / 'savings.png').read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
# Regenerate the deliverables to prove calculations and rendering text are stable.
m5_report.run(False)
assert (out / 'results.json').read_bytes() == result_bytes
assert (out / 'report.md').read_bytes() == report_bytes
assert (out / 'writeup.md').read_bytes() == writeup_bytes
print('Submission reconciliation, 50-row FOCUS sample and deterministic regeneration passed.')
