#!/usr/bin/env python3
import logging
import os
import subprocess

import pandas as pd
from flask_admin import Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from flask import send_file, abort, request  # add send_file and abort

from brain_dashboard.settings import DATA_DIR, PYTHON_EXECUTABLE, FLASK_APP, USERS_CHARACTERISTICS_CSV_PATH, logger, \
    PORT_ADMIN

db = SQLAlchemy(FLASK_APP)

# Status constants
USER_STATUS_PREPROCESSED = 'preprocessed'
USER_STATUS_FREESURFER_PROCESSING = 'freesurfer_processing'
USER_STATUS_FREESURFER_COMPLETED = 'freesurfer_completed'
USER_STATUS_FREESURFER_FAILED = 'freesurfer_failed'
USER_STATUS_UPDATE_TABLE_PROCESSING = 'update_table_processing'
USER_STATUS_UPDATE_TABLE_COMPLETED = 'update_table_completed'
USER_STATUS_UPDATE_TABLE_FAILED = 'update_table_failed'


class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.String, primary_key=True)
    file_name = db.Column(db.String, nullable=False)
    status = db.Column(db.String, default=USER_STATUS_PREPROCESSED, nullable=False)


class AnalysisResult(db.Model):
    __tablename__ = 'analysis_results'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    analysis_name = db.Column(db.String)
    selected_users = db.Column(db.String)
    selected_feature = db.Column(db.String)
    selected_statistical = db.Column(db.String)
    results = db.Column(db.String, nullable=True)  # Store JSON as string
    status = db.Column(db.String)
    timestamp = db.Column(db.String)


class UserAdmin(ModelView):
    column_list = ('user_id', 'status', 'file_name')
    
    def _format_status(view, context, model, name):
        from markupsafe import Markup
        status = getattr(model, name)
        if status == 'freesurfer_completed' or status == 'update_table_completed':
            return Markup('<span class="label label-success">{}</span>'.format(status))
        elif status == 'freesurfer_failed' or status == 'update_table_failed':
            return Markup('<span class="label label-danger">{}</span>'.format(status))
        elif status == 'freesurfer_processing' or status == 'update_table_processing':
            return Markup('<span class="label label-warning">{}</span>'.format(status))
        else:
            return Markup('<span class="label label-info">{}</span>'.format(status))
    
    column_formatters = {
        'status': _format_status
    }


class AnalysisAdmin(ModelView):
    column_list = (
    'id', 'status', 'analysis_name', 'selected_users', 'selected_feature', 'selected_statistical', 'timestamp', 'results')
    
    def _format_status(view, context, model, name):
        from markupsafe import Markup
        status = getattr(model, name)
        if status == 'completed':
            return Markup('<span class="label label-success">{}</span>'.format(status))
        elif status == 'failed':
            return Markup('<span class="label label-danger">{}</span>'.format(status))
        elif status == 'processing':
            return Markup('<span class="label label-warning">{}</span>'.format(status))
        else:
            return Markup('<span class="label label-info">{}</span>'.format(status))
    
    def _format_statistical_test(view, context, model, name):
        from markupsafe import Markup
        test = getattr(model, name)
        return Markup('<span class="label label-default">{}</span>'.format(test))
    
    def _format_results(view, context, model, name):
        from markupsafe import Markup
        file_path = getattr(model, name)
        if file_path and os.path.isfile(file_path):
            filename = os.path.basename(file_path)
            # Use a download route
            return Markup(f'<a href="/admin/download_result?path={file_path}" download="{filename}">{filename}</a>')
        elif file_path:
            return Markup(f'<span>{file_path}</span>')
        else:
            return ''

    def _format_selected_users(view, context, model, name):
        from markupsafe import Markup, escape
        users = getattr(model, name)
        if users:
            user_list = [escape(u.strip()) for u in users.split(',') if u.strip()]
            return Markup('<br>'.join(user_list))
        return ''

    column_formatters = {
        'status': _format_status,
        'selected_statistical': _format_statistical_test,
        'results': _format_results,
        'selected_users': _format_selected_users
    }


class DatabaseView(BaseView):
    def is_accessible(self):
        return True
    
    @expose('/')
    def index(self):
        # Get basic database statistics
        user_count = User.query.count()
        analysis_count = AnalysisResult.query.count()
        
        # Get user status statistics
        user_status_stats = db.session.query(
            User.status, 
            db.func.count(User.user_id).label('count')
        ).group_by(User.status).all()
        
        # Get analysis status statistics
        analysis_status_stats = db.session.query(
            AnalysisResult.status, 
            db.func.count(AnalysisResult.id).label('count')
        ).group_by(AnalysisResult.status).all()
        
        # Get analysis statistical test statistics
        statistical_test_stats = db.session.query(
            AnalysisResult.selected_statistical, 
            db.func.count(AnalysisResult.id).label('count')
        ).group_by(AnalysisResult.selected_statistical).all()
        
        return self.render(
            'database_admin.html',
            user_count=user_count,
            analysis_count=analysis_count,
            user_status_stats=user_status_stats,
            analysis_status_stats=analysis_status_stats,
            statistical_test_stats=statistical_test_stats
        )


# Override the admin index to show statistics instead of the default home page
@FLASK_APP.route('/admin/')
def admin_index():
    from flask import render_template
    # Get the same data as the Statistics view
    user_count = User.query.count()
    analysis_count = AnalysisResult.query.count()
    
    user_status_stats = db.session.query(
        User.status, 
        db.func.count(User.user_id).label('count')
    ).group_by(User.status).all()
    
    analysis_status_stats = db.session.query(
        AnalysisResult.status, 
        db.func.count(AnalysisResult.id).label('count')
    ).group_by(AnalysisResult.status).all()
    
    statistical_test_stats = db.session.query(
        AnalysisResult.selected_statistical, 
        db.func.count(AnalysisResult.id).label('count')
    ).group_by(AnalysisResult.selected_statistical).all()
    
    return render_template(
        'admin_index.html',
        user_count=user_count,
        analysis_count=analysis_count,
        user_status_stats=user_status_stats,
        analysis_status_stats=analysis_status_stats,
        statistical_test_stats=statistical_test_stats
    )


admin = Admin(FLASK_APP, name='Brain Dashboard Admin', template_mode='bootstrap3')
admin.add_view(DatabaseView(name='Statistics', endpoint='statistics'))
admin.add_view(UserAdmin(User, db.session))
admin.add_view(AnalysisAdmin(AnalysisResult, db.session))

# Disable authentication for development
def is_accessible(self):
    return True

# Apply to all views
DatabaseView.is_accessible = is_accessible
UserAdmin.is_accessible = is_accessible
AnalysisAdmin.is_accessible = is_accessible

class RunProcessorView(BaseView):
    def is_accessible(self):
        return True
    
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        from flask import request, redirect, url_for, flash
        if request.method == 'POST':
            action = request.form.get('action')
            if action == 'run_reconall':
                user_id = request.form.get('user_id_freesurfer')
                if user_id:
                    user = User.query.get(user_id)
                    if user:
                        try:
                            process = subprocess.Popen(
                                [
                                    PYTHON_EXECUTABLE,  # Use the Python executable from the environment
                                    '-m',
                                    'brain_dashboard.scripts.freesurfer',
                                    '--file-name', user.file_name,
                                    '--recon-all',
                                ],
                                shell=False,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True,
                            )
                            # Log the process ID for tracking
                            logging.info(
                                f"Started freesurfer processing for user '{user_id}', file name {user.file_name}, PID: {process.pid}, with command {PYTHON_EXECUTABLE} -m brain_dashboard.scripts.free_surfer --file-name {user.file_name} --recon-all.")
                            flash(f"Started freesurfer processing for user '{user_id}', file name {user.file_name}, PID: {process.pid}.",
                                  'success')

                        except Exception as e:
                            logger.error(f'Failed freesurfer run for user {user_id}: {str(e)}, Command used: {PYTHON_EXECUTABLE} -m brain_dashboard.scripts.freesurfer --file-name {user.file_name} --recon-all')
                            flash(f'Failed freesurfer run for user {user_id}: {str(e)}', 'error')
                return redirect(url_for('.index'))
            elif action == 'run_update_table':
                user_id = request.form.get('user_id_update_table')
                if user_id:
                    user = User.query.get(user_id)
                    if user:
                        try:
                            process = subprocess.Popen(
                                [
                                    PYTHON_EXECUTABLE,  # Use the Python executable from the environment
                                    '-m',
                                    'brain_dashboard.scripts.freesurfer',
                                    '--file-name', user.file_name,
                                    '--update-table',
                                ],
                                shell=False,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True,
                            )
                            logger.info(f"Started update_table of freesurfer processing for user '{user_id}', file name {user.file_name}, PID: {process.pid}, with command {PYTHON_EXECUTABLE} -m brain_dashboard.scripts.free_surfer --file-name {user.file_name} --update-table.")
                            flash(f"Started update_table of freesurfer processing for user '{user_id}', file name {user.file_name}.",
                                  'success')
                        except Exception as e:
                            logger.error(f'Failed update_table run for user {user_id}: {str(e)}, Command used: {PYTHON_EXECUTABLE} -m brain_dashboard.scripts.freesurfer --file-name {user.file_name} --update-table')
                            flash(f'Failed update_table run for user {user_id}: {str(e)}', 'error')
                return redirect(url_for('.index'))
            elif action == 'update_db':
                # Run the folder watcher in one-shot mode to ingest new files
                try:
                    process = subprocess.Popen(
                        [
                            PYTHON_EXECUTABLE,  # Use the Python executable from the environment
                            '-m',
                            'brain_dashboard.scripts.watch_folder',
                            '--folder', str(DATA_DIR),
                            '--once'
                        ],
                        shell=False,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                    logger.info(f'Database updated from data folder, PID: {process.pid}, with command {PYTHON_EXECUTABLE} -m brain_dashboard.scripts.watch_folder --folder {DATA_DIR} --once')
                    flash('Database updated from data folder.', 'success')
                except Exception as e:
                    logger.error(f'Failed to update database: {str(e)}, with command {PYTHON_EXECUTABLE} -m brain_dashboard.scripts.watch_folder --folder {DATA_DIR} --once')
                    flash(f'Failed to update database: {str(e)}', 'error')
                return redirect(url_for('.index'))

        # Only show users with preprocessed status
        # Also show recent users for status visibility
        recent_users = User.query.order_by(User.user_id.desc()).all()

        # Merge recent_users with CSV characteristics by file_name
        # Build DataFrame from recent_users
        recent_df = pd.DataFrame([
            {
                'user_id': u.user_id,
                'file_name': u.file_name,
                'status': u.status,
            }
            for u in recent_users
        ])

        char_columns = []
        merged_rows = []
        display_columns = []
        column_specs = {}
        try:
            if os.path.exists(USERS_CHARACTERISTICS_CSV_PATH):
                csv_df = pd.read_csv(USERS_CHARACTERISTICS_CSV_PATH)
                if not csv_df.empty:
                    first_col = csv_df.columns[0]
                    if first_col != 'file_name':
                        csv_df = csv_df.rename(columns={first_col: 'file_name'})
                    # Dynamic characteristic columns are everything after file_name
                    char_columns = [c for c in csv_df.columns if c != 'file_name']
                    csv_df = csv_df.set_index('file_name')
                    if not recent_df.empty:
                        merged = recent_df.join(csv_df, on='file_name', how='left')
                        merged_rows = merged.to_dict(orient='records')
                        # Build display columns and column specs
                        display_columns = ['user_id', 'status'] + ['file_name'] + char_columns
                        # Infer types for characteristics columns
                        for col in display_columns:
                            if col in ['user_id', 'file_name']:
                                column_specs[col] = {"type": "text"}
                            elif col == 'status':
                                choices = sorted([v for v in merged[
                                    'status'].dropna().unique()]) if 'status' in merged.columns else []
                                column_specs[col] = {"type": "categorical", "choices": choices}
                            else:
                                series = merged[col] if col in merged.columns else pd.Series(dtype='object')
                                # Determine numeric columns
                                is_numeric = pd.api.types.is_numeric_dtype(series)
                                if is_numeric:
                                    clean = series.dropna()
                                    if not clean.empty:
                                        column_specs[col] = {
                                            "type": "numeric",
                                            "min": float(clean.min()),
                                            "max": float(clean.max())
                                        }
                                    else:
                                        column_specs[col] = {"type": "numeric"}
                                else:
                                    choices = sorted([str(v) for v in series.dropna().unique()])
                                    column_specs[col] = {"type": "categorical", "choices": choices}
        except Exception:
            # On any error, fall back to DB-only view
            merged_rows = recent_df.to_dict(orient='records') if not recent_df.empty else []
            display_columns = ['user_id', 'status', 'file_name']
            # Specs for fallback
            column_specs = {
                'user_id': {"type": "text"},
                'file_name': {"type": "text"},
                'status': {"type": "categorical", "choices": sorted(
                    [v for v in recent_df['status'].dropna().unique()]) if not recent_df.empty else []}
            }

        users_for_freesurfer = User.query.filter(
            or_(
                User.status == USER_STATUS_PREPROCESSED,
                User.status == USER_STATUS_FREESURFER_FAILED
            )
        ).all()
        users_for_update_table = User.query.filter(
            or_(
                User.status == USER_STATUS_FREESURFER_COMPLETED,
                User.status == USER_STATUS_UPDATE_TABLE_FAILED
            )
        ).all()

        return self.render(
            'run_processor.html',
            users_for_freesurfer=users_for_freesurfer,
            users_for_update_table=users_for_update_table,
            recent_users=recent_users,
            char_columns=char_columns,
            merged_rows=merged_rows,
            display_columns=display_columns,
            column_specs=column_specs,
        )


admin.add_view(RunProcessorView(name='Run Processor', endpoint='run_processor', category=None))


@FLASK_APP.route('/admin/download_result')
def download_result():
    file_path = request.args.get('path')
    if not file_path or not os.path.isfile(file_path):
        abort(404)
    # Optionally, add security checks here to restrict allowed directories
    return send_file(file_path, as_attachment=True)



def main():
    with FLASK_APP.app_context():
        db.create_all()
    FLASK_APP.run(host='127.0.0.1', port=PORT_ADMIN, debug=True)

if __name__ == '__main__':
    main()