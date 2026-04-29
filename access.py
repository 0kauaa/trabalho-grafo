# libs
import spotipy
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
        
        for item in results['items']:
            if item['track'] is not None:
                tracks.append(item['track'])
        
        offset += limit
    
    print(f"{len(tracks)} tracks encontradas")
    
    return tracks

# acessa os genêros dos artistas
def fetch_artist_genres(sp: spotipy.Spotify, artist_ids: List[str]) -> dict:
    """
    busca gêneros dos artistas (até 50 por request)
    
    args:
        sp: cliente spotipy autenticado
        artist_ids: lista de ids de artistas
        
    returns:
        dicionário {artist_id: [genres]}
    """
    genre_mapping = {}
    artist_ids = list(set([aid for aid in artist_ids if aid is not None]))
    
    print(f"buscando gêneros para {len(artist_ids)} artistas...")
    
    for i in range(0, len(artist_ids), 50):
        chunk = artist_ids[i:i+50]
        
        try:
            artists = sp.artists(chunk)
            for artist in artists['artists']:
                if artist is not None:
                    genre_mapping[artist['id']] = artist.get('genres', [])
        except Exception as e:
            print(f"erro ao buscar artistas: {e}")
    
    print(f"gêneros obtidos para {len(genre_mapping)} artistas")
    
    return genre_mapping

# acessa as áudio features das tracks
def fetch_audio_features(sp: spotipy.Spotify, track_ids: List[str]) -> dict:
    """
    busca audio features das tracks (até 100 por request)
    
    args:
        sp: cliente spotipy autenticado
        track_ids: lista de ids de tracks
        
    returns:
        dicionário {track_id: audio_features}
    """
    features_mapping = {}
    track_ids = list(set([tid for tid in track_ids if tid is not None]))
    
    print(f"buscando audio features para {len(track_ids)} tracks...")
    
    for i in range(0, len(track_ids), 100):
        chunk = track_ids[i:i+100]
        
        try:
            audio_feats = sp.audio_features(chunk)
            for feat in audio_feats:
                if feat is not None:
                    features_mapping[feat['id']] = feat
        except Exception as e:
            print(f"erro ao buscar audio features: {e}")
    
    print(f"audio features obtidos para {len(features_mapping)} tracks")
    
    return features_mapping