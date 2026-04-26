# libs
from auth import auth
import json
import pandas as pd

import spotipy
from spotipy.oauth2 import SpotifyOAuth

# autenticação
CLIENT_ID, CLIENT_SECRET, REDIRECT_URI = auth()
SCOPE = 'playlist-read-private'

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id = CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE
    )
)

# usuario (eu mesmo)
user    = sp.current_user()
user_id = user['id']

# acessando e salvando playlist
playlist_id = 'spotify:playlist:1rWIhl1hpQnpkUDRV4RIKT'
playlist = sp.playlist_tracks(
    playlist_id=playlist_id,
)

playlist_df = pd.DataFrame(playlist)
playlist_df.to_csv('playlist.csv')