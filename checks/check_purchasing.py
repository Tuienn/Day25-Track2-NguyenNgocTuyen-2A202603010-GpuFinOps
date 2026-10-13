"""Ensure a reservation pays for idle hours as well as active hours."""
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from missions import m3_purchasing as m3

job = {"job_id": "steady", "gpu_type": "X", "num_gpus": "2",
       "hours_per_day": "18", "interruptible": "0"}
catalog = {"X": {"on_demand_hr": "10", "reserved_3yr_hr": "5"}}
with patch.object(m3, "load_csv", return_value=[job]), patch.object(m3, "catalog_by_type", return_value=catalog):
    r = m3.run(False)
assert r["on_demand_monthly"] == 18 * 30 * 2 * 10
assert r["optimized_monthly"] == 24 * 30 * 2 * 5
assert r["recommendations"][0]["billed_gpu_hours"] == 1440
print("Purchasing commitment accounting checks passed.")
