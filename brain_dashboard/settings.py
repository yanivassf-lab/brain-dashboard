# settings.py

import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask

DEFAULT_ENV_PATH = Path(__file__).parent.parent / '.env'

ENV_FILE = os.getenv("DEFAULT_ENV_PATH", DEFAULT_ENV_PATH)

load_dotenv(dotenv_path=ENV_FILE)  # This loads variables from .env into os.environ

PORT_APP = int(os.environ.get('PORT_APP', 5006))
PORT_ADMIN = int(os.environ.get('PORT_ADMIN', 5000))

PYTHON_EXECUTABLE = Path(os.environ.get('PYTHON_EXECUTABLE', '/Users/user/Documents/pythonProject/ve-brain-dashboard/bin/python'))
PROJECT_ROOT = Path(os.environ.get('PROJECT_ROOT', '/Users/user/Documents/pythonProject/brain-dashboard/brain-dashboard'))
FREESURFER_HOME = Path(os.environ.get('FREESURFER_HOME', '/Applications/freesurfer/8.0.0/'))
SUBJECTS_DIR = Path(os.environ.get('SUBJECTS_DIR', '/Users/user/Documents/pythonProject/brain-dashboard/brain-dashboard/runs/freesurfer_output'))
FREESURFER_ENV_FILE = Path(os.environ.get('FREESURFER_ENV_FILE', '/Applications/freesurfer/8.0.0/FreeSurferEnv.sh'))
ASEG_DF = SUBJECTS_DIR / 'aseg_volumes.csv'
APARC_LH_DF = SUBJECTS_DIR / 'aparc_lh.csv'
APARC_RH_DF = SUBJECTS_DIR / 'aparc_rh.csv'

RUN_DIR = PROJECT_ROOT / 'runs'
DB_DIR = RUN_DIR / 'instance'
DB_PATH = DB_DIR / 'brain_data.sqlite3'
DB_NAME = 'sqlite:///' + str(DB_PATH)
ANALYSES_DIR = RUN_DIR / 'analyses'
DATA_DIR = Path(os.environ.get('DATA_DIR', '/Users/user/Documents/pythonProject/brain-dashboard/brain-dashboard/runs/data'))
LOGS_DIR = RUN_DIR / 'logs'
CONFIG_DIR = RUN_DIR / 'config'
CONFIG_PATH = CONFIG_DIR / 'config.json'


if not os.path.exists(DB_DIR): os.makedirs(DB_DIR)
if not os.path.exists(RUN_DIR): os.makedirs(RUN_DIR)
if not os.path.exists(RUN_DIR): os.makedirs(RUN_DIR)
if not os.path.exists(ANALYSES_DIR): os.makedirs(ANALYSES_DIR)
if not os.path.exists(LOGS_DIR): os.makedirs(LOGS_DIR)
if not os.path.exists(CONFIG_DIR): os.makedirs(CONFIG_DIR)

FLASK_SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key')
FLASK_APP = Flask(__name__)
FLASK_APP.config['SECRET_KEY'] = FLASK_SECRET_KEY
FLASK_APP.config['SQLALCHEMY_DATABASE_URI'] = DB_NAME
FLASK_APP.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Exposed dynamic constants (override-able via config.json)
NON_FILTER_COLUMNS = ["user_id", "file_name", "status"]
USERS_CHARACTERISTICS_CSV_PATH = str(CONFIG_DIR / 'users_features.csv')

# statistical_tests
PEARSON_TEST = "pearson"
SPEARMAN_TEST = "spearman"
ANOVA_TEST = "anova"
T_TEST = "t-test"
STATISTICAL_TESTS = [PEARSON_TEST, SPEARMAN_TEST, ANOVA_TEST, T_TEST]

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s",
    handlers=[
        logging.FileHandler(Path(LOGS_DIR) / 'brain_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("brain_analysis")
