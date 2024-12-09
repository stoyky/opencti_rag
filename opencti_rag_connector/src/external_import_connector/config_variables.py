import os
from pathlib import Path

import yaml
from pycti import get_config_variable


class ConfigConnector:
    def __init__(self):
        """
        Initialize the connector with necessary configurations
        """

        # Load configuration file
        self.load = self._load_config()
        self._initialize_configurations()

    @staticmethod
    def _load_config() -> dict:
        """
        Load the configuration from the YAML file
        :return: Configuration dictionary
        """
        config_file_path = Path(__file__).parents[1].joinpath("config.yml")
        config = (
            yaml.load(open(config_file_path), Loader=yaml.FullLoader)
            if os.path.isfile(config_file_path)
            else {}
        )

        return config

    def _initialize_configurations(self) -> None:
        """
        Connector configuration variables
        :return: None
        """
        self.duration_period = get_config_variable(
            "CONNECTOR_DURATION_PERIOD",
            ["connector", "duration_period"],
            self.load,
        )

        self.OPENCTI_URL = get_config_variable(
            "OPENCTI_URL",
            ["opencti", "url"],
            self.load,
        )

        self.OPENCTI_TOKEN = get_config_variable(
            "OPENCTI_TOKEN",
            ["opencti", "token"],
            self.load,
        )

        self.ELASTICSEARCH_URL = get_config_variable(
            "CONNECTOR_ELASTICSEARCH_URL",
            ["connector", "elasticsearch_url"],
            self.load,
        )

        self.ELASTICSEARCH_INDEX = get_config_variable(
            "CONNECTOR_ELASTICSEARCH_INDEX",
            ["connector", "elasticsearch_index"],
            self.load,
        )

        self.EMBEDDING_MODEL = get_config_variable(
            "CONNECTOR_EMBEDDING_MODEL",
            ["connector", "embedding_model"],
            self.load,
        )

        self.IMPORT_REPORTS_AFTER = get_config_variable(
            "CONNECTOR_IMPORT_REPORTS_AFTER",
            ["connector", "import_reports_after"],
            self.load,
        )
