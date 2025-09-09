# app.py
import asyncio
import os
import pickle
import re
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime

import numpy as np
import panel as pn
import param
import plotly.colors as pc
import plotly.graph_objects as go

from brain_dashboard.atlas_utils import AtlasUtils
from brain_dashboard.brain_visualization import BrainVisualization
from brain_dashboard.data_loaders import load_users_data, load_brain_volumes_data
from brain_dashboard.run_analysis import perform_statistical_analysis, is_valid_test
from brain_dashboard.scripts.admin_app import db, AnalysisResult
from brain_dashboard.settings import (
    ANALYSES_DIR,
    NON_FILTER_COLUMNS,
    FLASK_APP,
    PEARSON_TEST,
    STATISTICAL_TESTS,
    logger, SPEARMAN_TEST, T_TEST, ANOVA_TEST
)

# Panel definition
pn.extension('plotly', 'tabulator')

NOT_STARTED = 'not_started'
RUNNING = 'running'
FAILED = 'failed'
COMPLETED = 'completed'

EMPTY_GRAPH_MESSEGE = 'Waiting for analysis...'
FAILED_GRAPH_MESSEGE = 'Analysis failed. Check settings.'
RUNNING_GRAPH_MESSEGE = 'Analysis is running...'
SELECT_REGION_MESSEGE = 'Select an analysis and a brain region to display data'

WAIT = 20
SIDEBAR_WIDTH = 600
SIDEBAR_FIELD_WIDTH = 70
SIDEBAR_SLIDER_WIDTH = 100
SIDEBAR_HEIGHT = None
BRAIN_WIDTH = 1200
BRAIN_HEIGHT = 800
PLOT_WIDTH = 1200
PLOT_HEIGHT = 400
CENTER_WIDTH = None
CENTER_HEIGHT = None


class BrainAnalysisApp(param.Parameterized):
    """Brain Analysis Application"""

    # Application parameters
    selected_name = param.String(default='', doc="Selected analysis name")
    selected_users = param.List(default=[], doc="Selected users")
    selected_feature = param.Selector(default="", doc="Selected feature")
    selected_statistical = param.Selector(default="", doc="Statistical test")
    apply_fdr = param.Boolean(default=True, doc="FDR correction")
    display_metric = param.Selector(
        default="p-value",
        objects=["p-value", "r-value", "t-value", "f-value"],
        doc="Metric to display"
    )
    selected_brain_region = param.Selector(default="", doc="Selected brain region")
    current_analysis_name = param.String(default="", doc="Current analysis name")
    view_type = param.Selector(
        default="3D Interactive",
        objects=["3D Interactive", "Surface Views", "Glass Brain", "2D Glass Brain"],
        doc="Type of brain view"
    )

    def __init__(self, **params):
        super().__init__(**params)

        # Initialize brain visualization
        self.brain_viz = BrainVisualization()

        # Load data
        self.users_df = load_users_data()
        self.filter_columns = self.get_filter_columns()
        self.param.selected_feature.objects = self.filter_columns

        self.brain_volumes_df = load_brain_volumes_data()
        logger.debug(f"Brain volumes columns: {self.brain_volumes_df.columns.tolist()}")
        self.param.selected_statistical.objects = STATISTICAL_TESTS
        self.param.selected_brain_region.objects = list(self.brain_volumes_df.columns)

        # Analysis results
        self.analysis_results = None
        self.analysis_status = NOT_STARTED  # Analysis status
        self.analyses_history = []

        # Create interface
        self.setup_ui()

    def get_filter_columns(self):
        filter_columns = self.users_df.columns.tolist()
        for col in NON_FILTER_COLUMNS:
            if col in filter_columns:
                filter_columns.remove(col)
        return filter_columns

    def setup_ui(self):
        """Set up user interface"""
        # User filters
        self.user_filter_widgets = self.create_user_filters()
        # User selection with search and checkboxes
        self.user_selector = pn.widgets.MultiChoice(
            name='Select users',
            options=list(self.users_df.index),
            search_option_limit=300,
            width=SIDEBAR_WIDTH - SIDEBAR_FIELD_WIDTH
        )

        # Run analysis button with status indicator
        self.run_button = pn.widgets.Button(
            name='▶ Execute Analysis',
            button_type='danger',
            width=SIDEBAR_WIDTH - SIDEBAR_FIELD_WIDTH,
            height=50,
            css_classes=['bold-button']
        )
        self.run_button.on_click(lambda event: asyncio.create_task(self.run_analysis(event)))

        # Status indicator next to the button
        self.status_indicator = pn.pane.Markdown(
            "",
            width=70,
            height=70,
            margin=(0, 10, 0, 0)
        )

        self.name_selector = pn.widgets.TextInput(
            name='Analysis Name',
            placeholder='Enter analysis name (only a-zA-Z0-9 allowed)',
            value='',
            width=SIDEBAR_WIDTH - SIDEBAR_FIELD_WIDTH
        )
        self.name_selector.param.watch(self.on_name_change, 'value')

        self.statistical_selector = pn.widgets.Select(
            name="Select Statistical Test",
            options=[""] + STATISTICAL_TESTS,
            value='',
            width=SIDEBAR_WIDTH - SIDEBAR_FIELD_WIDTH
        )
        self.statistical_selector.param.watch(self.on_statistical_change, 'value')

        # Feature selector widget
        self.feature_selector = pn.widgets.Select(
            name='Select Feature',
            options=[''] + self.filter_columns,
            value='',
            width=SIDEBAR_WIDTH - SIDEBAR_FIELD_WIDTH
        )
        self.feature_selector.param.watch(self.on_feature_change, 'value')

        self.analyses_history = self.load_analyses_names_history()

        # Previous analyses history
        options_dict = {"Select Analysis": ""}
        options_dict.update(dict(zip(self.analyses_history[0], self.analyses_history[1])))

        self.history_selector = pn.widgets.Select(
            name='Previous analyses',
            options=options_dict,
            width=SIDEBAR_WIDTH - SIDEBAR_FIELD_WIDTH
        )
        self.history_selector.param.watch(self.load_previous_analysis, 'value')

        # Brain display container (dynamic)
        self.brain_display = pn.Column(
            self.create_brain_view(),
            width=BRAIN_WIDTH,
            height=BRAIN_HEIGHT
        )

        # Data plot
        self.data_plot = pn.pane.Plotly(
            self.create_empty_plot(message=EMPTY_GRAPH_MESSEGE),
            width=PLOT_WIDTH,
            height=PLOT_HEIGHT
        )

    def get_metrics_for_test(self, test_name):
        """Return valid display metrics depending on the statistical test."""
        if test_name in [PEARSON_TEST, SPEARMAN_TEST]:
            return ["p-value", "r-value"]
        elif test_name == T_TEST:
            return ["p-value", "t-value"]
        elif test_name == ANOVA_TEST:
            return ["p-value", "f-value"]
        return ["p-value"]  # default fallback

    def load_analyses_names_history(self):
        if not os.path.exists(ANALYSES_DIR):
            os.makedirs(ANALYSES_DIR)
        analyses_names = []
        analysis_file_names = []
        """Load previous analysis names with status"""

        # Full paths to files in the directory
        full_paths = [os.path.join(ANALYSES_DIR, f) for f in os.listdir(ANALYSES_DIR) if f.endswith('.pkl')]
        # Sort by creation time (os.path.getctime)
        sorted_files = sorted(full_paths, key=os.path.getctime, reverse=True)
        # If you only want the filenames (without full path)
        sorted_filenames = [os.path.basename(f) for f in sorted_files]
        for analysis_file in sorted_filenames:
            try:
                with open(os.path.join(ANALYSES_DIR, analysis_file), 'rb') as f:
                    analysis = pickle.load(f)
                    # Get status and add to name
                    status = analysis.get('status_run', NOT_STARTED)
                    name = analysis.get('name', 'Unknown')

                    # Add status indicator to name
                    if status == COMPLETED:
                        status_indicator = "✓"
                    elif status == RUNNING:
                        status_indicator = "▶"
                    elif status == FAILED:
                        status_indicator = "✗"
                    else:
                        status_indicator = "○"

                    analyses_names.append(f"{status_indicator} {name}")
                    analysis_file_names.append(analysis_file)
            except Exception as e:
                print(f"Error loading analysis file {analysis_file}: {e}")
                continue
        return analyses_names, analysis_file_names

    def create_user_filters(self):
        """Create user filters"""
        filters = {}
        for col in self.filter_columns:
            if self.users_df[col].dtype in ['int64', 'float64']:
                min_val = float(self.users_df[col].min())
                max_val = float(self.users_df[col].max())
                filters[col] = pn.widgets.RangeSlider(
                    name=f'{col} range',
                    start=min_val,
                    end=max_val,
                    value=(min_val, max_val),
                    step=0.1 if self.users_df[col].dtype == 'float64' else 1,
                    width=SIDEBAR_WIDTH - SIDEBAR_SLIDER_WIDTH
                )
            else:
                unique_values = list(self.users_df[col].dropna().unique())
                filters[col] = pn.widgets.MultiSelect(
                    name=f'{col} values',
                    options=unique_values,
                    value=unique_values,
                    size=min(5, len(unique_values)),
                    width=SIDEBAR_WIDTH - SIDEBAR_SLIDER_WIDTH
                )

        # Add callback to update users
        for widget in filters.values():
            widget.param.watch(self.update_filtered_users, 'value')

        return filters

    def update_filtered_users(self, event):
        logger.info('Updating filtered users...')
        logger.info(self.users_df.index.tolist())
        """Update filtered user list"""
        filtered_users = self.users_df.index.tolist()

        for col, widget in self.user_filter_widgets.items():
            if isinstance(widget, pn.widgets.RangeSlider):
                min_val, max_val = widget.value
                filtered_users = [
                    user for user in filtered_users
                    if min_val <= self.users_df.loc[user, col] <= max_val
                ]
            else:  # MultiSelect
                selected_values = widget.value
                filtered_users = [
                    user for user in filtered_users
                    if self.users_df.loc[user, col] in selected_values
                ]
        self.user_selector.options = filtered_users

    async def run_analysis(self, event):
        """Run statistical analysis"""
        logger.info("=== Starting new analysis ===")

        if not self.user_selector.value:
            logger.warning("No users selected for analysis")
            pn.state.notifications.error('Please select users for analysis', duration=3000)
            return

        # Check if feature is selected
        analysis_feature = self.feature_selector.value
        analysis_statistical = self.statistical_selector.value
        analysis_users = self.user_selector.value
        logger.info(f"Selected analysis name: '{self.selected_name}' (type: {type(self.selected_name)})")
        logger.info(f"Selected feature value: '{analysis_feature}' (type: {type(analysis_feature)})")
        logger.info(f"Selected feature value: '{analysis_statistical}' (type: {type(analysis_statistical)})")
        logger.info(f"Selected users: {len(analysis_users)} users")

        values_features_selected_user = self.users_df.loc[analysis_users, analysis_feature]
        if not is_valid_test(values_features_selected_user, analysis_statistical):
            logger.warning(
                f"Selected statistical test '{analysis_statistical}' is not valid for feature '{analysis_feature}'")
            pn.state.notifications.error(
                f"Statistical test '{analysis_statistical}' is not valid for feature '{analysis_feature}'",
                duration=5000
            )
            return
        if not self.selected_name or self.selected_name == "" or self.selected_name is None:
            logger.warning("No analysis name provided")
            pn.state.notifications.error('Please provide a name for the analysis', duration=3000)
            return

        if not analysis_feature or analysis_feature == "" or analysis_feature is None:
            logger.warning("No feature selected for analysis")
            pn.state.notifications.error('Please select a feature for analysis', duration=3000)
            return

        if not analysis_statistical or analysis_statistical == "" or analysis_statistical is None:
            logger.warning("No statistical test selected for analysis")
            pn.state.notifications.error('Please select a statistical test for analysis', duration=3000)
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        timestamp_filename = timestamp.replace('-', '').replace(':', '').replace(' ', '_')
        analysis_name = f"{self.selected_name} - {analysis_feature} - {analysis_statistical} - {timestamp}"
        filename = f"{self.selected_name}-{analysis_feature}-{analysis_statistical}-{timestamp_filename}.pkl"
        logger.info(f"Analysis name: {analysis_name}")
        logger.info(f"Filename: {filename}")

        # Save initial results with RUNNING status
        self.save_analysis_to_history(analysis_name, filename, timestamp, analysis_users, analysis_feature,
                                      analysis_statistical)
        self.analysis_status = RUNNING
        self.current_analysis_name = analysis_name

        # Show prominent running notification
        pn.state.notifications.info("🚀 Analysis started! Please wait...", duration=5000)

        # Update status indicator to show running
        self.update_status_indicator("▶", "Running...")

        # Clear the running indicator after analysis completes
        self.running_indicator_task = asyncio.create_task(self.clear_running_indicator_after_delay(3))

        # Reset UI selections immediately when analysis starts
        self.name_selector.value = ''
        self.statistical_selector.value = ''
        self.user_selector.value = []
        self.feature_selector.value = ""
        # self.selected_brain_region = ""

        # Start a background task to update the UI while analysis is running
        # update_task = asyncio.create_task(self.update_ui_during_analysis())

        # Run the analysis in a separate thread to avoid blocking the UI
        loop = asyncio.get_event_loop()

        with ProcessPoolExecutor() as executor:
            results = await loop.run_in_executor(
                executor,
                perform_statistical_analysis,
                analysis_users,
                analysis_feature,
                self.apply_fdr,
                self.users_df,
                self.brain_volumes_df,
                analysis_statistical
            )

        # Cancel the update task when analysis is done
        # update_task.cancel()

        # Cancel the running indicator task and clear it immediately
        if hasattr(self, 'running_indicator_task'):
            self.running_indicator_task.cancel()
        self.update_status_indicator("", "")

        if results:  # Check if analysis completed without immediate failure
            logger.info("=== Analysis completed successfully ===")
            self.save_analysis_results(filename, results, COMPLETED, analysis_name, analysis_users, analysis_feature,
                                       analysis_statistical, timestamp)
            pn.state.notifications.success("✅ Analysis completed successfully!", duration=3000)
        else:  # Analysis failed, status already set to FAILED in perform_statistical_analysis
            logger.error("=== Analysis failed ===")
            self.save_analysis_results(filename, {}, FAILED, analysis_name, analysis_users, analysis_feature,
                                       analysis_statistical, timestamp)  # Save empty results with FAILED status
            pn.state.notifications.error("❌ Analysis failed. Check settings.", duration=5000)

    def update_pickle_result_file(self, selected_analysis, results, status, filepath):
        selected_analysis['results'] = results
        selected_analysis['status_run'] = status
        selected_analysis['timestamp_ended'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(filepath, 'wb') as f:
            pickle.dump(selected_analysis, f)
        logger.info(f"Successfully saved analysis results to {filepath}")

    def update_txt_result_file(self, filepath, content):
        with open(filepath, 'w') as f:
            for k, v in content.items():
                f.write(f"{k}: {v}\n")
        logger.info(f"Successfully saved analysis results to {filepath}")

    def update_status_history_analysis_list(self, filename, selected_analysis, status):
        # Update the status in the history list
        if filename in self.analyses_history[1]:
            idx = self.analyses_history[1].index(filename)
            name = selected_analysis.get('name', 'Unknown')

            # Update status indicator
            if status == COMPLETED:
                status_indicator = "✓"
            elif status == RUNNING:
                status_indicator = "▶"
            elif status == FAILED:
                status_indicator = "✗"
            else:
                status_indicator = "○"

            self.analyses_history[0][idx] = f"{status_indicator} {name}"

            # Update the options dictionary with "Select Analysis" option
            options_dict = {"Select Analysis": ""}
            options_dict.update(dict(zip(
                self.analyses_history[0],
                self.analyses_history[1]
            )))
            self.history_selector.options = options_dict

    def update_status_in_db(self, analysis_name, analysis_users, analysis_feature, analysis_statistical,
                            results_txt_filepath, status, timestamp):
        try:
            with FLASK_APP.app_context():
                selected_user_ids = ','.join(str(uid) for uid in analysis_users)
                analysis_result = AnalysisResult(
                    analysis_name=analysis_name,
                    selected_users=selected_user_ids,
                    selected_feature=analysis_feature,
                    selected_statistical=analysis_statistical,
                    results=results_txt_filepath,
                    status=status,
                    timestamp=timestamp
                )
                db.session.add(analysis_result)
                db.session.commit()
        except Exception as e:
            logger.error(f"Failed to update AnalysisResult in DB: {e}")

    def save_analysis_results(self, filename, results, status, analysis_name, analysis_users, analysis_feature,
                              analysis_statistical, timestamp):
        """Save analysis results to file"""
        logger.info(f"Saving analysis results to {filename} with status: {status}")
        result_pkl_filepath = os.path.join(ANALYSES_DIR, filename)
        results_txt_filepath = result_pkl_filepath.replace('.pkl', '.txt')
        try:
            with open(result_pkl_filepath, 'rb') as f:
                selected_analysis = pickle.load(f)
        except FileNotFoundError:
            # This should ideally not happen if save_analysis_to_history is called first
            logger.warning(f"File {filename} not found when trying to update results. Creating new.")
            selected_analysis = {}  # Create an empty dict if file not found
            pn.state.notifications.warning(f"File {filename} not found when trying to update results. Creating new.",
                                           duration=3000)

        self.update_pickle_result_file(selected_analysis, results, status, result_pkl_filepath)
        self.update_txt_result_file(results_txt_filepath, selected_analysis)
        self.update_status_history_analysis_list(filename, selected_analysis, status)
        self.update_status_in_db(analysis_name, analysis_users, analysis_feature, analysis_statistical,
                                 results_txt_filepath, status, timestamp)

    def create_brain_plot(self):
        """Create a real brain plot"""
        if self.analysis_results is None:
            if self.analysis_status == RUNNING:
                return self.create_empty_brain_plot(message=RUNNING_GRAPH_MESSEGE)
            return self.create_empty_brain_plot(message=EMPTY_GRAPH_MESSEGE)

        # Prepare data for mapping
        region_values = {}
        for region, results in self.analysis_results.items():
            if self.display_metric == 'p-value':
                if self.apply_fdr:
                    value = -np.log10(results.get('p_adjusted', 1))
                else:
                    value = -np.log10(results.get('p', 1))
            elif self.display_metric == 'r-value':
                value = results.get('r', 0)
            elif self.display_metric == 't-value':
                value = results.get('t', 0)
            elif self.display_metric == 'f-value':
                value = results.get('f', 0)

            region_values[region] = value

        # Create interactive 3D brain plot
        fig = self.brain_viz.create_3d_brain_plotly(
            region_values,
            colorscale='RdBu_r',
            title=f'{self.display_metric} - {self.selected_feature}'
        )
        fig.update_layout(
            scene=dict(
                xaxis_title='X',
                yaxis_title='Y',
                zaxis_title='Z'
            ),
            width=BRAIN_WIDTH,
            height=BRAIN_HEIGHT,
        )
        return fig

    def _compute_region_values(self):
        """Compute scalar value per region according to display_metric and FDR setting."""
        if not self.analysis_results:
            return {}

        region_values = {}
        for region, results in self.analysis_results.items():
            if self.display_metric == 'p-value':
                if self.apply_fdr:
                    value = -np.log10(results.get('p_adjusted', 1))
                else:
                    value = -np.log10(results.get('p', 1))
            elif self.display_metric == 'r-value':
                value = results.get('r', 0)
            elif self.display_metric == 'f-value':
                value = results.get('f', 0)
            else:
                value = results.get('t', 0)
            region_values[region] = value
        return region_values

    def create_brain_view(self):
        """Create the brain view pane according to view_type and current state."""
        # When no results yet, show appropriate placeholder as Plotly
        if self.analysis_results is None:
            message = RUNNING_GRAPH_MESSEGE if self.analysis_status == RUNNING else EMPTY_GRAPH_MESSEGE
            return pn.pane.Plotly(
                self.create_empty_brain_plot(message=message),
                width=BRAIN_WIDTH,
                height=BRAIN_HEIGHT
            )

        region_values = self._compute_region_values()

        if self.view_type == "3D Interactive":
            return pn.pane.Plotly(
                self.create_brain_plot(),
                width=BRAIN_WIDTH,
                height=BRAIN_HEIGHT
            )

        if self.view_type == "Surface Views":
            surface_fig = self.brain_viz.create_surface_brain_nilearn(
                region_values,
                views=['lateral', 'medial', 'ventral', 'dorsal'],
                hemisphere='both',
                cmap='RdBu_r',
                title=f'{self.display_metric} - {self.selected_feature}'
            )
            return pn.pane.Matplotlib(surface_fig, width=1000, height=700, dpi=100)

        if self.view_type == "Glass Brain" or self.view_type == "2D Glass Brain":
            coords = []
            values = []
            names = []
            for region, value in region_values.items():
                coordinates = AtlasUtils.get_coordinates_for_region(region)
                if coordinates is not None:
                    coords.append(coordinates)
                    values.append(value)
                    names.append(region)
            if coords:
                if self.view_type == "Glass Brain":
                    fig = self.brain_viz.create_glass_brain(
                        np.array(coords),
                        np.array(values),
                        title=f'{self.display_metric} - {self.selected_feature}',
                        region_names=names
                    )
                    return pn.pane.Plotly(
                        fig,
                        width=BRAIN_WIDTH,
                        height=BRAIN_HEIGHT
                    )
                elif self.view_type == "2D Glass Brain":
                    fig = self.brain_viz.create_2d_glass_brain(
                        np.array(coords),
                        np.array(values),
                        title=f'{self.display_metric} - {self.selected_feature}'
                    )
                    return pn.pane.Matplotlib(fig, width=1000, height=700)
            # Fallback when no coordinates are available
            return pn.pane.Plotly(
                self.create_empty_brain_plot(message='No coordinates for current regions'),
                width=BRAIN_WIDTH,
                height=BRAIN_HEIGHT
            )
        # Default
        return pn.pane.Plotly(
            self.create_brain_plot(),
            width=BRAIN_WIDTH,
            height=BRAIN_HEIGHT
        )

    def create_empty_brain_plot(self, message):
        """Create a brain plot showing analysis is running"""
        fig = go.Figure()
        fig.add_trace(go.Scatter3d(
            x=[0], y=[0], z=[0],
            mode='markers',
            marker=dict(size=1, color='orange')
        ))
        fig.update_layout(
            title=message,
            scene=dict(
                xaxis_title='X',
                yaxis_title='Y',
                zaxis_title='Z'
            ),
            width=BRAIN_WIDTH,
            height=BRAIN_HEIGHT,
        )
        return fig

    def create_data_plot(self):
        """Create a data plot for the selected brain region"""
        if not self.selected_brain_region or not self.selected_users:
            return self.create_empty_plot(SELECT_REGION_MESSEGE)

        # If analysis is running, show running message
        if self.analysis_status == RUNNING:
            return self.create_empty_plot(RUNNING_GRAPH_MESSEGE)
        if self.analysis_status == FAILED:
            return self.create_empty_plot(FAILED_GRAPH_MESSEGE)

        # Data
        feature_data = self.users_df.loc[self.selected_users, self.selected_feature]
        brain_data = self.brain_volumes_df.loc[self.selected_users, self.selected_brain_region]

        fig = go.Figure()

        if feature_data.dtype in ['int64', 'float64']:
            # Scatter plot for continuous data
            fig.add_trace(go.Scatter(
                x=feature_data,
                y=brain_data,
                mode='markers',
                marker=dict(size=10, color='blue', opacity=0.6),
                name='Data'
            ))

            # Add regression line
            if self.analysis_results and self.selected_brain_region in self.analysis_results:
                r = self.analysis_results[self.selected_brain_region].get('r', 0)
                p = self.analysis_results[self.selected_brain_region].get('p', 1)

                # Calculate regression line
                z = np.polyfit(feature_data, brain_data, 1)
                p_line = np.poly1d(z)
                x_line = np.linspace(feature_data.min(), feature_data.max(), 100)

                fig.add_trace(go.Scatter(
                    x=x_line,
                    y=p_line(x_line),
                    mode='lines',
                    line=dict(color='red', width=2),
                    name=f'Regression (r={r:.3f}, p={p:.3f})'
                ))

            fig.update_layout(
                title=f'{self.selected_brain_region} vs {self.selected_feature}',
                xaxis_title=self.selected_feature,
                yaxis_title=f'Volume {self.selected_brain_region}',
                template='simple_white',
                font=dict(family='Segoe UI, Arial, sans-serif', size=16, color='#222'),
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(l=60, r=30, t=60, b=60)
            )
        else:
            # Box plot for discrete data
            unique_values = sorted(feature_data.unique())
            palette = pc.qualitative.Plotly
            for i, value in enumerate(unique_values):
                mask = feature_data == value
                color = palette[i % len(palette)]
                fig.add_trace(go.Box(
                    y=brain_data[mask],
                    name=str(value),
                    boxpoints='all',
                    jitter=0.3,
                    pointpos=-1.8,
                    marker_color=color,
                    line_color=color,
                    fillcolor=color,
                    opacity=0.6,
                    line=dict(width=2)
                ))

            fig.update_layout(
                title=f'{self.selected_brain_region} by {self.selected_feature}',
                xaxis_title=self.selected_feature,
                yaxis_title=f'Volume {self.selected_brain_region}',
                showlegend=True,
                template='simple_white',
                font=dict(family='Segoe UI, Arial, sans-serif', size=16, color='#222'),
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(l=60, r=30, t=60, b=60)
            )
        fig.update_layout(
            width=PLOT_WIDTH,
            height=PLOT_HEIGHT,
            template='simple_white',
            font=dict(family='Segoe UI, Arial, sans-serif', size=16, color='#222'),
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=60, r=30, t=60, b=60)
        )
        return fig

    def create_empty_plot(self, message):
        """Create an empty plot"""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=20, color="#1976D2", family='Segoe UI, Arial, sans-serif')
        )
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            width=PLOT_WIDTH,
            height=PLOT_HEIGHT,
            template='simple_white',
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=60, r=30, t=60, b=60)
        )
        return fig

    async def update_ui_during_analysis(self):
        """Update UI while analysis is running"""
        while self.analysis_status == RUNNING:
            # Update brain display to show "running" status
            self.update_brain_display()
            # Update data plot
            self.update_data_plot()
            # Wait 2 seconds before next update
            await asyncio.sleep(2)

    def update_status_indicator(self, icon, text):
        """Update the status indicator next to the run button"""
        if hasattr(self, 'status_indicator'):
            if icon and text:
                self.status_indicator.object = f"**{icon} {text}**"
            else:
                self.status_indicator.object = ""

    async def clear_running_indicator_after_delay(self, seconds):
        """Clear the running indicator after a delay"""
        await asyncio.sleep(seconds)
        self.update_status_indicator("", "")

    def on_feature_change(self, event):
        """Handle feature selection change"""
        logger.info(f"Feature change: '{event.old}' -> '{event.new}'")
        self.selected_feature = event.new

    def on_name_change(self, event):
        """Handle statistical selection change"""
        name = re.sub(r'[^a-zA-Z0-9]', '', event.new)
        logger.info(f"Name change: '{event.old}' -> '{name}'")
        self.selected_name = name

    def on_statistical_change(self, event):
        """Handle statistical selection change"""
        logger.info(f"Statistic change: '{event.old}' -> '{event.new}'")
        self.selected_statistical = event.new

        # Update display_metric options
        new_metrics = self.get_metrics_for_test(event.new)
        self.param.display_metric.objects = new_metrics
        if self.display_metric not in new_metrics:
            self.display_metric = new_metrics[0]

    def update_brain_display(self):
        """Update brain display"""
        self.brain_display.objects = [self.create_brain_view()]

    def update_data_plot(self):
        """Update data plot"""
        self.data_plot.object = self.create_data_plot()

    @param.depends('selected_brain_region', watch=True)
    def on_brain_region_change(self):
        """Handle brain region selection change"""
        self.update_data_plot()

    @param.depends('display_metric', 'apply_fdr', 'view_type', watch=True)
    def on_display_settings_change(self):
        """Handle display settings change"""
        if self.analysis_results:
            self.update_brain_display()

    def save_analysis_to_history(self, analysis_name, filename, timestamp, selected_users, selected_feature,
                                 analysis_statistical):
        """Save analysis to history"""

        analysis_data = {
            'name': analysis_name,
            'timestamp': timestamp,
            'selected_users': selected_users,
            'selected_feature': selected_feature,
            'selected_statistical': analysis_statistical,
            'apply_fdr': self.apply_fdr,
            'results': self.analysis_results,  # This will be None initially
            'status_run': RUNNING,
            'timestamp_ended': None  # Will be updated after analysis completion
        }

        # Check if the filename already exists in history to avoid duplicates in the options
        if filename not in self.analyses_history[1]:
            # Add new analysis with running status
            status_indicator = "▶"
            self.analyses_history[0].append(f"{status_indicator} {analysis_name}")
            self.analyses_history[1].append(filename)
        else:
            # If exists, update the name in the history selector to reflect potential restart of analysis
            idx = self.analyses_history[1].index(filename)
            status_indicator = "▶"
            self.analyses_history[0][idx] = f"{status_indicator} {analysis_name}"

        # Rebuild the options dictionary with "Select Analysis" option
        options_dict = {"Select Analysis": ""}
        options_dict.update(dict(zip(
            self.analyses_history[0],
            self.analyses_history[1]
        )))
        self.history_selector.options = options_dict

        # Save to file
        self.save_to_file(analysis_data, filename)

    def save_to_file(self, analysis_data, filename):
        """Save analysis to file"""
        if not os.path.exists(ANALYSES_DIR):
            os.makedirs(ANALYSES_DIR)

        with open(os.path.join(ANALYSES_DIR, filename), 'wb') as f:
            pickle.dump(analysis_data, f)

    def load_previous_analysis(self, event):
        """Load previous analysis"""
        if not event.new:
            return

        # Find the selected analysis
        selected_analysis_file = event.new  # event.new already contains the filename

        if selected_analysis_file:
            with open(os.path.join(ANALYSES_DIR, selected_analysis_file), 'rb') as f:
                selected_analysis = pickle.load(f)
            # Restore settings
            self.analysis_name = selected_analysis.get('name', '')  # Use .get for robustness
            self.current_analysis_name = selected_analysis.get('name', '')
            self.selected_users = selected_analysis.get('selected_users', [])
            self.selected_feature = selected_analysis.get('selected_feature', '')
            self.selected_statistical = selected_analysis.get('selected_statistical', PEARSON_TEST)
            self.apply_fdr = selected_analysis.get('apply_fdr', True)
            self.analysis_results = selected_analysis.get('results', None)
            self.analysis_status = selected_analysis.get('status_run', NOT_STARTED)

            # Update display_metric options based on loaded test
            new_metrics = self.get_metrics_for_test(self.selected_statistical)
            self.param.display_metric.objects = new_metrics
            if self.display_metric not in new_metrics:
                self.display_metric = new_metrics[0]

            # Update displays
            self.update_brain_display()
            self.update_data_plot()

            # Update the analysis title
            if hasattr(self, 'analysis_title'):
                self.analysis_title.object = f"# Current Analysis: {self.current_analysis_name}"

            # Update user selector options
            self.user_selector.options = list(self.users_df.index)

            pn.state.notifications.info(f'Loaded analysis: {self.analysis_name}', duration=3000)

    def create_layout(self):
        """Create the main layout"""
        # Left sidebar - user selection and filters
        filters_accordion = pn.Accordion(
            ('Filters', pn.Column(*self.user_filter_widgets.values())),
            active=[0],
            width=SIDEBAR_WIDTH - SIDEBAR_FIELD_WIDTH
        )

        left_panel = pn.Column(
            "# Run Analysis",
            self.name_selector,
            "## 1. User Selection:",
            self.user_selector,
            filters_accordion,
            pn.layout.Divider(),
            "## 2. Analysis Settings:",
            self.feature_selector,
            self.statistical_selector,
            pn.layout.Divider(),
            pn.Row(
                self.run_button,
            ),
            pn.Row(
                self.status_indicator,
                align='center'
            ),
            pn.layout.Divider(),
            pn.layout.Divider(),

            "# Analysis History",
            self.history_selector,
            pn.layout.Divider(),
            "# Display Settings",
            pn.Param(
                self,
                parameters=['view_type', 'apply_fdr', 'display_metric', 'selected_brain_region'],
                widgets={
                    'view_type': pn.widgets.RadioButtonGroup,
                    'apply_fdr': pn.widgets.Checkbox,
                    'display_metric': pn.widgets.RadioButtonGroup,
                    'selected_brain_region': pn.widgets.Select
                },
                width=SIDEBAR_WIDTH - SIDEBAR_FIELD_WIDTH
            ),
            width=SIDEBAR_WIDTH,
            height=SIDEBAR_HEIGHT,
            scroll=True
        )

        # Main center - displays
        # Create dynamic title that shows current analysis
        self.analysis_title = pn.pane.Markdown(
            f"# Current Analysis: {self.current_analysis_name}" if self.current_analysis_name else "# No Analysis Selected",
            width=CENTER_WIDTH
        )

        # Add a callback to update the title when current_analysis_name changes
        @param.depends('current_analysis_name', watch=True)
        def update_title():
            self.analysis_title.object = f"# Current Analysis: {self.current_analysis_name}" if self.current_analysis_name else "# No Analysis Selected"

        center_panel = pn.Column(
            self.analysis_title,
            pn.layout.Divider(),
            "# Brain Display",
            self.brain_display,
            pn.layout.Divider(),
            "# Data Plot",
            self.data_plot,
            width=CENTER_WIDTH,
            height=CENTER_HEIGHT,
            scroll=True
        )

        # Main template
        template = pn.template.BootstrapTemplate(
            title="Brain Data Analysis System",
            sidebar=[left_panel],
            main=[center_panel],
            sidebar_width=SIDEBAR_WIDTH
        )

        return template


def create_app():
    """Create the application"""
    app = BrainAnalysisApp()
    return app.create_layout()


# Run the application
if __name__ == "__main__":
    # Set theme
    pn.config.theme = 'light'

    # Create the application
    app = create_app()

    # Serve the application
    app.servable()

    # For local testing:
    # app.show(port=5006)
