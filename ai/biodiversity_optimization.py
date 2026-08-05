"""Simple biodiversity optimization helpers for Day 54.

Provides a naive optimizer that suggests species mixes to maximize taxonomic
diversity given slot constraints and environmental suitability.
"""
from typing import List, Dict, Any
from collections import defaultdict

def optimize_diversity(species_list: List[Dict[str, Any]], slots: int = 10) -> List[Dict[str, Any]]:
    """Pick species to maximize family-level diversity, preferring species
    with broader environmental tolerances.

    species_list: list of species dicts with keys: id, scientific_name, family, score (optional)
    returns list of selected species dicts
    """
    if not species_list or slots <= 0:
        return []

    # score fallback
    for s in species_list:
        s.setdefault('score', 1.0)

    # Group by family and pick top-scoring species from each family first
    families = defaultdict(list)
    for s in species_list:
        families[s.get('family') or 'unknown'].append(s)

    # sort species within family by score desc
    for fam in families:
        families[fam].sort(key=lambda x: x.get('score', 1.0), reverse=True)

    selected = []

    # Round-robin pick one from each family until slots exhausted
    fam_keys = list(families.keys())
    idx = 0
    while len(selected) < slots and fam_keys:
        fam = fam_keys[idx % len(fam_keys)]
        if families[fam]:
            candidate = families[fam].pop(0)
            selected.append(candidate)
        else:
            fam_keys.remove(fam)
            idx -= 1
        idx += 1

    # If still slots left, fill with remaining highest-score species
    if len(selected) < slots:
        leftover = []
        for fam in families:
            leftover.extend(families[fam])
        leftover.sort(key=lambda x: x.get('score', 1.0), reverse=True)
        needed = slots - len(selected)
        selected.extend(leftover[:needed])

    return selected
