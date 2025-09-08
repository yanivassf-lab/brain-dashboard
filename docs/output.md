# Output folder

Location
- Analysis outputs are written to `runs/analyses/` at the project root. Each analysis run may create a file (pickle, text, images) and often a timestamped filename such as `name-metric-YYYYMMDD_HHMMSS.pkl`.

Typical contents
- Pickle result objects (`.pkl`) containing analysis results and metadata
- Plain text summaries (`.txt`)
- Figures and plots (`.png`, `.svg`)
- Logs and run metadata files

Accessing results
- File system: view or copy files directly, e.g. `ls -lh runs/analyses/` or `open runs/analyses/` on macOS.
- Web UI: the Admin Flask site includes an **Analysis Results** table (see the admin interface). Each analysis entry contains a clickable link to its result file in the table; click the link to view or download the output produced for that analysis.

Best practices
- Keep outputs organized by run or analysis id to avoid filename collisions.
- Archive or remove old outputs when disk space is limited.
- If running analyses programmatically, store run id or timestamp so you can locate the matching output files.

Example commands
- List recent analyses: `ls -lh runs/analyses/ | tail -n 20`
- Copy a result file: `cp runs/analyses/myanalysis-20250907_123456.pkl /path/to/backup/`
# Input folder

Location
- Place input files in the `data/input/` directory at the project root (`data/input/`).

Accepted file types
- Tabular and structured: CSV, TSV, JSON
- Neuroimaging (if used): `.nii`, `.nii.gz`
- Images: `.png`, `.jpg`, `.jpeg`
- Archives: `.zip` (if processing code supports automatic extraction)

Naming and structure
- Use descriptive, stable names. Prefer underscores and avoid spaces, e.g. `sub-01_task-rest_bold.nii.gz` or `subject01_timeseries.csv`.
- You may organize inputs into subfolders (e.g. `data/input/sub-01/` or `data/input/run-20250907-1200/`) to keep runs reproducible.

How to add files
- From Terminal (macOS):
  - Create folder: `mkdir -p data/input`
  - Copy files: `cp /path/to/myfile.nii.gz data/input/`
- If the project exposes an upload feature in the admin Flask UI, you can also upload files via the web interface (when available).

Permissions
- Ensure files are readable by the application process (owner/group/world read as appropriate).

Notes
- Validate inputs against any project-specific schema or README instructions before running analyses.
- Avoid changing filenames after launching an analysis run; outputs reference the input filenames in logs and results metadata.

