import pandas as pd
import numpy as np
import igraph as ig
from typing import List, Tuple

# similaridade entre as músicas baseada em popularidade e artistas compartilhados
def compute_similarity(df: pd.DataFrame) -> np.ndarray:
    """
    calcula uma matriz de similaridade entre tracks baseada em popularidade e artistas compartilhados
    
    similaridade = 0.7 * (1 - |pop1 - pop2| / 100) + 0.3 * (1 se artistas comuns, 0 caso contrário)
    
    args:
        df: dataFrame com tracks
        
    returns:
        matriz de similaridade N×N
    """
    
    n = len(df)
    sim_matrix = np.zeros((n, n))
    
    print(f"calculando similaridade para {n} tracks...")
    
    # Normalizar popularidade
    pop_min = df['popularity'].min()
    pop_max = df['popularity'].max()
    if pop_max > pop_min:
        pop_normalized = (df['popularity'] - pop_min) / (pop_max - pop_min)
    else:
        pop_normalized = np.ones(n) * 0.5  # Se todas iguais, média
    
    # calculo da similaridade
    for i in range(n):
        for j in range(i, n):
            if i == j:
                sim_matrix[i][j] = 1.0
            else:
                # Similaridade de popularidade (inversa da diferença)
                pop_diff = abs(pop_normalized[i] - pop_normalized[j])
                sim_pop = 1.0 - pop_diff
                
                # Similaridade de artistas (1 se compartilhado, 0 caso contrário)
                artists_i = set(df.iloc[i]['artist_name'].split(', ')) if isinstance(df.iloc[i]['artist_name'], str) else set()
                artists_j = set(df.iloc[j]['artist_name'].split(', ')) if isinstance(df.iloc[j]['artist_name'], str) else set()
                sim_artists = 1.0 if artists_i & artists_j else 0.0
                
                # Score composto
                score = 0.7 * sim_pop + 0.3 * sim_artists
                
                # simetrizar
                sim_matrix[i][j] = score
                sim_matrix[j][i] = score
    
    print(f"matriz de similaridade computada")
    
    return sim_matrix

# define as arestas do grafo
def extract_edges(
    df: pd.DataFrame,
    sim_matrix: np.ndarray,
    threshold: float = 0.1,
    max_per_node: int = 10
) -> pd.DataFrame:
    """
    extrai arestas do grafo baseado na similaridade
    
    args:
        df: dataframe com tracks
        sim_matrix: matriz de similaridade N×N
        threshold: similaridade mínima (0-1)
        max_per_node: máximo de vizinhos por nó
        
    returns:
        dataframe com arestas (source, target, weight)
    """
    
    edges = []
    n = len(df)
    
    print(f"extraindo arestas (threshold={threshold})...")
    
    for i in range(n):
        sims = sim_matrix[i].copy()
        sims[i] = -1  # Ignorar self-loop
        
        # top n arestas
        top_indices = np.argsort(sims)[-max_per_node:]
        
        for j in top_indices:
            if j > i and sims[j] >= threshold:
                edges.append({
                    'source': df.iloc[i]['track_id'],
                    'source_name': df.iloc[i]['track_name'],
                    'target': df.iloc[j]['track_id'],
                    'target_name': df.iloc[j]['track_name'],
                    'weight': sims[j]
                })
    
    edges_df = pd.DataFrame(edges)
    print(f"{len(edges_df)} arestas extraídas")
    
    return edges_df

# montagem do grafo
def create_graph(df: pd.DataFrame, edges_df: pd.DataFrame) -> ig.Graph:
    """
    cria grafo igraph a partir dos dados
    
    args:
        df: dataframe com tracks
        edges_df: dataframe com arestas
        
    returns:
        objeto igraph.Graph
    """
    
    # mpeamento de ids
    track_to_idx = {track_id: idx for idx, track_id in enumerate(df['track_id'])}
    
    # converter arestas
    edges = []
    weights = []
    
    for _, row in edges_df.iterrows():
        src_idx = track_to_idx.get(row['source'])
        tgt_idx = track_to_idx.get(row['target'])
        
        if src_idx is not None and tgt_idx is not None:
            edges.append((src_idx, tgt_idx))
            weights.append(row['weight'])
    
    # grafo
    g = ig.Graph(len(df), edges=edges, directed=False)
    
    # atributos de vértices
    g.vs['id'] = df['track_id'].tolist()
    g.vs['name'] = df['track_name'].tolist()
    g.vs['artist'] = df['artist_name'].tolist()
    g.vs['popularity'] = df['popularity'].tolist()
    g.vs['_original_id'] = list(range(len(df)))  # Para comunidades
    
    # tamanho baseado em popularidade
    pop_norm = (df['popularity'] - df['popularity'].min()) / \
               (df['popularity'].max() - df['popularity'].min() + 1e-6)
    g.vs['size'] = (pop_norm * 20 + 5).tolist()
    
    # atributos de arestas
    if weights:
        g.es['weight'] = weights
    
    print(f"\ngrafo criado: {g.vcount()} nós, {g.ecount()} arestas")
    
    return g

# comunidades
def detect_communities(g: ig.Graph) -> List[List[int]]:
    """
    detecta comunidades no grafo usando Louvain
    
    args:
        g: grafo igraph
        
    returns:
        lista de comunidades
    """
    
    if g.ecount() == 0:
        print("grafo sem arestas - sem comunidades para detectar")
        return [[i] for i in range(g.vcount())]
    
    print(f"detectando comunidades...")
    
    if 'weight' in g.es.attributes():
        partition = g.community_multilevel(weights='weight')
    else:
        partition = g.community_multilevel()
    
    communities = [partition.subgraph(i).vs['_original_id'] for i in range(len(partition))]
    
    print(f"{len(communities)} comunidades detectadas")
    
    return communities

# visualização
def visualize_graph(g: ig.Graph, filepath: str = 'playlist_graph.png') -> None:
    """
    visualiza o grafo e salva como imagem
    
    args:
        g: grafo igraph
        filepath: caminho para salvar imagem
    """
    
    print(f"\nvisualizando grafo...")
    
    # layout
    layout = g.layout_fruchterman_reingold(niter=500)

    # cor uniforme por nó, já que a similaridade não depende de gêneros
    g.vs['color'] = ['#4ECDC4'] * g.vcount()
    
    # renderização
    try:
        ig.plot(
            g,
            filepath,
            layout=layout,
            vertex_size=g.vs['size'],
            vertex_color=g.vs['color'],
            vertex_label=None,
            edge_width=[w*2 for w in g.es['weight']] if 'weight' in g.es.attributes() else 1,
            edge_color='gray',
            edge_arrow_size=0,
            margin=50
        )
        print(f"grafo salvo em '{filepath}'")
    except AttributeError as e:
        print(f"não foi possível gerar o gráfico: {e}")
        print("instale pycairo ou cairocffi para habilitar a renderização de imagens")
    except Exception as e:
        print(f"erro ao gerar gráfico: {e}")