Installation
============

This page describes how to install and prepare the **brain-dashboard** system for development and production.

Prerequisites
-------------

- **Python 3.12** (recommended)
- **virtualenv**
- **FreeSurfer** (if you will run FreeSurfer processing locally)

FreeSurfer Setup
----------------

If you need to run FreeSurfer processing, download it from https://surfer.nmr.mgh.harvard.edu/fswiki/DownloadAndInstall and
install FreeSurfer according to their documentation. Set the required environment variables in your `.env` file (see bellow).

Quick Install
-------------

1. **Set up folders for data and outputs**

    Create necessary directories for the project. Adjust paths as needed.

    Create a folder for project root:

    .. code-block:: bash

        PROJECT_ROOT=/absolute/path/to/brain-dashboard-project
        mkdir -p $PROJECT_ROOT

    For example,
        .. code-block:: bash

            PROJECT_ROOT=$HOME/brain-dashboard-project
            mkdir -p $PROJECT_ROOT

    Create a folders for runs outputs:

    .. container:: scrollable

        .. code-block:: bash

            mkdir -p $PROJECT_ROOT/freesurfer_output                # for FreeSurfer tables and folders of the outputs
            mkdir -p $PROJECT_ROOT/config                           # for storing features of the users
            mkdir -p $PROJECT_ROOT/analyses                         # for storing analysis results
            mkdir -p $PROJECT_ROOT/instances                        # for storing database instances
            mkdir -p $PROJECT_ROOT/logs                             # for storing log files
            touch $PROJECT_ROOT/freesurfer_output/aparc_lh.csv      # create empty file for FreeSurfer left aparc
            touch $PROJECT_ROOT/freesurfer_output/aparc_rh.csv      # create empty file for FreeSurfer left aparc
            touch $PROJECT_ROOT/freesurfer_output/aseg_volumes.csv  # create empty file for FreeSurfer aseg volumes
            touch $PROJECT_ROOT/config/users_features.csv           # create empty file for user features

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
        git clone ...



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
   PYTHON_EXECUTABLE=/ve-brain-dashboard/bin/python
   PROJECT_ROOT=$PROJECT_ROOT
   DATA_DIR=/rawdata
   FREESURFER_HOME=/Applications/freesurfer/8.0.0/
   SUBJECTS_DIR=$PROJECT_ROOT/freeview_output
   FREESURFER_ENV_FILE=/Applications/freesurfer/8.0.0/SetUpFreeSurfer.sh
   PORT_APP=5006
   PORT_ADMIN=5000

**Security:**

- Never commit `.env` to git. Add it to `.gitignore`.
- Ensure .env is readable only by the app user (chmod 600 .env).


