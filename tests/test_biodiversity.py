from ai.biodiversity_optimization import optimize_diversity


def test_optimize_diversity_basic():
    species = [
        {'id': 1, 'scientific_name': 'A', 'family': 'F1', 'score': 1.0},
        {'id': 2, 'scientific_name': 'B', 'family': 'F2', 'score': 0.9},
        {'id': 3, 'scientific_name': 'C', 'family': 'F1', 'score': 0.8},
    ]

    selected = optimize_diversity(species, slots=2)
    assert len(selected) == 2
    families = {s['family'] for s in selected}
    assert len(families) >= 1
