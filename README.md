# Playlist Communities

Análise de similaridade e detecção de comunidades em playlists do Spotify através de grafos.

## Visão Geral

Este projeto é uma atividade acadêmica da matéria de Processamento de Linguegem Natural do curso de Ciência de Dados da Fatec Baixada Santista "Rubens Lara". O projeto analisa uma playlist do Spotify e constrói um grafo de similaridade entre faixas, identificando automaticamente agrupamentos (comunidades) de músicas similares usando o algoritmo Louvain.

A métrica de similaridade combina:

- **70%** - Popularidade normalizada das faixas
- **30%** - Presença de artistas compartilhados

## Requisitos

- Python 3.12+
- Conta de desenvolvedor no [Spotify Developer Dashboard](https://developer.spotify.com/)

## Instalação

### 1. Clonar o repositório

```bash
git clone https://github.com/0kauaa/playlist-communities.git
cd playlist-communities
```

### 2. Criar ambiente virtual

```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar credenciais Spotify

Crie um arquivo `auth.txt` na raiz do projeto com:

```
CLIENT_ID
CLIENT_SECRET
REDIRECT_URI
```

Obtenha essas credenciais em: [https://developer.spotify.com/dashboard/applications](https://developer.spotify.com/dashboard/applications)

## Uso

### Executar a análise

```bash
python main.py
```

O programa solicitará um ID, URI ou URL de playlist do Spotify.

**Exemplos de entrada válida:**

- `37i9dQZF1DXcBWIGoYBM5M` (ID)
- `spotify:playlist:37i9dQZF1DXcBWIGoYBM5M` (URI)
- `https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M?si=...` (URL)

### Saídas geradas

Após a execução, os seguintes arquivos serão criados:

| Arquivo                           | Descrição                                                                               |
| --------------------------------- | ----------------------------------------------------------------------------------------- |
| `data/playlist_data.csv`        | Dados estruturados das músicas (ID, nome, artista, duração, popularidade, explicitude) |
| `data/playlist_edges.csv`       | Arestas do grafo com pesos de similaridade                                                |
| `graphs/playlist_graph.png`     | Visualização do grafo                                                                   |
| `graphs/playlist_graph.graphml` | Grafo em formato GraphML (compatível com Gephi, Cytoscape, etc.)                         |

## Componentes

### `main.py`

Orquestra a execução completa do pipeline:

1. Autenticação no Spotify
2. Busca da playlist
3. Estruturação do DataFrame
4. Cálculo de similaridades
5. Construção do grafo
6. Detecção de comunidades
7. Visualização e exportação

### `src/auth.py`

Gerencia autenticação com as credenciais do arquivo `auth.txt`.

### `src/access.py`

Interface com a API do Spotify:

- `get_spotify_client()`: cria cliente autenticado
- `fetch_playlist_tracks()`: obtém todas as faixas da playlist

### `src/dataframe.py`

Estrutura e resume dados:

- `build_dataframe()`: cria DataFrame com atributos essenciais
- `summarize_dataframe()`: exibe resumo da playlist

### `src/graph.py`

Operações de grafo:

- `compute_similarity()`: calcula matriz de similaridade
- `extract_edges()`: filtra arestas por threshold e limite de vizinhos
- `create_graph()`: monta grafo igraph com atributos
- `detect_communities()`: detecta comunidades usando Louvain
- `visualize_graph()`: renderiza e salva imagem do grafo

## Configuração de Parâmetros

No arquivo `main.py`, você pode ajustar:

```python
# Threshold mínimo de similaridade (0-1)
edges = extract_edges(df, sim_matrix, threshold=0.6, max_per_node=10)
```

- `threshold`: Similaridade mínima para criar uma aresta (aumentar = menos arestas)
- `max_per_node`: Número máximo de vizinhos por nó

## Visualização

O grafo é renderizado com:

- **Layout**: Fruchterman-Reingold (posicionamento baseado em força)
- **Tamanho de nó**: Proporcional à popularidade da faixa
- **Cor de nó**: Baseada na comunidade detectada
- **Peso de aresta**: Representa a similaridade entre faixas

## Interpretação dos Resultados

### O Que Significa o Grafo?

**Nós** = Cada música da playlist
**Arestas** = Conexão entre duas músicas similares

### Fórmula de Similaridade

```
score = 0.7 × sim_popularidade + 0.3 × sim_artistas

Onde:
  • sim_popularidade = 1 - |pop1_norm - pop2_norm|
    └─ Quão parecidas são as popularidades (0-1)
  
  • sim_artistas = 1 se artistas compartilhados, 0 caso contrário
    └─ Dá peso extra para músicas do mesmo artista
```

### Estrutura Visual Esperada

```
CENTRO (muitas conexões):
  └─ Músicas populares (70-100 de popularidade)
  └─ Fortemente conectadas entre si
  └─ Seu "core" de hits

PERIFÉRIA (poucas conexões):
  └─ Músicas menos populares (0-50 de popularidade)
  └─ Talvez descobertas pessoais
  └─ Menos conectadas ao resto

PROXIMIDADE DENTRO DE CLUSTERS:
  └─ Nós muito próximos = MESMO ARTISTA ou popularidade parecida
  └─ Você verá agrupamentos por artista e faixa de popularidade
```

### O Que as Comunidades Significam?

Diferente de análises por gênero/mood, suas comunidades representam:

- **Agrupamentos por faixa de popularidade** (qual é o público)
- **Artistas em comum dentro de cada comunidade**
- Não é por gênero musical, mas por como as músicas "escalam" em popularidade

**Exemplo esperado:**

```
Comunidade 1 (40% dos nós) = Hits populares (80-100)
Comunidade 2-5 (50% dos nós) = Artistas em diferentes faixas de popularidade
Comunidades menores (10%) = Outliers ou descobertas pessoais
```

### Métricas Úteis

- **Densidade**: % de todas as possíveis arestas que existem

  - Alta (>50%) = Playlist concentrada em popularidades parecidas
  - Baixa (<30%) = Variedade grande de popularidades
- **Grau médio**: Quantas conexões cada música tem em média

  - Saudável: 10-20 para ~40 nós
- **Tamanho das comunidades**:

  - Comunidade grande = Seu "gosto principal"
  - Comunidades pequenas = Experimentação

## Dependências

- `pandas`: estruturação e análise de dados
- `numpy`: operações numéricas
- `spotipy`: autenticação e acesso à API do Spotify
- `python-igraph`: construção e análise de grafos

## Estrutura de Diretórios

```
playlist-communities/
├── auth.txt                     # Credenciais Spotify (não versionar)
├── main.py                      # Script principal
├── requirements.txt             # Dependências Python
├── README.md                    # Este arquivo
├── src/
│   ├── __init__.py
│   ├── auth.py                  # Autenticação
│   ├── access.py                # Acesso à API Spotify
│   ├── dataframe.py             # Construção de DataFrame
│   └── graph.py                 # Operações de grafo
├── data/
│   ├── playlist_data.csv        # Faixas (gerado)
│   └── playlist_edges.csv       # Arestas (gerado)
├── graphs/
│   ├── playlist_graph.png       # Imagem (gerado)
│   └── playlist_graph.graphml   # GraphML (gerado)
└── desc/
    ├── descricao_projeto.txt
    ├── estrutura_playlist.txt
    └── exemplo_item.json
```

## O Que Pode Fazer Com Seus Resultados

1. **Entender seu padrão de escuta**

   - Qual é seu "core" de hits? (comunidade maior)
   - Qual % é exploração vs hits conhecidos?
2. **Análise de recomendações**

   - Artistas na comunidade maior podem ter mais música para explorar
   - Comunidades pequenas podem revelar gêneros ou artistas de nicho
3. **Exportação para outras ferramentas**

   - Arquivo GraphML pode ser aberto em Gephi ou Cytoscape
   - CSV de arestas mostra todos os pesos de similaridade
4. **Decomposição da playlist**

   * Decompor uma playlist em diferentes outras por comunidades identificadas

## Dicas de Interpretação

- Se a maioria dos nós está no centro → seu gosto é "hits"
- Se há clusters bem separados → você tem múltiplos estilos/públicos
- Se uma comunidade é 50%+ → essa é sua preferência principal
- Arestas espessas = similaridade alta (mesmo artista ou popularidade muito parecida)

## Limitações e Considerações

- A API do Spotify tem limites de requisição (rate limiting)
- Playlists muito grandes podem levar tempo para processar
- A qualidade das comunidades detectadas depende do threshold de similaridade configurado
- Requer acesso a internet para autenticação e busca de dados
- Esta implementação não analisa gênero ou audio features, apenas popularidade e artistas

## Licença

MIT

## Autor

Kauã Santana
