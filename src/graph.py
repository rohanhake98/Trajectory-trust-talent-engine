import math
from typing import Iterable

import networkx as nx

from ingest import CandidateModel
from normalize import normalize_title


def build_career_graph(candidates: Iterable[CandidateModel]) -> nx.DiGraph:
    """Builds a directed career transition graph from candidate career histories.

    Weights are based on transition frequencies. High transition frequency -> lower path cost.
    """
    G = nx.DiGraph()
    for candidate in candidates:
        # Sort career history chronologically by start date to trace career moves
        history = sorted(candidate.career_history, key=lambda x: x.start_date)
        normalized_titles = [normalize_title(job.title) for job in history]

        # Add directed edges for sequential job title transitions
        for i in range(len(normalized_titles) - 1):
            u = normalized_titles[i]
            v = normalized_titles[i + 1]
            if u == v:  # Ignore self-loops (retaining same canonical title)
                continue
            if G.has_edge(u, v):
                G[u][v]["weight"] += 1
            else:
                G.add_edge(u, v, weight=1)

    # Calculate path cost as the inverse of frequency
    for u, v, d in G.edges(data=True):
        d["cost"] = 1.0 / d["weight"]

    return G


def get_transition_score(
    G: nx.DiGraph, start_title: str, target_title: str, gamma: float = 0.5
) -> float:
    """Computes career transition path suitability using shortest path cost on graph.

    Decays exponentially using the cost of transition moves. Range: [0.0, 1.0]
    """
    start = normalize_title(start_title)
    target = normalize_title(target_title)

    if start == target:
        return 1.0

    if not G.has_node(start) or not G.has_node(target):
        return 0.0

    try:
        # Compute shortest path cost based on edge transition weights
        cost = nx.shortest_path_length(G, source=start, target=target, weight="cost")
        # Scale to [0, 1] using exponential decay
        return math.exp(-gamma * cost)
    except nx.NetworkXNoPath:
        return 0.0
