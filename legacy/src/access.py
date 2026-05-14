# libs
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import List

# acessa a playlist e retorna as tracks
def fetch_playlist_tracks(sp: spotipy.Spotify, playlist_id: str) -> List[dict]:
    """
    busca todas as tracks de uma playlist com paginação
    
    args:
        sp: cliente spotipy autenticado
        playlist_id: ID ou URI da playlist
        
    returns:
        listal de objetos track
    """
    tracks = []
    offset = 0
    limit = 50
    
    print(f"buscando tracks da playlist...")
    
    while True:
        results = sp.playlist_tracks(
            playlist_id=playlist_id,
            offset=offset,
            limit=limit
        )
        
        if not results['items']:
            break
        
        for item in results.get('items', []):
            track = item.get('track') or item.get('item')
            if track is not None:
                tracks.append(track)
        
        offset += limit
    
    print(f"{len(tracks)} tracks encontradas")
    
    return tracks

# autenticação do usuario
def get_spotify_client(client_id: str, client_secret: str, redirect_uri: str) -> spotipy.Spotify:
    """
    autentica e retorna cliente spotify autenticado
    
    args:
        client_id: id da aplicação Spotify
        client_secret: secret da aplicação Spotify
        redirect_uri: uri de redirecionamento
        
    returns:
        cliente Spotipy autenticado
    """
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope='playlist-read-private'
        )
    )
    
    # Validar autenticação
    user = sp.current_user()
    print(f"autenticado como: {user.get('display_name', user['id'])}")
    
    return sp