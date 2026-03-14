import argparse
import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import run_scirpt as script


class FractionParsingTests(unittest.TestCase):
    def test_parse_fractions_sorts_and_deduplicates(self) -> None:
        self.assertEqual(script.parse_fractions("50,10,50,90,100"), [10, 50, 90])

    def test_parse_fractions_rejects_invalid_values(self) -> None:
        with self.assertRaises(argparse.ArgumentTypeError):
            script.parse_fractions("0,10")


class InputResolutionTests(unittest.TestCase):
    def test_resolve_inputs_uses_base_dir_for_relative_paths(self) -> None:
        base_dir = Path("/tmp/example")
        resolved = script.resolve_inputs(base_dir, {"m1_r1": "reads/sample_r1.fastq.gz"})
        self.assertEqual(resolved["m1_r1"], base_dir / "reads/sample_r1.fastq.gz")

    def test_validate_inputs_reports_missing_files(self) -> None:
        with self.assertRaises(FileNotFoundError) as ctx:
            script.validate_inputs({"m1_r1": Path("/tmp/missing.fastq.gz")})
        self.assertIn("/tmp/missing.fastq.gz", str(ctx.exception))


class SamplesheetTests(unittest.TestCase):
    def test_sample_rows_include_full_sample(self) -> None:
        output_dir = Path("/tmp/subsamples")
        rows = script.sample_rows(output_dir, [10, 20])
        self.assertEqual(rows[-1]["sample"], "EMOBON_Sub_100")
        self.assertEqual(len(rows), 3)

    def test_write_samplesheet_creates_expected_csv(self) -> None:
        rows = script.sample_rows(Path("/tmp/out"), [10])
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "samplesheet.csv"
            script.write_samplesheet(csv_path, rows)
            with csv_path.open(newline="", encoding="utf-8") as handle:
                parsed = list(csv.DictReader(handle))
        self.assertEqual(parsed[0]["sample"], "EMOBON_Sub_10")
        self.assertEqual(parsed[1]["sample"], "EMOBON_Sub_100")


if __name__ == "__main__":
    unittest.main()
