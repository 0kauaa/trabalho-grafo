# libs
import pandas as pd
from typing import List

# esturura o dataframe
def build_dataframe(
    tracks: List[dict]
) -> pd.DataFrame:
    """
    consolida tracks em um dataframe único
    
    args:
        tracks: lista de objetos track da api
        
    returns:
        dataFrame com as informações essenciais de cada track
    """
    
    data = []
    
    for track in tracks:
        if not isinstance(track, dict) or track.get('id') is None:
            continue
        
        # artista principal
        artists = track.get('artists') or []
        artist = artists[0] if len(artists) > 0 else {}
        artist_id = artist.get('id')
        
        # linha
        row = {
            'track_id': track.get('id'),
            'track_name': track.get('name'),
            'artist_id': artist_id,
            'artist_name': artist.get('name'),
            'duration_ms': track.get('duration_ms', 0),
            'popularity': track.get('popularity', 0),
            'explicit': track.get('explicit', False),
        }
        
        data.append(row)
    
    df = pd.DataFrame(data)
    
    print(f"dataframe criado: {len(df)} tracks × {len(df.columns)} colunas")
    
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
    
    # artistas mais frequentes
    top_artists = df['artist_name'].value_counts().head(5)
    
    if not top_artists.empty:
        print(f"\ntop 5 artistas:")
        for artist, count in top_artists.items():
            print(f"  • {artist}: {count} track(s)")
