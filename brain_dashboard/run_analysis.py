import time

import numpy as np
import pandas as pd
import panel as pn
from scipy import stats
from statsmodels.stats.multitest import multipletests

from brain_dashboard.settings import PEARSON_TEST,SPEARMAN_TEST, ANOVA_TEST, T_TEST, logger

# Panel definition
pn.extension('plotly', 'tabulator')

NOT_STARTED = 'not_started'
RUNNING = 'running'
FAILED = 'failed'
COMPLETED = 'completed'

WAIT = 20


def check_continues_variable(variable):
    """Check if the explanatory variable is continuous"""
    is_continuous = False
    n_unique = variable.nunique()
    n = len(variable)
    x = variable.dropna().to_numpy()
    dtype = x.dtype

    if np.issubdtype(dtype, np.floating) or np.issubdtype(dtype, np.integer):
        is_continuous = True

    return is_continuous, n_unique


def is_valid_test(x: pd.Series, test_name: str) -> bool:
    """
    Check if a statistical test is valid for the given explanatory variable array.
    x: numpy array of explanatory variable values
    test_name: str, one of ['pearson', 'spearman', 'anova', 't-test']
    Returns: True if valid, False otherwise
    """

    is_continuous, n_unique = check_continues_variable(x)

    test_name = test_name.lower()

    if test_name == PEARSON_TEST:
        return is_continuous
    elif test_name == SPEARMAN_TEST:
        return is_continuous
    elif test_name == T_TEST:
        return n_unique == 2
    elif test_name == ANOVA_TEST:
        return n_unique >= 3 and not is_continuous
    else:
        return False


def perform_statistical_analysis(selected_users, selected_feature, apply_fdr, users_df,
                                 brain_volumes_df, statistical_test):
    """Perform statistical tests"""
    logger.info(f"=== Starting statistical analysis ===")
    logger.info(f"Users: {len(selected_users)}")
    logger.info(f"Feature: '{selected_feature}' (type: {type(selected_feature)})")
    logger.info(f"Apply FDR: {apply_fdr}")
    logger.info(f"self.selected_feature: '{selected_feature}' (type: {type(selected_feature)})")
    logger.info(f"Statistical test: {statistical_test} (type: {type(statistical_test)})")

    # Simulate a long-running computation
    logger.info("Starting computation...")
    time.sleep(WAIT)
    logger.info("Computation finished")

    try:
        results = {}

        # Check if selected_feature is empty
        if not selected_feature or selected_feature == "":
            logger.error(f"Selected feature is empty! Value: '{selected_feature}'")
            raise ValueError("Selected feature cannot be empty")

        # Check if selected_users is empty
        if not selected_users or len(selected_users) == 0:
            logger.error("No users selected!")
            raise ValueError("No users selected")

        # Selected user data
        logger.info(f"Accessing data for {len(selected_users)} users and feature: '{selected_feature}'")
        logger.info(f"Available features in users_df: {list(users_df.columns)}")
        logger.info(f"Selected users: {selected_users}")
        values_features_selected_user = users_df.loc[selected_users, selected_feature]

        is_continuous, n_unique = check_continues_variable(values_features_selected_user)

        for brain_region in brain_volumes_df.columns:
            # brain_volumes = brain_volumes_df.loc[selected_users, brain_region]
            brain_volumes = brain_volumes_df.loc[selected_users, brain_region]
            # print(f"Analyzing brain region: {brain_region}")
            # print(brain_region, brain_volumes.shape, selected_user_data.shape)

            # TODO: Remove it in production
            brain_volumes = brain_volumes + np.random.normal(0, 100, size=brain_volumes.shape)

            if is_continuous:
                if statistical_test == PEARSON_TEST:
                    r, p = stats.pearsonr(values_features_selected_user, brain_volumes)
                    results[brain_region] = {'r': r, 'p': p}
                elif statistical_test == SPEARMAN_TEST:
                    r, p = stats.spearmanr(values_features_selected_user, brain_volumes)
                    results[brain_region] = {'r': r, 'p': p}
            else:
                # Tests for discrete features
                groups = []
                for value in values_features_selected_user.unique():
                    group_data = brain_volumes[values_features_selected_user == value]
                    if len(group_data) > 0:
                        groups.append(group_data)

                if len(groups) == 2 and statistical_test == T_TEST:
                    t, p = stats.ttest_ind(groups[0], groups[1])
                    results[brain_region] = {'t': t, 'p': p}
                elif len(groups) > 2 and statistical_test == ANOVA_TEST:
                    f, p = stats.f_oneway(*groups)
                    results[brain_region] = {'f': f, 'p': p}
                else:
                    results[brain_region] = {'p': 1.0}  # No suitable test

        # FDR correction if requested
        if apply_fdr:
            logger.info("Applying FDR correction...")
            p_values = [res.get('p', 1.0) for res in results.values()]
            rejected, p_adjusted, _, _ = multipletests(p_values, method='fdr_bh')

            for i, (region, res) in enumerate(results.items()):
                res['p_adjusted'] = p_adjusted[i]
                res['significant'] = rejected[i]
            logger.info(f"FDR correction applied. Significant regions: {sum(rejected)}")

        logger.info(f"Analysis completed successfully. Results for {len(results)} brain regions")
        logger.info("Results summary:")
        for region, res in results.items():
            logger.info(f"  {region}: p={res.get('p', 'N/A'):.4f}, significant={res.get('significant', False)}")

        return results
    except Exception as e:
        logger.error(f"Analysis failed with error: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        pn.state.notifications.error(f'Analysis failed: {str(e)}', duration=5000)
        return None
