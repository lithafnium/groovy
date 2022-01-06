import datetime

from cassandra.util import max_uuid_from_time

from src.config import ASTRA_DB_ID, ASTRA_DB_REGION, ASTRA_DB_APPLICATION_TOKEN
from typing import List
from astrapy.client import create_astra_client

ASTRA_DB_KEYSPACE = "discordplaylists"


class AstraClient:
    def __init__(self):
        self.client = create_astra_client(
            astra_database_id=ASTRA_DB_ID,
            astra_database_region=ASTRA_DB_REGION,
            astra_application_token=ASTRA_DB_APPLICATION_TOKEN,
        )

    def add_row(self, row_definition, table_name: str):
        self.client.rest.add_row(
            keyspace=ASTRA_DB_KEYSPACE, table=table_name, row=row_definition
        )

    def get_timeuuid(self):
        now = datetime.datetime.now()
        return max_uuid_from_time(now)
