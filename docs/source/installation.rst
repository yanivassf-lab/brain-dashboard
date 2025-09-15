Installation
============

This page describes how to install and prepare the **brain-dashboard** system for development and production.

Prerequisites
-------------

- **Python 3.12** (recommended)
- **virtualenv**
- **FreeSurfer** (if you will run FreeSurfer processing locally)

The system can be installed on both Linux and Mac operating systems.

FreeSurfer Setup
----------------

To run FreeSurfer processing, download it from the official website and install it following their documentation:
https://surfer.nmr.mgh.harvard.edu/fswiki/DownloadAndInstall

**Remember:**

- Download and install: https://surfer.nmr.mgh.harvard.edu/fswiki/rel7downloads
- Verify prerequisites: https://surfer.nmr.mgh.harvard.edu/fswiki/BuildRequirements
- Place the ``license.txt`` file in the appropriate folder, as described here:
  https://surfer.nmr.mgh.harvard.edu/registration.html
- Check the installation by running the following commands in the ``bash`` shell (``/bin/bash``):

  .. code-block:: bash

      export FREESURFER_HOME=/Applications/freesurfer/8.0.0
      source /Applications/freesurfer/8.0.0/SetUpFreeSurfer.sh
      recon-all --help
      asegstats2table --help
      aparcstats2table --help

After installation, set the required environment variables in your ``.env`` file (see below).

Quick Install
-------------

1. **Set up folders for data and outputs**

    Create necessary directories for the project. Adjust paths as needed.

    Create a folder for project root:

    .. code-block:: bash

        PROJECT_ROOT=/path/to/brain-dashboard-project
        mkdir -p $PROJECT_ROOT

    For example,
        .. code-block:: bash

            PROJECT_ROOT=$HOME/brain-dashboard-project
            mkdir -p $PROJECT_ROOT

    Create a folders for runs outputs:

    .. container:: scrollable

        .. code-block:: bash

            mkdir -p $PROJECT_ROOT/runs/freesurfer_output                # for FreeSurfer tables and folders of the outputs
            mkdir -p $PROJECT_ROOT/runs/config                           # for storing features of the users
            mkdir -p $PROJECT_ROOT/runs/analyses                         # for storing analysis results
            mkdir -p $PROJECT_ROOT/runs/instance                        # for storing database instances
            mkdir -p $PROJECT_ROOT/runs/logs                             # for storing log files
            touch $PROJECT_ROOT/runs/freesurfer_output/aparc_lh.csv      # create empty file for FreeSurfer left aparc
            touch $PROJECT_ROOT/runs/freesurfer_output/aparc_rh.csv      # create empty file for FreeSurfer left aparc
            touch $PROJECT_ROOT/runs/freesurfer_output/aseg_volumes.csv  # create empty file for FreeSurfer aseg volumes
            touch $PROJECT_ROOT/runs/config/users_features.csv           # create empty file for user features

2. **Create and activate a virtual environment**

    .. code-block:: bash

        python3.12 -m venv venv
        source venv/bin/activate

    For example,
        .. code-block:: bash

            python3.12 -m venv $PROJECT_ROOT/brain-dashboard-venv
            source $PROJECT_ROOT/brain-dashboard-venv/bin/activate

3. **Donwload the source code**

    Clone this repository to your project root folder.

    .. code-block:: bash

        cd $PROJECT_ROOT
        git clone https://github.com/yanivassf-lab/brain-dashboard.git



4. **Install the package**

    .. code-block:: bash

        cd $PROJECT_ROOT/brain-dashboard
        pip install .


Environment File (.env)
-----------------------

All runtime configuration is read from a single `.env` file. System administrators should only need to edit this file to configure paths, service ports, and credentials.

**Location:**
Place a file named `.env` in trust location, the path to the file will be saved as environment variable DEFAULT_ENV_PATH.

**Required variables:**

- `FLASK_SECRET_KEY`: Flask secret key for sessions and CSRF protection.
- `PYTHON_EXECUTABLE`: Absolute path to the Python executable used for running scripts.
- `PROJECT_ROOT`: Absolute path to the project root directory.
- `DATA_DIR`: Path to the folder containing the raw data of the users.
- `FREESURFER_HOME`: FreeSurfer installation root (if running FreeSurfer locally).
- `SUBJECTS_DIR`: FreeSurfer `SUBJECTS_DIR` where the outputs of FreeSurfer are stored.
- `FREESURFER_ENV_FILE`: Path to the FreeSurfer environment setup script (e.g., `SetUpFreeSurfer.sh`).
- `PORT_APP`: Port for the main application.
- `PORT_ADMIN`: Port for the admin interface.

**Example .env:**

.. code-block:: bash

   FLASK_SECRET_KEY=dev-secret-key-2adsf4kl0acasd32e2drq346f8b
   PYTHON_EXECUTABLE=/path/to/brain-dashboard-project/brain-dashboard-venv/bin/python
   PROJECT_ROOT=/path/to/brain-dashboard-project
   DATA_DIR=/rawdata
   FREESURFER_HOME=/Applications/freesurfer/8.0.0
   SUBJECTS_DIR=/path/to/brain-dashboard-project/runs/freesurfer_output
   FREESURFER_ENV_FILE=/Applications/freesurfer/8.0.0/SetUpFreeSurfer.sh
   PORT_APP=5006
   PORT_ADMIN=5000

**Security:**

- Never commit `.env` to git. Add it to `.gitignore`.
- Ensure .env is readable only by the app user (chmod 600 .env).


