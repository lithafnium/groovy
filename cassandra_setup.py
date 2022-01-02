from config import ASTRA_DB_ID, ASTRA_DB_REGION, ASTRA_DB_APPLICATION_TOKEN
ASTRA_DB_KEYSPACE = 'discordplaylists'

from astrapy.client import create_astra_client

'''
Initial creation of schema file for Cassandra DB on Datastax Astra
'''

astra_client = create_astra_client(astra_database_id=ASTRA_DB_ID,
                                   astra_database_region=ASTRA_DB_REGION,
                                   astra_application_token=ASTRA_DB_APPLICATION_TOKEN)

print(astra_client.schemas.get_tables(keyspace=ASTRA_DB_KEYSPACE))

drop_playlists_response = astra_client.schemas.delete_table(keyspace=ASTRA_DB_KEYSPACE, table='Playlists')
drop_tracks_response = astra_client.schemas.delete_table(keyspace=ASTRA_DB_KEYSPACE, table='playlist_tracks')

print(drop_playlists_response)
print(drop_tracks_response)

'''Guild ID as index associated with playlist IDs'''
playlist_response = astra_client.schemas.create_table(keyspace=ASTRA_DB_KEYSPACE, table_definition={
    'name': 'playlists',
    'columnDefinitions': [
        {
            'name': 'guild_id',
            'typeDefinition': 'text'
        },
        {
            'name': 'playlist_tid',
            'typeDefinition': 'timeuuid'
        }
    ],
    'primaryKey': {
        'partitionKey': ['guild_id'],
        'clusteringKey': ['playlist_tid']
    },
    'tableOptions': {
        'clusteringExpression': [
            {
            'column': 'playlist_tid',
            'order': 'DESC'
            }
        ]
    }
})

'''Playlist ID as index with track name as a field'''
playlist_track_response = astra_client.schemas.create_table(keyspace=ASTRA_DB_KEYSPACE, table_definition={
    'name': 'playlist_tracks',
    'columnDefinitions': [
        {
            'name': 'playlist_tid',
            'typeDefinition': 'timeuuid'
        },
        {
            'name': 'added',
            'typeDefinition': 'timestamp'
        },
        {
            'name': 'song_name',
            'typeDefinition': 'text'
        }
    ],
    'primaryKey': {
        'partitionKey': ['playlist_tid'],
        'clusteringKey': ['added']
    },
    'tableOptions': {
        'clusteringExpression': [
            {
            'column': 'added',
            'order': 'DESC'
            }
        ]
    }
})

print(playlist_response)
print(playlist_track_response)