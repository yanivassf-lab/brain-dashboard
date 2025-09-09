import argparse
import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import or_

from brain_dashboard.scripts.admin_app import User, USER_STATUS_FREESURFER_PROCESSING, \
    USER_STATUS_FREESURFER_COMPLETED, USER_STATUS_FREESURFER_FAILED, USER_STATUS_UPDATE_TABLE_PROCESSING, \
    USER_STATUS_UPDATE_TABLE_COMPLETED, \
    USER_STATUS_UPDATE_TABLE_FAILED, db
from brain_dashboard.settings import DATA_DIR, SUBJECTS_DIR, FREESURFER_ENV_FILE, FREESURFER_HOME, ASEG_DF, APARC_LH_DF, \
    APARC_RH_DF, logger
from brain_dashboard.settings import FLASK_APP


class FreeSurfer:
    def __init__(self, file_name):
        self.freesurfer_env = {}
        self.freesurfer_env['SUBJECTS_DIR'] = str(SUBJECTS_DIR)

        # Define paths
        self.input_nii_path = DATA_DIR / file_name
        self.subject_name = file_name.replace(''.join(Path(file_name).suffixes), '')  # Remove extension for subject ID

    def _run_command(self, command):
        """
        Executes a shell command and captures its output.
        Returns True for success, False for failure.
        """
        try:
            # Popen is used to get more control over the subprocess, including
            # capturing stdout/stderr and setting the environment.
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                check=True,
            )
            return True, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed with return code {e.returncode}")
            logger.error(f"Stdout: {e.returncode}")
            logger.error(f"Stderr: {e.stderr}")
            return False, e.stdout, e.stderr

    def run_freesurfer(self):
        """
        This function runs in a separate process to execute FreeSurfer commands.
        """

        # Run recon-all
        recon_all_cmd = (
            f"export FREESURFER_HOME={FREESURFER_HOME} && "
            f"export SUBJECTS_DIR={SUBJECTS_DIR} && "
            f"source {FREESURFER_ENV_FILE} && "
            f"recon-all -i {self.input_nii_path} -s {self.subject_name} -all"
        )
        logger.info(f"Running recon-all command: {recon_all_cmd} for user {self.subject_name}...")
        success, stdout, stderr = self._run_command(recon_all_cmd)
        if success:
            logger.info(f"recon-all command: {recon_all_cmd} completed successfully for user {self.subject_name}.")
        else:
            logger.error(f"Command failed: {recon_all_cmd} with error: {stdout}")  # FreeSurfer logs are in stdout
            raise RuntimeError(f"Command failed: {recon_all_cmd} with error: {stdout}")

    def update_table(self, existing_file, new_subject_file):
        """
        Backup existing table file with date, append new subjects, and save updated table.

        :param existing_file: Path to existing table CSV
        :param new_subject_file: Path to new subjects table CSV
        :return: Path to updated table
        """
        # Backup existing file
        # Check if existing file exists and is not empty
        if os.path.exists(existing_file) and os.path.getsize(existing_file) > 0:

            date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = Path(f"{str(existing_file).rstrip('.csv')}_backup_{date_str}.csv")
            shutil.copy(existing_file, backup_file)
            print(f"Backup created: {backup_file}")

            # Load tables
            df_existing = pd.read_csv(existing_file, header=0)
            df_new = pd.read_csv(new_subject_file, header=0)

            # Assume first column is the subject identifier
            id_col = df_existing.columns[0]

            # Remove old row(s) from existing if same ID exists in new
            df_existing = df_existing[~df_existing[id_col].isin(df_new[id_col])]

            # Combine tables (new replaces old if present)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        else:
            # First-time: just use new table
            df_combined = pd.read_csv(new_subject_file, header=0)

        # Save updated table
        df_combined.to_csv(existing_file, index=False)
        print(f"Updated table saved: {existing_file}")
        return existing_file

    def successful_subjects(self):

        successful_users = User.query.filter(
            or_(
                User.status == USER_STATUS_FREESURFER_COMPLETED,
                User.status == USER_STATUS_UPDATE_TABLE_FAILED
            )
        ).all()
        successful_subjects = [user.file_name for user in successful_users]
        return ' '.join(successful_subjects)

    def update_freesurfer_table(self, all_completed=False):
        # Determine subjects
        subject_names = self.successful_subjects() if all_completed else self.subject_name

        table_commands = [
            ("asegstats2table", ASEG_DF, "--meas volume"),
            ("aparcstats2table --hemi lh", APARC_LH_DF, ""),
            ("aparcstats2table --hemi rh", APARC_RH_DF, "")
        ]

        for cmd_base, df_name, meas_flag in table_commands:
            with tempfile.NamedTemporaryFile(suffix=".csv", delete=True) as tmpfile:
                tablefile_path = tmpfile.name
                cmd = (
                    f"export FREESURFER_HOME={FREESURFER_HOME} && "
                    f"export SUBJECTS_DIR={SUBJECTS_DIR} && "
                    f"source {FREESURFER_ENV_FILE} && "
                    f"{cmd_base} --subjects {subject_names} {meas_flag} --delimiter comma --tablefile {tablefile_path}"
                )
                logger.info(f"Running update freesurfer command: {cmd} for user {self.subject_name}...")
                success, stdout, stderr = self._run_command(cmd)
                if not success:
                    logger.error(
                        f"Command failed: {cmd} with error: {stdout} {stderr}")  # FreeSurfer logs are in stdout
                    raise RuntimeError(f"Command failed: {cmd} with error: {stdout} {stderr}")

                # Update the real table safely
                existing_file = df_name
                self.update_table(existing_file=existing_file, new_subject_file=tablefile_path)
                logger.info(f"Updated table {existing_file} with subjects: {subject_names}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run FreeSurfer processing for a user.")
    parser.add_argument("--file-name", type=str, required=True, help="File name to process")
    parser.add_argument("--recon-all", action='store_true', help="Run recon-all command")
    parser.add_argument("--update-table", action='store_true', help="Run asegstats2table and aparcstats2table command")
    args = parser.parse_args()

    file_name = args.file_name
    with FLASK_APP.app_context():
        user = User.query.filter_by(file_name=file_name).first()
        if not user:
            raise ValueError(f"User with file name {file_name} not found in database.")

        freesurfer = FreeSurfer(file_name=user.file_name)
        if args.recon_all:
            logger.info(f"Starting FreeSurfer processing for user {user.file_name}...")
            user.status = USER_STATUS_FREESURFER_PROCESSING
            db.session.commit()
            # Start a process to run the user job in the background
            try:
                freesurfer.run_freesurfer()
                user.status = USER_STATUS_FREESURFER_COMPLETED
                db.session.commit()
            except RuntimeError as e:
                user.status = USER_STATUS_FREESURFER_FAILED
                logger.error(f"FreeSurfer processing failed for user {user.file_name}: {e}")
                db.session.commit()
                raise RuntimeError(f"FreeSurfer processing failed for user {user.file_name}: {e}")

        if args.update_table:
            if user.status != USER_STATUS_FREESURFER_COMPLETED and user.status != USER_STATUS_UPDATE_TABLE_FAILED:
                logger.error(
                    f"Cannot update table: User {user.file_name} status is not '{USER_STATUS_FREESURFER_COMPLETED}'.")
                raise RuntimeError(
                    f"Cannot update table: User {user.file_name} status is not '{USER_STATUS_FREESURFER_COMPLETED}'.")
            try:
                logger.info(f"Starting FreeSurfer table update for user {user.file_name}...")
                user.status = USER_STATUS_UPDATE_TABLE_PROCESSING
                db.session.commit()
                freesurfer.update_freesurfer_table()
                user.status = USER_STATUS_UPDATE_TABLE_COMPLETED
            except RuntimeError as e:
                user.status = USER_STATUS_UPDATE_TABLE_FAILED
                logger.error(f"Updating FreeSurfer tables failed for user {user.file_name}: {e}")
                raise RuntimeError(f"Updating FreeSurfer tables failed for user {user.file_name}: {e}")
            db.session.commit()

"""
Instructions to run FreeSurfer processing and update tables for a user:
1. Ensure the Flask application and database are set up correctly.
2. Place the NIfTI file to be processed in the DATA_DIR directory.
3. Run the following commands in the terminal:
    python freesurfer.py --file-name <your_file_name.nii> --recon-all
    python freesurfer.py --file-name <your_file_name.nii> --update-table
    Replace <your_file_name.nii> with the actual file name.
"""