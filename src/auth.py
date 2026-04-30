def auth() -> tuple[str, str, str]:
    """
    gera constantes de autenticação, com base no arquvio auth.txt.
    retorna os valores exigidos pelo autenticador do spotipy:
    CLIENT_ID, CLIENT_SECRET, REDIRECT_URI
    """
    with open('auth.txt', 'r') as file:
        CLIENT_ID      = file.readline().strip()
        CLIENT_SECRET  = file.readline().strip()
        REDIRECT_URI   = file.readline().strip()
    return(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)