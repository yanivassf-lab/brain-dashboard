# brain-dashboard

## Setup & Installation

1. **Create and activate a virtual environment (Python 3.12 recommended):**
   ```bash
   python3.12 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **(Recommended) Install the package in editable mode:**
   ```bash
   pip install -e .
   ```

## Running the Folder Watcher

You can run the folder watcher in two ways:

### 1. As a CLI tool (recommended)
After installing the package (step 3 above), run:
```bash
watch-folder --folder brain_dashboard/data --interval 30
```
- `--folder` : Folder to watch for new files (default: value from `settings.py)`)
- `--interval` : Polling interval in seconds (default: 30)

### 2. As a Python module
```bash
python -m brain_dashboard.scripts.admin_app 
python -m brain_dashboard.scripts.run_app 
python -m brain_dashboard.scripts.watch_folder
```

## Packaging
This project uses [PEP 621](https://www.python.org/dev/peps/pep-0621/) and `pyproject.toml` for modern Python packaging. The CLI entry point `watch-folder` is provided for convenience.

## Author
Refael Kohen (<refael.kohen@gmail.com>)


To open the admin site: 
http://127.0.0.1:5000/admin/


Install freesurfer and set the environment variable:
https://surfer.nmr.mgh.harvard.edu/fswiki//FS7_mac

export FREESURFER_HOME=/Applications/freesurfer/8.0.0/
export SUBJECTS_DIR=/Users/user/Documents/pythonProject/brain-dashboard/freesurfer-files/subjects
source $FREESURFER_HOME/SetUpFreeSurfer.sh

## Documentation (Read the Docs)

Full documentation is hosted on Read the Docs and contains detailed installation, administration and user guides, examples, and templates.

- Read the Docs: https://readthedocs.org/projects/brain-dashboard/ (placeholder — replace with your project URL)
- Source for the docs lives in the `docs/` directory of this repository. To avoid duplication, the long-form documentation lives there; the README only links to it.

To build the docs locally (optional):

1. Install Sphinx and build tools:
   ```bash
   pip install -U sphinx sphinx-rtd-theme
   ```
2. From the project root run:
   ```bash
   sphinx-build -b html docs/ docs/_build/html
   ```