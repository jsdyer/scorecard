from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from refresh import assemble


class ReceiptTests(unittest.TestCase):
    def test_excludes_releases_on_and_after_decision(self):
        surveys = [dict(edition="test", published=day, url="source", forecasts={"2026-10": {"median": 3}})
                   for day in ["2026-10-01", "2026-10-28", "2026-11-01"]]
        results = assemble(surveys, {"2026-10-28": 2.5}, "2026-11-22")
        self.assertEqual([row["published"] for row in results], ["2026-10-01"])

    def test_only_prior_month_can_enter_undated_comparison(self):
        survey = dict(edition="test", published="2026-11-01", url="source",
                      forecasts={"2026-11": {}, "2026-12": {}})
        rows = assemble([survey], {}, "2026-11-22")
        self.assertEqual([(r["target"], r["actual"]) for r in rows], [("2026-12", None)])

    def test_refuses_to_score_ambiguous_month(self):
        survey = dict(edition="test", published="2026-01-01", url="source", forecasts={"2026-02": {}})
        with self.assertRaisesRegex(ValueError, "Multiple decisions"):
            assemble([survey], {"2026-02-01": 2.5, "2026-02-02": 3.0}, "2026-02-02")
