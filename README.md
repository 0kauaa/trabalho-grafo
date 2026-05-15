# 🎵 Playlist Communities

> Análise de Similaridade e Detecção de Comunidades em Playlists do Spotify

**Disciplina:** Processamento de Linguagem Natural
**Curso:** Ciência de Dados — Fatec Baixada Santista - Rubens Lara
**Autores:** Kauã Santana · Victor Leme

---

## Visão Geral

Toda playlist conta uma história — mas será que músicas colocadas juntas são realmente similares entre si? Este projeto investiga essa pergunta construindo dois **grafos de similaridade** sobre uma playlist do Spotify e identificando automaticamente agrupamentos (***comunidades***) de faixas que se parecem.

A análise é feita em duas perspectivas complementares:

- **Grafo Estrutural** — agrupa faixas por *duração* e *artista em comum*, capturando similaridade de formato e proximidade editorial
- **Grafo Lírico** — agrupa faixas pelo *conteúdo semântico das letras*, usando embeddings de linguagem para medir o quanto as músicas falam sobre os mesmos temas

### Pipeline

```
Autenticação → Fetch Playlist → DataFrame → [Grafo Estrutural] → Comunidades
                                          → [Busca de Letras]  → [Grafo Lírico] → Comparação
```

---

## Estrutura do Repositório

```
playlist-communities/
│
├── playlist_communities.ipynb  ← notebook principal (versão atual)
├── fetch_lyrics.py             ← script local para busca de letras*
│
├── data/
│   ├── playlist_data.csv       ← faixas extraídas da playlist
│   ├── lyrics.csv              ← letras coletadas
│   └── lyrics_report.csv       ← relatório de cobertura das letras
│
├── graphs/                     ← imagens e GraphML gerados pelo notebook
│
├── legacy/                     ← fase inicial do projeto (Python puro, abandonada)
│   ├── main.py
│   └── src/
│       ├── access.py
│       ├── auth.py
│       ├── dataframe.py
│       ├── graph.py
│       └── __init__.py
│
├── auth.txt                    ← credenciais locais (não versionado)
├── requirements.txt
└── .gitignore
```

> \* `fetch_lyrics.py` é executado **localmente** (não no Colab). A API do Genius rejeita IPs de datacenter, então a busca de letras precisa rodar na máquina do desenvolvedor e os CSVs resultantes são enviados manualmente para o Colab.

---

## Como Reproduzir

### Pré-requisitos

- Python 3.10+
- Conta no [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) (para obter `CLIENT_ID` e `CLIENT_SECRET`, que devem ser correspondentes à conta no Spotify Developer Dashboard)
- Token da [Genius API](https://genius.com/api-clients) (gratuito)

### 1. Clonar e instalar dependências

```bash
git clone https://github.com/<usuario>/playlist-communities.git
cd playlist-communities
pip install -r requirements.txt
```

### 2. Configurar credenciais

Crie um arquivo `auth.txt` na raiz com três linhas:

```
SEU_SPOTIFY_CLIENT_ID
SEU_SPOTIFY_CLIENT_SECRET
https://open.spotify.com
```

> `auth.txt` está no `.gitignore` e nunca deve ser commitado.

### 3. Rodar o notebook (Colab)

Abra `playlist_communities.ipynb` no Google Colab. As seções **0 a 7** cobrem autenticação, fetch, estruturação do DataFrame e o Grafo Estrutural. As seções **8 e 9** dependem das letras.

### 4. Buscar letras (localmente)

O notebook exporta `data/playlist_data.csv`. Baixe esse arquivo, coloque na pasta `data/` e execute:

```bash
python fetch_lyrics.py
```

O script tenta o **Genius** como fonte primária e o **LRCLib** como fallback. Ao final, gera:

- `data/lyrics.csv` — letras coletadas
- `data/lyrics_report.csv` — relatório de cobertura (status, fonte, motivo de falha)

Suba os dois arquivos de volta para a pasta `data/` no Colab e continue o notebook a partir da seção 8.

---

## Metodologia

### Grafo Estrutural — Duração + Artista

$$
\text{score}(i, j) = 0.7 \times \left(1 - |\hat{d}_i - \hat{d}_j|\right) + 0.3 \times \mathbb{1}[A_i \cap A_j \neq \emptyset]
$$

Dois pesos equilibram duração normalizada (contínua, 70%) e artista em comum (binário, 30%). O campo `popularity` está indisponível no modo Development da API do Spotify desde novembro de 2024; a duração foi adotada como substituto.

### Grafo Lírico — Similaridade de Cosseno

$$
\text{score}(i, j) = \cos(\vec{e}_i, \vec{e}_j) = \frac{\vec{e}_i \cdot \vec{e}_j}{\|\vec{e}_i\|\,\|\vec{e}_j\|}
$$

Os embeddings são gerados pelo modelo multilíngue `paraphrase-multilingual-MiniLM-L12-v2` (Sentence Transformers, ~120 MB, roda em CPU). A escolha é justificada por suporte nativo a 50+ idiomas e pela captura de semântica — essencial para uma playlist com músicas em português e inglês.

### Detecção de Comunidades

Ambos os grafos usam o algoritmo de **Louvain** (`community_multilevel` do igraph), com arestas ponderadas pelo score de similaridade.

---

## Resultados

Análise realizada sobre uma playlist com **166 faixas** e **49 artistas**.

| Métrica              | Grafo Estrutural | Grafo Lírico |
| --------------------- | ---------------- | ------------- |
| Arestas               | 809              | 762           |
| Densidade             | 0.0591           | 0.0556        |
| Grau médio           | 9.75             | 9.18          |
| **Comunidades** | **8**      | **13**  |

A diferença central está no número de comunidades: a métrica estrutural agrupa de forma mais coesa (8 grupos, fortemente influenciados pela identidade de formato de cada artista), enquanto a métrica lírica fragmenta mais (13 grupos), revelando nichos semânticos que a duração sozinha não captura.

**Conclusão:** a playlist é editorialmente coesa, mas liricamente rica e variada — o que pode ser exatamente o que a torna interessante.

---

## Legado

A pasta `legacy/` contém a primeira fase do projeto, desenvolvida em Python puro com módulos separados (`access.py`, `auth.py`, `dataframe.py`, `graph.py`). Essa abordagem foi abandonada em favor do Jupyter Notebook, que permitiu desenvolvimento iterativo, visualizações inline e integração direta com o Colab. O código legado é mantido para registro histórico.

---

## Referências

- Blondel, V. D. et al. (2008). *Fast unfolding of communities in large networks*. Journal of Statistical Mechanics.
- Reimers, N. & Gurevych, I. (2019). *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks*. EMNLP.
- Fruchterman, T. M. J. & Reingold, E. M. (1991). *Graph drawing by force-directed placement*. Software: Practice and Experience.
- [Spotify Web API Reference](https://developer.spotify.com/documentation/web-api)
- [python-igraph Documentation](https://python.igraph.org/en/stable/)
- [Sentence Transformers](https://www.sbert.net/)
- [LyricsGenius](https://lyricsgenius.readthedocs.io/)
- [LRCLib](https://lrclib.net/)
