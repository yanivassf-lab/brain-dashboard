#!/usr/bin/env python3

import panel as pn

from brain_dashboard.app import BrainAnalysisApp
from brain_dashboard.settings import PORT_APP

# Settings
pn.extension('plotly', 'tabulator', notifications=True)
pn.config.theme = 'default'

def create_app():
    """Create the application"""
    app = BrainAnalysisApp()
    return app.create_layout()

def main():
    pn.serve(
        create_app,
        port=PORT_APP,
        title="Brain Analysis System",
        show=True,
        autoreload=True
    )

if __name__ == '__main__':
    main()

"""
Instructions to run the app:
4. Run the script using Python:
   python run_app.py
5. Open your web browser and go to http://localhost:5006 to access the app.


"""