from __future__ import annotations

import argparse
import csv
import gzip
import shutil
import subprocess
from pathlib import Path
from typing import Iterable, Sequence


DEFAULT_BASE_DIR = Path("/home/jonyb/Downloads")
DEFAULT_OUTPUT_NAME = "subsamples_emobon"
DEFAULT_SEED = 12345

DEFAULT_INPUT_FILES = {
    "m1_r1": "EMOBON_RFormosa_So_210805_micro_1_DBH_AAALOSDA_1_1_HMNJKDSX3.UDI236_clean.fastq.gz",
    "m1_r2": "EMOBON_RFormosa_So_210805_micro_1_DBH_AAALOSDA_1_2_HMNJKDSX3.UDI236_clean.fastq.gz",
    "m2_r1": "EMOBON_RFormosa_So_210805_micro_2_DBH_AAAMOSDA_4_1_HMNJKDSX3.UDI250_clean.fastq.gz",
    "m2_r2": "EMOBON_RFormosa_So_210805_micro_2_DBH_AAAMOSDA_4_2_HMNJKDSX3.UDI250_clean.fastq.gz",
}


def parse_fractions(raw: str) -> list[int]:
    values: list[int] = []
    seen: set[int] = set()
    for chunk in raw.split(","):
        clean = chunk.strip()
        if not clean:
            continue
        value = int(clean)
        if value <= 0 or value > 100:
            raise argparse.ArgumentTypeError("fractions must be integers between 1 and 100")
        if value == 100:
            continue
        if value not in seen:
            values.append(value)
            seen.add(value)
    if not values:
        raise argparse.ArgumentTypeError("provide at least one fraction below 100")
    return sorted(values)


def resolve_inputs(base_dir: Path, overrides: dict[str, str]) -> dict[str, Path]:
    resolved: dict[str, Path] = {}
    for key, default_name in DEFAULT_INPUT_FILES.items():
        file_name = overrides.get(key) or default_name
        candidate = Path(file_name).expanduser()
        resolved[key] = candidate if candidate.is_absolute() else base_dir / candidate
    return resolved


def validate_inputs(input_paths: dict[str, Path]) -> None:
    missing = [str(path) for path in input_paths.values() if not path.exists()]
    if missing:
        missing_block = "\n".join(f"- {path}" for path in missing)
        raise FileNotFoundError(f"Missing input FASTQ files:\n{missing_block}")


def ensure_seqtk_available() -> None:
    if shutil.which("seqtk") is None:
        raise RuntimeError("seqtk is not available in PATH")


def concatenate_files(inputs: Sequence[Path], output_path: Path, force: bool = False) -> None:
    if output_path.exists() and not force:
        print(f"Skipping existing concatenated file: {output_path}")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as writer:
        for input_path in inputs:
            with input_path.open("rb") as reader:
                shutil.copyfileobj(reader, writer)


def run_seqtk_sample(input_fastq: Path, fraction: float, seed: int, output_fastq: Path, force: bool = False) -> None:
    if output_fastq.exists() and not force:
        print(f"Skipping existing subsample: {output_fastq}")
        return

    output_fastq.parent.mkdir(parents=True, exist_ok=True)
    command = ["seqtk", "sample", "-s", str(seed), str(input_fastq), str(fraction)]
    with output_fastq.open("wb") as raw_handle:
        with gzip.GzipFile(fileobj=raw_handle, mode="wb") as gz_handle:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            assert process.stdout is not None
            shutil.copyfileobj(process.stdout, gz_handle)
            _, stderr = process.communicate()
    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, command, stderr=stderr)


def sample_rows(output_dir: Path, percents: Iterable[int]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for percent in percents:
        sample_id = f"EMOBON_Sub_{percent}"
        rows.append(
            {
                "sample": sample_id,
                "run_accession": "0",
                "instrument_platform": "ILLUMINA",
                "fastq_1": str(output_dir / f"{sample_id}_R1.fastq.gz"),
                "fastq_2": str(output_dir / f"{sample_id}_R2.fastq.gz"),
                "fasta": "",
            }
        )

    rows.append(
        {
            "sample": "EMOBON_Sub_100",
            "run_accession": "0",
            "instrument_platform": "ILLUMINA",
            "fastq_1": str(output_dir / "EMOBON_Concat_100_R1.fastq.gz"),
            "fastq_2": str(output_dir / "EMOBON_Concat_100_R2.fastq.gz"),
            "fasta": "",
        }
    )
    return rows


def write_samplesheet(csv_path: Path, rows: Sequence[dict[str, str]]) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as csv_handle:
        writer = csv.DictWriter(
            csv_handle,
            fieldnames=["sample", "run_accession", "instrument_platform", "fastq_1", "fastq_2", "fasta"],
        )
        writer.writeheader()
        writer.writerows(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Concatenate FASTQ pairs and generate nf-core/mag subsamples")
    parser.add_argument("--base-dir", type=Path, default=DEFAULT_BASE_DIR, help="Base directory containing source FASTQ files")
    parser.add_argument("--out-dir", type=Path, help="Output directory for concatenated and subsampled FASTQ files")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Random seed passed to seqtk")
    parser.add_argument("--fractions", type=parse_fractions, default=parse_fractions("10,20,30,40,50,60,70,80,90"), help="Comma-separated percentages below 100")
    parser.add_argument("--m1-r1", default=DEFAULT_INPUT_FILES["m1_r1"], help="FASTQ file name or absolute path for sample M1 R1")
    parser.add_argument("--m1-r2", default=DEFAULT_INPUT_FILES["m1_r2"], help="FASTQ file name or absolute path for sample M1 R2")
    parser.add_argument("--m2-r1", default=DEFAULT_INPUT_FILES["m2_r1"], help="FASTQ file name or absolute path for sample M2 R1")
    parser.add_argument("--m2-r2", default=DEFAULT_INPUT_FILES["m2_r2"], help="FASTQ file name or absolute path for sample M2 R2")
    parser.add_argument("--force", action="store_true", help="Overwrite existing concatenated or subsampled files")
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs and print the planned work without running seqtk")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    base_dir = args.base_dir.expanduser()
    output_dir = args.out_dir.expanduser() if args.out_dir else base_dir / DEFAULT_OUTPUT_NAME
    csv_out = output_dir / "samplesheet.csv"
    input_paths = resolve_inputs(
        base_dir,
        {
            "m1_r1": args.m1_r1,
            "m1_r2": args.m1_r2,
            "m2_r1": args.m2_r1,
            "m2_r2": args.m2_r2,
        },
    )

    validate_inputs(input_paths)

    concat_r1 = output_dir / "EMOBON_Concat_100_R1.fastq.gz"
    concat_r2 = output_dir / "EMOBON_Concat_100_R2.fastq.gz"
    rows = sample_rows(output_dir, args.fractions)

    print("1. Input FASTQ files validated.")
    print(f"2. Output directory: {output_dir}")
    print(f"3. Fractions to generate: {', '.join(str(percent) for percent in args.fractions)}")

    if args.dry_run:
        print("Dry run requested; no files were written.")
        print(f"Would create: {concat_r1}")
        print(f"Would create: {concat_r2}")
        print(f"Would write samplesheet: {csv_out}")
        return

    ensure_seqtk_available()

    print("4. Concatenating source FASTQ files...")
    concatenate_files([input_paths["m1_r1"], input_paths["m2_r1"]], concat_r1, force=args.force)
    concatenate_files([input_paths["m1_r2"], input_paths["m2_r2"]], concat_r2, force=args.force)

    print("5. Running seqtk subsampling...")
    for percent in args.fractions:
        fraction = percent / 100.0
        sample_id = f"EMOBON_Sub_{percent}"
        print(f"   -> {sample_id}")
        run_seqtk_sample(concat_r1, fraction, args.seed, output_dir / f"{sample_id}_R1.fastq.gz", force=args.force)
        run_seqtk_sample(concat_r2, fraction, args.seed, output_dir / f"{sample_id}_R2.fastq.gz", force=args.force)

    write_samplesheet(csv_out, rows)
    print(f"6. Completed successfully. Samplesheet written to: {csv_out}")


if __name__ == "__main__":
    main()
