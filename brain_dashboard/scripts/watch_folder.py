#!/usr/bin/env python3

import argparse
import os
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from brain_dashboard.scripts.admin_app import db, User  # Import SQLAlchemy db and User model
from brain_dashboard.settings import DATA_DIR, FLASK_APP


class NewFileHandler(FileSystemEventHandler):
    def __init__(self, process_func, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.process_func = process_func

    def on_created(self, event):
        if event.is_directory:
            return
        self.process_func(event.src_path)

    def on_moved(self, event):
        if event.is_directory:
            return
        self.process_func(event.dest_path)


class Command:
    help = 'Watch a folder for new files; characteristics are provided via Excel, not filename.'

    def add_arguments(self, parser):
        parser.add_argument('--folder', type=str, default=DATA_DIR, help='Folder to watch')
        parser.add_argument('--interval', type=int, default=30, help='Interval time (in seconds) to watch')
        parser.add_argument('--once', action='store_true', help='Process existing files once and exit')

    def process_file(self, file_path):
        filename = os.path.basename(file_path)
        if filename.startswith('.'):
            return
        with FLASK_APP.app_context():
            # Check if file already processed
            if User.query.filter_by(file_name=filename).first():
                print(f"File {filename} already processed. Skipping.")
                return

        print(f"Processing file: {filename}")

        # Use filename (without extension) as user_id
        sample_name, _ = os.path.splitext(filename)

        with FLASK_APP.app_context():
            # Create new User entry
            user = User(
                user_id=sample_name,
                file_name=filename,
                status='preprocessed'
            )
            db.session.add(user)
            db.session.commit()
            print(f"User created for file {filename}.")

    def handle_existing_files(self, folder):
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            if os.path.isfile(file_path):
                self.process_file(file_path)

    def handle(self, *args, **options):
        folder = options.get('folder', DATA_DIR)
        interval = options.get('interval', 30)
        once = options.get('once', False)
        print(f"Watching folder: {folder} (processing existing files first), interval: {interval} seconds.")

        if not os.path.isdir(folder):
            print(f"Error: Folder {folder} does not exist!")
            return

        self.handle_existing_files(folder)

        if once:
            print("Processed existing files. Exiting due to --once flag.")
            return

        event_handler = NewFileHandler(process_func=self.process_file)
        observer = Observer()
        observer.schedule(event_handler, folder, recursive=False)
        observer.start()
        try:
            while True:
                time.sleep(interval)
        except KeyboardInterrupt:
            observer.stop()
            print("Stopped watching folder.")
        observer.join()


def main():
    parser = argparse.ArgumentParser(description="Watch a folder for new files.")
    cmd = Command()
    cmd.add_arguments(parser)
    args = parser.parse_args()
    cmd.handle(**vars(args))

if __name__ == '__main__':
    main()
# This script watches a specified folder for new files and processes them
# Usage as a module:
#   python -m brain_dashboard.scripts.watch_folder --folder data --interval 30
