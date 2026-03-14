# FASTQ Subsampling Pipeline for nf-core/mag

A Python script to **concatenate** paired-end FASTQ files and generate **subsampled fractions** (10% – 100%) ready for input into the [nf-core/mag](https://nf-co.re/mag) metagenomics assembly pipeline.

## What it does

1. **Concatenates** two paired-end Illumina samples (M1 + M2) into a single 100% reference FASTQ pair.
2. **Subsamples** the concatenated reads using [`seqtk`](https://github.com/lh3/seqtk) at fractions of **10%, 20%, … 90%, 100%**, always using the same random seed so R1/R2 pairs stay perfectly in sync.
3. **Generates a `samplesheet.csv`** in the format required by nf-core/mag, with one row per fraction.

## Use case

This was designed for benchmarking the nf-core/mag pipeline:
- Compare assembly quality and resource usage at different sequencing depths.
- Determine the minimum sequencing depth needed for reliable MAG recovery.
- Data: EMOBON Ria Formosa sediment metagenomes (UDI236 + UDI250).

## Requirements

- Python 3.8+
- [`seqtk`](https://github.com/lh3/seqtk) installed and available in `$PATH`
- Input FASTQ files (gzipped)

Install seqtk (if not available):
```bash
conda install -c bioconda seqtk
# or
sudo apt install seqtk
```

## Usage

1. **Run** the script with your base directory:

```bash
python run_scirpt.py --base-dir /path/to/your/fastq/files
```

2. **Optionally override** specific input files or output directory:

```bash
python run_scirpt.py \
	--base-dir /path/to/your/fastq/files \
	--m1-r1 sample1_R1.fastq.gz \
	--m1-r2 sample1_R2.fastq.gz \
	--m2-r1 sample2_R1.fastq.gz \
	--m2-r2 sample2_R2.fastq.gz \
	--out-dir /path/to/your/fastq/files/subsamples_emobon
```

3. **Preview the plan** without writing files:

```bash
python run_scirpt.py --base-dir /path/to/your/fastq/files --dry-run
```

4. **Output** will be created in `$BASE_DIR/subsamples_emobon/` by default:

```
subsamples_emobon/
├── EMOBON_Concat_100_R1.fastq.gz     # Full concatenated R1
├── EMOBON_Concat_100_R2.fastq.gz     # Full concatenated R2
├── EMOBON_Sub_10_R1.fastq.gz         # 10% subsample R1
├── EMOBON_Sub_10_R2.fastq.gz         # 10% subsample R2
├── EMOBON_Sub_20_R1.fastq.gz
├── ...
├── EMOBON_Sub_90_R1.fastq.gz
├── EMOBON_Sub_90_R2.fastq.gz
└── samplesheet.csv                   # nf-core/mag input sheet
```

## Output: samplesheet.csv

The generated CSV follows the nf-core/mag format:

| sample | run_accession | instrument_platform | fastq_1 | fastq_2 | fasta |
|--------|--------------|---------------------|---------|---------|-------|
| EMOBON_Sub_10 | 0 | ILLUMINA | `.../EMOBON_Sub_10_R1.fastq.gz` | `.../EMOBON_Sub_10_R2.fastq.gz` | |
| ... | | | | | |
| EMOBON_Sub_100 | 0 | ILLUMINA | `.../EMOBON_Concat_100_R1.fastq.gz` | `.../EMOBON_Concat_100_R2.fastq.gz` | |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `BASE_DIR` | `/home/jonyb/Downloads` | Directory with input FASTQ files |
| `OUT_DIR` | `$BASE_DIR/subsamples_emobon` | Output directory |
| `SEED` | `12345` | Random seed for seqtk (ensures R1/R2 sync) |

## New CLI features

- `--fractions 10,25,50,75,90`: choose custom subsampling percentages below 100
- `--dry-run`: validate inputs and print planned outputs without running `seqtk`
- `--force`: overwrite existing concatenated/subsampled files
- Input validation now fails early if one of the FASTQ files is missing
- `seqtk` is executed without `shell=True`, reducing quoting issues and shell-injection risk

## Tests

```bash
python -m unittest discover -s tests -v
```

## Notes

- The **random seed** (`SEED = 12345`) is critical — using the same seed for R1 and R2 guarantees that the subsampled reads remain properly paired.
- Concatenation is done in pure Python (no external tools needed for this step).
- The 100% sample in the CSV points to the concatenated files, not the originals.

## License

MIT
