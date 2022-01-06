import sys

from src.config import ASTRA_DB_ID, ASTRA_DB_REGION, ASTRA_DB_APPLICATION_TOKEN
from typing import List

ASTRA_DB_KEYSPACE = "discordplaylists"

from astrapy.client import create_astra_client

"""
Refer to AstraPY and the Datastax API Reference.
"""


class AstraClient:
    def __init__(self):
        self.client = create_astra_client(
            astra_database_id=ASTRA_DB_ID,
            astra_database_region=ASTRA_DB_REGION,
            astra_application_token=ASTRA_DB_APPLICATION_TOKEN,
        )
        print(self.client.schemas.get_tables(keyspace=ASTRA_DB_KEYSPACE))
        print(self.client.collections.namespace(ASTRA_DB_KEYSPACE).get_collections())

    """
        Design:
            - Add playlist
            - Add track
            - 
    """

    def add_playlist(self, playlist_name: str, tracks: List[str]):
        pass

    def add_track(self, track_name: str):
        pass


a = AstraClient()
