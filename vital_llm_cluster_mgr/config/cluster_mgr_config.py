import logging

import yaml


class ClusterMgrConfig:
    def __init__(self, file_path):

        self.runpod_key = ""

        self.load_config(file_path)

    def load_config(self, file_path):
        try:
            with open(file_path, 'r') as file:
                config = yaml.safe_load(file)

                cluster_mgr_config = config.get("vital_llm_cluster_mgr", {})

                self.runpod_key = cluster_mgr_config.get("runpod_key", "")

                logging.info("Configuration loaded successfully.")
        except FileNotFoundError:
            logging.info(f"Configuration file not found at: {file_path}")
        except yaml.YAMLError as e:
            logging.info(f"Error parsing YAML file: {e}")
