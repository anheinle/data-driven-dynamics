__author__ = "Manuel Galliker"
__maintainer__ = "Manuel Galliker"
__license__ = "BSD 3"

""" The model class contains properties shared between all models and shgall simplyfy automated checks and the later 
export to a sitl gazebo model by providing a unified interface for all models. """

from ..tools import load_ulog, pandas_from_topic, compute_flight_time, resample_dataframes
from pyulog import core
import pandas as pd


class DynamicsModel():
    def __init__(self, rel_ulog_path, req_topics_dict):
        assert type(
            req_topics_dict) is dict, 'req_topics_dict input must be a dict'
        assert bool(req_topics_dict), 'req_topics_dict can not be empty'
        self.ulog = load_ulog(rel_ulog_path)
        self.req_topics_dict = req_topics_dict
        print(self.req_topics_dict.keys())
        assert self.check_ulog_for_req_topics(
        ), 'not all required topics or topic types are contained in the log file'

    def check_ulog_for_req_topics(self):
        for topic_type in self.req_topics_dict.keys():
            try:
                topic_type_data = self.ulog.get_dataset(topic_type)
                topic_type_data = topic_type_data.data
                topic_list = self.req_topics_dict[topic_type]
                for topic in topic_list:
                    topic_data = (topic_type_data[topic])
            except:
                return False
        return True

    def compute_resampled_dataframe(self, resample_freq):
        # setup object to crop dataframes for flight data
        fts = compute_flight_time(self.ulog)
        df_list = []
        # getting data
        for topic_type in self.req_topics_dict.keys():
            curr_df = pandas_from_topic(self.ulog, [topic_type])
            curr_df = curr_df[self.req_topics_dict[topic_type]]
            df_list.append(curr_df)

        resampled_df = resample_dataframes(
            df_list, fts["t_start"], fts["t_end"], resample_freq)
        return resampled_df
