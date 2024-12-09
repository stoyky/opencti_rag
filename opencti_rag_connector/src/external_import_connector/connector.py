import sys
from datetime import datetime
from dateutil import parser
import pprint 
import requests
import html2text
import requests
       
from pycti import OpenCTIConnectorHelper, OpenCTIApiClient
from mitreattack.stix20 import MitreAttackData

from llama_index.core.schema import Document
from llama_index.vector_stores.elasticsearch import ElasticsearchStore
from llama_index.readers.web import SimpleWebPageReader
from llama_index.core import StorageContext
from llama_index.core import VectorStoreIndex
from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from .client_api import ConnectorClient
from .config_variables import ConfigConnector


class OpenCTI_RAG_Connector:
    """
    Specifications of the external import connector

    This class encapsulates the main actions, expected to be run by any external import connector.
    Note that the attributes defined below will be complemented per each connector type.
    This type of connector aim to fetch external data to create STIX bundle and send it in a RabbitMQ queue.
    The STIX bundle in the queue will be processed by the workers.
    This type of connector uses the basic methods of the helper.

    ---

    Attributes
        - `config (ConfigConnector())`:
            Initialize the connector with necessary configuration environment variables

        - `helper (OpenCTIConnectorHelper(config))`:
            This is the helper to use.
            ALL connectors have to instantiate the connector helper with configurations.
            Doing this will do a lot of operations behind the scene.

        - `converter_to_stix (ConnectorConverter(helper))`:
            Provide methods for converting various types of input data into STIX 2.1 objects.

    ---

    Best practices
        - `self.helper.api.work.initiate_work(...)` is used to initiate a new work
        - `self.helper.schedule_iso()` is used to encapsulate the main process in a scheduler
        - `self.helper.connector_logger.[info/debug/warning/error]` is used when logging a message
        - `self.helper.stix2_create_bundle(stix_objects)` is used when creating a bundle
        - `self.helper.send_stix2_bundle(stix_objects_bundle)` is used to send the bundle to RabbitMQ
        - `self.helper.set_state()` is used to set state

    """

    def __init__(self):
        """
        Initialize the Connector with necessary configurations
        """

        # Load configuration file and connection helper
        self.config = ConfigConnector()
        self.helper = OpenCTIConnectorHelper(self.config.load)
        self.client = OpenCTIApiClient(url=self.config.OPENCTI_URL, token=self.config.OPENCTI_TOKEN)

        self.vector_store = ElasticsearchStore(
            es_url=self.config.ELASTICSEARCH_URL,
            index_name=self.config.ELASTICSEARCH_INDEX
        )

        self.index = None 
        self.init_vector_store()
        self.collect_and_send_reports(self.config.IMPORT_REPORTS_AFTER)

    def init_vector_store(self):
        mitre_attack_data = MitreAttackData("enterprise-attack.json")

        groups = mitre_attack_data.get_groups(remove_revoked_deprecated=True)

        docs = []

        group_urls = []
        for group in groups:
            group_urls.append(group["external_references"][0]["url"])

        for group_url in group_urls:
            try:
                temp_docs = SimpleWebPageReader(html_to_text=True).load_data([group_url])
                for doc in temp_docs:
                    doc.metadata = {"url" : group_url}
                    docs.append(doc)
            except:
                pass

        # define embedding function
        # For models see: https://huggingface.co/spaces/mteb/leaderboard
        Settings.embed_model = HuggingFaceEmbedding(
            model_name=self.config.EMBEDDING_MODEL
        )

        storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        self.index = VectorStoreIndex.from_documents(
            docs, storage_context=storage_context
        )

        self.helper.log_info("Ingestion of MITRE ATT&CK data finished.")

    def collect_and_send_reports(self, last_run) -> list:
        client = OpenCTIApiClient(self.config.OPENCTI_URL, token=self.config.OPENCTI_TOKEN)
        
        data = {"pagination": {"hasNextPage": True, "endCursor": None}}
        while data["pagination"]["hasNextPage"]:
            after = data["pagination"]["endCursor"]
            if after:
                print("Listing reports after " + after)
            data = client.report.list(
                first=50,
                after=after,
                withPagination=True,
                orderBy="published",
                orderMode="desc",
            )

            count = 0
            for report in data["entities"]:
                report_published_date = parser.parse(report["published"], ignoretz=True)
                last_run_datetime = parser.parse(last_run)
                if report_published_date > last_run_datetime:
                    self.helper.log_info("Loading report from most recent to cutoff date...")
                    self.helper.log_info("Title: " + str(report["name"]))
                    self.helper.log_info("Date: " + str(report_published_date.date()) + " - cutoff date: " + str(last_run_datetime))
                    try:
                        for ext_ref in report["externalReferences"]:
                            response = requests.get(ext_ref["url"], headers=None, timeout=3).text
                            text = html2text.html2text(response)

                            report_doc = Document(text=text, id_=ext_ref["url"], metadata={"url" : ext_ref["url"]})

                            if len(report_doc.text) <= 20:
                                report_doc.text = report["description"]

                            self.index.insert(report_doc)

                    except Exception as e:
                        self.helper.log_info("Error.")
                        pass

                    count+=1
                else:
                    return
                
    def process_message(self) -> None:
        """
        Connector main process to collect intelligence
        :return: None
        """
        self.helper.connector_logger.info(
            "[CONNECTOR] Starting connector...",
            {"connector_name": self.helper.connect_name},
        )

        try:
            # Get the current state
            now = datetime.now()
            current_timestamp = int(datetime.timestamp(now))
            current_state = self.helper.get_state()

            if current_state is not None and "last_run" in current_state:
                last_run = current_state["last_run"]

                self.helper.connector_logger.info(
                    "[CONNECTOR] Connector last run",
                    {"last_run_datetime": last_run},
                )
            else:
                self.helper.connector_logger.info(
                    "[CONNECTOR] Connector has never run..."
                )

            # Friendly name will be displayed on OpenCTI platform
            friendly_name = "Connector template feed"

            # Initiate a new work
            work_id = self.helper.api.work.initiate_work(
                self.helper.connect_id, friendly_name
            )

            self.helper.connector_logger.info(
                "[CONNECTOR] Running connector...",
                {"connector_name": self.helper.connect_name},
            )

            # Performing the collection of intelligence
            # ===========================
            # === Add your code below ===
            # ===========================

            last_run = datetime.strptime(self.helper.get_state()["last_run"], "%Y-%m-%d %H:%M:%S")
            last_run = last_run.strftime("%Y-%m-%d")
            self.collect_and_send_reports(last_run=last_run)

            # ===========================
            # === Add your code above ===
            # ===========================

            # Store the current timestamp as a last run of the connector
            self.helper.connector_logger.debug(
                "Getting current state and update it with last run of the connector",
                {"current_timestamp": current_timestamp},
            )
            current_state = self.helper.get_state()
            current_state_datetime = now.strftime("%Y-%m-%d %H:%M:%S")
            last_run_datetime = datetime.utcfromtimestamp(current_timestamp).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            if current_state:
                current_state["last_run"] = current_state_datetime
            else:
                current_state = {"last_run": current_state_datetime}
            self.helper.set_state(current_state)

            message = (
                f"{self.helper.connect_name} connector successfully run, storing last_run as "
                + str(last_run_datetime)
            )

            self.helper.api.work.to_processed(work_id, message)
            self.helper.connector_logger.info(message)

        except (KeyboardInterrupt, SystemExit):
            self.helper.connector_logger.info(
                "[CONNECTOR] Connector stopped...",
                {"connector_name": self.helper.connect_name},
            )
            sys.exit(0)
        except Exception as err:
            self.helper.connector_logger.error(str(err))

    def run(self) -> None:
        """
        Run the main process encapsulated in a scheduler
        It allows you to schedule the process to run at a certain intervals
        This specific scheduler from the pycti connector helper will also check the queue size of a connector
        If `CONNECTOR_QUEUE_THRESHOLD` is set, if the connector's queue size exceeds the queue threshold,
        the connector's main process will not run until the queue is ingested and reduced sufficiently,
        allowing it to restart during the next scheduler check. (default is 500MB)
        It requires the `duration_period` connector variable in ISO-8601 standard format
        Example: `CONNECTOR_DURATION_PERIOD=PT5M` => Will run the process every 5 minutes
        :return: None
        """
        self.helper.schedule_iso(
            message_callback=self.process_message,
            duration_period=self.config.duration_period,
        )
