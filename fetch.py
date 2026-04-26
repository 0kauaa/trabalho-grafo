def fetch(sp, artist_ids) -> dict:
    """
    busca pelos generos de cada artista da playlist.
    retorna um dicionario para mapear os generos do dataframe.
    """
    artist_ids = list(set(artist_ids))

    genres_map = {}

    for i in range(0, len(artist_ids), 50):
        batch = artist_ids[i:i+50]

        response = sp.artists(batch)

        for artist in response["artists"]:
            genres_map[artist["id"]] = artist["genres"]

    return genres_map