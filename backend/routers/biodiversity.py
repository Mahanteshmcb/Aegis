"""Biodiversity API routes for Day 54.

Expose a simple optimizer endpoint that suggests species mixes for a zone.
"""
from fastapi import APIRouter, Depends
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.dependencies import get_db
from backend.models_db import BiologicalSpecies
from ai.biodiversity_optimization import optimize_diversity

router = APIRouter(prefix="/api/v1/biodiversity", tags=["biodiversity"])


@router.get('/optimize')
async def optimize(zone_id: Optional[int] = None, slots: int = 10, db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    # For now ignore zone suitability and fetch candidate species
    species = db.query(BiologicalSpecies).limit(200).all()
    species_list = []
    for s in species:
        species_list.append({
            'id': s.id,
            'scientific_name': s.scientific_name,
            'common_name': s.common_name,
            'family': s.family,
            'score': 1.0,
        })

    selected = optimize_diversity(species_list, slots=slots)
    return selected
