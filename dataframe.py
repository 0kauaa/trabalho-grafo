# libs
import pandas as pd
from typing import List, Dict

# esturura o dataframe
def build_dataframe(
    tracks: List[dict],
    genre_mapping: Dict[str, List[str]],
    audio_features: Dict[str, dict]
) -> pd.DataFrame:
    """
    consolida tracks, gêneros e audio features em um dataframe único
    
    args:
        tracks: lista de objetos track da api
        genre_mapping: Dicionário {artist_id: [genres]}
        audio_features: Dicionário {track_id: audio_features}
        
    returns:
        dataFrame com todas as informações
    """
    
    data = []
    
    for track in tracks:
        if track['id'] is None:
            continue
        
        # artista principal
        artist = track['artists'][0] if track['artists'] else {}
        artist_id = artist.get('id')
        
        # linha
        row = {
            'track_id': track['id'],
            'track_name': track['name'],
            'artist_id': artist_id,
            'artist_name': artist.get('name'),
            'duration_ms': track['duration_ms'],
            'popularity': track['popularity'],
            'explicit': track['explicit'],
            'genres': genre_mapping.get(artist_id, []),
        }
        
        # audio features
        if track['id'] in audio_features:
            feat = audio_features[track['id']]
            row.update({
                'danceability': feat.get('danceability'),
                'energy': feat.get('energy'),
                'acousticness': feat.get('acousticness'),
                'instrumentalness': feat.get('instrumentalness'),
                'liveness': feat.get('liveness'),
                'speechiness': feat.get('speechiness'),
                'valence': feat.get('valence'),
                'tempo': feat.get('tempo'),
                'key': feat.get('key'),
                'loudness': feat.get('loudness'),
                'time_signature': feat.get('time_signature'),
            })
        
        data.append(row)
    
    df = pd.DataFrame(data)
    
    print(f"\dataframe criado: {len(df)} tracks × {len(df.columns)} colunas")
    
    return df

# detalhes do dataframe da playlist
def summarize_dataframe(df: pd.DataFrame) -> None:
    """
    exibe resumo exploratório do dataframe
    
    args:
        df: dataFrame da playlist
    """
    print("\nRESUMO DA PLAYLIST")
    print(f"\ntracks: {len(df)}")
    print(f"artistas únicos: {df['artist_name'].nunique()}")
    print(f"duração total: {df['duration_ms'].sum() / 60000:.1f} minutos")
    
    # gêneros mais frequentes
    from collections import Counter
    all_genres = []
    for genres_list in df['genres']:
        all_genres.extend(genres_list)
    
    if all_genres:
        genre_counts = Counter(all_genres)
        print(f"\ntop 5 gêneros:")
        for genre, count in genre_counts.most_common(5):
            print(f"  • {genre}: {count} artista(s)")
    
    # audio features médias
    audio_cols = ['danceability', 'energy', 'acousticness', 'valence']
    print(f"\naudio features (média):")
    for col in audio_cols:
        if col in df.columns and df[col].notna().any():
            avg = df[col].mean()
            print(f"  • {col}: {avg:.2f}")