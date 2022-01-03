from config import ASTRA_DB_ID, ASTRA_DB_REGION, ASTRA_DB_APPLICATION_TOKEN
ASTRA_DB_KEYSPACE = 'discordplaylists'

from astrapy.client import create_astra_client

'''
Refer to AstraPY and the Datastax API Reference.
'''

class AstraClient():
    def __init__(self):
        self.client = create_astra_client(astra_database_id=ASTRA_DB_ID,
                                   astra_database_region=ASTRA_DB_REGION,
                                   astra_application_token=ASTRA_DB_APPLICATION_TOKEN)