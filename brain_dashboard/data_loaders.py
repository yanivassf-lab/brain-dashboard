# data_loaders.py
import os
import sqlite3

import pandas as pd

from brain_dashboard.scripts.admin_app import USER_STATUS_UPDATE_TABLE_COMPLETED
from brain_dashboard.settings import DB_PATH, USERS_CHARACTERISTICS_CSV_PATH, ASEG_DF, APARC_LH_DF, \
    APARC_RH_DF, logger


def load_brain_volumes_data():
    """
    Loads brain volumes from FreeSurfer.
    Returns combined DataFrame even if some files are empty.
    """

    def safe_read(file_path, index_col):
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return pd.read_csv(file_path).set_index(index_col)
        else:
            # Return empty DataFrame with file_name as index
            return pd.DataFrame(columns=['file_name']).set_index('file_name')

    daseg_df = safe_read(ASEG_DF, 'Measure:volume')
    aparc_lh_df = safe_read(APARC_LH_DF, 'lh.aparc.area')
    aparc_rh_df = safe_read(APARC_RH_DF, 'rh.aparc.area')

    df = pd.concat([daseg_df, aparc_lh_df, aparc_rh_df], axis=1)
    return df.loc[:, ~df.columns.duplicated()]  # keep first occurrence



def load_users_data():
    """Load user data from SQLite database and enrich with dynamic characteristics from CSV."""
    # Load users from DB
    conn = sqlite3.connect(DB_PATH)
    users_df = pd.read_sql_query(f"SELECT * FROM users WHERE status='{USER_STATUS_UPDATE_TABLE_COMPLETED}'", conn,
                                 index_col='user_id')
    conn.close()

    # Try to load characteristics from CSV, first column is file_name
    try:
        characteristics_df = pd.read_csv(USERS_CHARACTERISTICS_CSV_PATH)
        if characteristics_df.empty:
            return users_df
        first_col = characteristics_df.columns[0]
        # Ensure first column is called 'file_name' for clarity
        if first_col != 'file_name':
            characteristics_df = characteristics_df.rename(columns={first_col: 'file_name'})
        characteristics_df = characteristics_df.set_index('file_name')
        if 'file_name' in users_df.columns:
            merged = users_df.join(
                characteristics_df,
                on='file_name',
                how='left',
                rsuffix='_char'
            )
            return merged
    except Exception as e:
        logger.warning(f"Could not load characteristics from CSV at {USERS_CHARACTERISTICS_CSV_PATH}: {e}")
    # If Excel not available or no matchable columns, return DB users only
    return users_df
