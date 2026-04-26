# libs
import pandas as pd
from auth import auth
from fetch import fetch

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

# acessando playlist
playlist_id = 'spotify:playlist:1rWIhl1hpQnpkUDRV4RIKT'
playlist = sp.playlist_tracks(
    playlist_id=playlist_id,
)

# isolando as tracks em um dataframe
playlist = pd.DataFrame([item['item'] for item in playlist['items'] if item is not None], index=None)

# mapeando os generos
playlist['artist_id'] = playlist['artists'].apply(
    lambda artists: artists[0]['id'] if artists else None
)

mapping = fetch(sp, playlist['artist_id'])
playlist['genres'] = playlist['artist_id'].map(mapping)
