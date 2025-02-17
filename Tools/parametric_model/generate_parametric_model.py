"""
 *
 * Copyright (c) 2021-2023 Manuel Yves Galliker
 *               2021-2023 Autonomous Systems Lab ETH Zurich
 * All rights reserved.
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 *
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in
 *    the documentation and/or other materials provided with the
 *    distribution.
 * 3. Neither the name Data Driven Dynamics nor the names of its contributors may be
 *    used to endorse or promote products derived from this software
 *    without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 * FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
 * COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
 * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
 * BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
 * OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
 * AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
 * ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 *
"""

__author__ = "Manuel Yves Galliker, Jaeyoung Lim, Julius Schlapbach"
__maintainer__ = "Manuel Yves Galliker, Julius Schlapbach"
__license__ = "BSD 3"

import os
import src.models as models
import src.models.extractor_models as extractors
from src.tools import DataHandler, string_to_bool
import argparse
import pandas as pd
import numpy as np


def start_model_estimation(
    config,
    log_path,
    data_selection="none",
    selection_var="none",
    plot=False,
    normalization=True,
    extraction=False,
):
    # Flag for enabling automatic data selection.
    data_handler = DataHandler(config, selection_var)
    data_handler.loadLogs(log_path)
    data_df = data_handler.get_dataframes()
    model_class = data_handler.config.model_class

    try:
        # This will call the model constructor directly from the model_class
        # in the yaml config (self-describing)
        # i.e if model_name is MultiRotorModel then it will call that __init__()
        model = getattr(models, model_class)(config, normalization=normalization)
    except AttributeError:
        error_str = (
            "Model '{0}' not found, is it added to models "
            "directory and models/__init__.py?".format(model_class)
        )
        raise AttributeError(error_str)

    # Interactive data selection
    if data_selection == "interactive":
        print("Interactive data selection enabled...")
        import vpselector

        model.load_dataframes(data_df)
        model.prepare_regression_matrices()
        model.compute_fisher_information()
        # Parse actuator topics, and remove the timestamp from it
        actuator_topics = data_handler.config_dict["data"]["required_ulog_topics"][
            "actuator_outputs"
        ]["dataframe_name"]
        actuator_topics.remove("timestamp")
        visual_dataframe_selector_config_dict = {
            "x_axis_col": "timestamp",
            "sub_plt1_data": ["q0", "q1", "q2", "q3"],
            "sub_plt2_data": actuator_topics,
            "sub_plt3_data": [],
        }

        if data_handler.estimate_forces == True:
            visual_dataframe_selector_config_dict["sub_plt3_data"].append(
                "fisher_information_force"
            )

        if data_handler.estimate_moments == True:
            visual_dataframe_selector_config_dict["sub_plt3_data"].append(
                "fisher_information_rot"
            )

        model.load_dataframes(
            vpselector.select_visual_data(
                model.data_df, visual_dataframe_selector_config_dict
            )
        )
        print("Interactive data selection completed.")

        model.prepare_regression_matrices()
        model.compute_fisher_information()

    # Setpoint based data selection
    elif data_selection == "setpoint":
        print("Setpoint based data selection enabled...")

        selector = selection_var.split("/")[1]

        zero_crossings = np.where(
            np.diff(np.sign(data_df[selector] + (data_df[selector] == 0)))
        )[0]

        if len(zero_crossings) == 0:
            raise AttributeError(
                "No selection variable activations have been found in the log."
            )

        if len(zero_crossings) % 2 != 0:
            raise AttributeError(
                "All selection variable activations have to start and end during the flight phase"
            )

        acc_df = pd.DataFrame()

        for i in range(0, len(zero_crossings), 2):
            start = zero_crossings[i]
            end = zero_crossings[i + 1]
            acc_df = pd.concat([acc_df, data_df.iloc[start:end]], ignore_index=True)

        model.load_dataframes(acc_df)
        print("Setpoint based data selection completed.")

        model.prepare_regression_matrices()
        model.compute_fisher_information()

    elif data_selection == "auto":  # Automatic data selection (WIP)
        print("Automatic data selection enabled...")
        from active_dataframe_selector.automatic_data_selector import (
            AutomaticDataSelector,
        )

        # The goal is to identify automatically the most relevant parts of a log.
        # Currently the draft is designed to choose the most informative 10% of the logs with regards to
        # force and moment parameters. This threshold is currently not validated at all and the percentage
        # can vary drastically from log to log.
        data_selector = AutomaticDataSelector(model.data_df)
        model.load_dataframes(data_selector.select_dataframes(10))
        print("Automatic data selection completed.")

        model.prepare_regression_matrices()
        model.compute_fisher_information()

    else:
        model.load_dataframes(data_df)
        model.prepare_regression_matrices()
        model.compute_fisher_information()

    model.estimate_model()

    if extraction:
        try:
            coefficient_list = model.get_model_coeffs()
            extractor = getattr(extractors, data_handler.config.extractor_class)(
                config=data_handler.config.extractor_config,
                model_config_file=config,
                coefficients=coefficient_list,
            )
        except AttributeError:
            error_str = (
                "Model '{0}' not found, is it added to models/extractors "
                "directory and models/extractors/__init__.py exists?".format(
                    model_class
                )
            )
            raise AttributeError(error_str)

        extractor.compute_px4_params()
        px4_params = extractor.get_px4_params()
        extractor.save_px4_params_to_yaml("model_results/")

    if plot:
        model.compute_residuals()
        model.plot_model_predicitons()

    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Estimate dynamics model from flight log."
    )
    parser.add_argument(
        "log_path",
        metavar="log_path",
        type=str,
        help="The path of the log to process relative to the project directory.",
    )
    parser.add_argument(
        "--config",
        metavar="config",
        type=str,
        default="configs/quadrotor_model.yaml",
        help="Configuration file path for pipeline configurations",
    )
    parser.add_argument(
        "--data_selection",
        metavar="data_selection",
        type=str,
        default="none",
        help="Data selection scheme none | interactive | setpoint | auto (Beta)",
    )
    parser.add_argument(
        "--selection_var",
        metavar="selection_var",
        type=str,
        default="",
        help="Setpoint variable, which should be used to filter the data - notation: 'topic/variable'.",
    )
    parser.add_argument(
        "--plot",
        metavar="plot",
        type=string_to_bool,
        default="True",
        help="Show plots after fit.",
    )
    parser.add_argument(
        "--extraction",
        metavar="extraction",
        type=string_to_bool,
        default="False",
        required=False,
        help="Specify if the parameter extraction should be applied as well.",
    )
    parser.add_argument(
        "--normalization",
        metavar="normalization",
        type=string_to_bool,
        default="True",
        required=False,
        help="Determine if the actuator data should be normalized before model estimation (False for simulation data).",
    )
    arg_list = parser.parse_args()
    start_model_estimation(**vars(arg_list))
