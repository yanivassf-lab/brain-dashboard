Running the Application
=======================

This section provides instructions for running the Brain Dashboard application.

Quick Install
-------------

1. **Set up envrionment variable DEFAULT_ENV_PATH**

    set the environment variable `DEFAULT_ENV_PATH` to point to the location of your `.env` file. This file contains all necessary configuration for the application.

    .. code-block:: bash

        export DEFAULT_ENV_PATH=/absolute/path/to/.env


    For example,
        .. code-block:: bash

            export DEFAULT_ENV_PATH=$PROJECT_ROOT/.env

2. **Run the admin site**
    From the project root, activate your virtual environment and run:

    .. code-block:: bash

        source $PROJECT_ROOT/brain-dashboard-venv/bin/activate
        export DEFAULT_ENV_PATH=$PROJECT_ROOT/brain-dashboard-project/.env
        admin-app

    The admin interface will be available at `http://localhost:5000/admin/statistics` (or the port you specified in your `.env` file).

3. **Run the main application**
    In a separate terminal, activate your virtual environment and run:

    .. code-block:: bash

        source $PROJECT_ROOT/brain-dashboard-venv/bin/activate
        export DEFAULT_ENV_PATH=$PROJECT_ROOT/brain-dashboard-project/.env
        run-app

    The main application will be available at `http://localhost:5006` (or the port you specified in your `.env` file).

Running Background Scripts with Crontab
---------------------------------------

To automate data processing, you may want to run `watch_folder.py` as background tasks using `cron`.

**1. Edit your crontab:**

.. code-block:: bash

   crontab -e

**2. Add the following lines (adjust paths as needed):**

.. code-block:: bash

   # Run watch_folder.py every 5 minutes
   */5 * * * * /path/to/venv/bin/python -m brain_dashboard.scripts.watch_folder --once >> /path/to/logs/watch_folder.log 2>&1

**Notes:**

- Replace `/path/to/brain-dashboard` with `$PROJECT_ROOT/brain-dashboard-venv/bin/python`,  and `/path/to/logs` with `$PROJECT_ROOT/runs/logs/watch_folder.log`.

- The `--once` flag ensures the script runs only once per invocation.
