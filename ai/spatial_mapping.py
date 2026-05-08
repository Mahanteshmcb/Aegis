"""
Aegis Spatial Mapping Algorithms

Day 33: 3D spatial algorithms for vertical crop layers (ground, mid-canopy, upper).
Provides collision detection, optimal positioning, and layer management for 3,000+ crop species.
"""

import math
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum


class VerticalLayer(Enum):
    """Vertical crop layers in the biosphere ecosystem."""
    GROUND = "ground"
    MID_CANOPY = "mid_canopy"
    UPPER = "upper"


@dataclass
class Coordinate3D:
    """3D coordinate system for spatial positioning."""
    x: float
    y: float
    z: float

    def distance_to(self, other: 'Coordinate3D') -> float:
        """Calculate Euclidean distance between two points."""
        return math.sqrt(
            (self.x - other.x) ** 2 +
            (self.y - other.y) ** 2 +
            (self.z - other.z) ** 2
        )

    def __add__(self, other: 'Coordinate3D') -> 'Coordinate3D':
        return Coordinate3D(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: 'Coordinate3D') -> 'Coordinate3D':
        return Coordinate3D(self.x - other.x, self.y - other.y, self.z - other.z)


@dataclass
class CropProfile:
    """Biological profile for spatial planning."""
    species_id: int
    scientific_name: str
    max_height_cm: float
    canopy_radius_cm: float
    vertical_layer: VerticalLayer
    companion_species: Set[int]
    antagonistic_species: Set[int]


@dataclass
class SpatialZone:
    """3D spatial zone boundaries."""
    zone_id: int
    min_x: float
    max_x: float
    min_y: float
    max_y: float
    min_z: float
    max_z: float
    supports_ground: bool = True
    supports_mid_canopy: bool = True
    supports_upper: bool = False


class SpatialMappingEngine:
    """
    Core spatial mapping engine for 3D crop positioning and collision detection.
    Handles vertical layer management and optimal placement algorithms.
    """

    def __init__(self):
        self.crop_profiles: Dict[int, CropProfile] = {}
        self.spatial_zones: Dict[int, SpatialZone] = {}
        self.occupied_positions: Dict[int, List[Coordinate3D]] = {}  # zone_id -> positions

    def register_crop_profile(self, profile: CropProfile) -> None:
        """Register a crop species profile for spatial planning."""
        self.crop_profiles[profile.species_id] = profile

    def register_spatial_zone(self, zone: SpatialZone) -> None:
        """Register a spatial zone for crop placement."""
        self.spatial_zones[zone.zone_id] = zone
        self.occupied_positions[zone.zone_id] = []

    def get_vertical_layer_bounds(self, zone: SpatialZone, layer: VerticalLayer) -> Tuple[float, float]:
        """
        Get the Z-coordinate bounds for a vertical layer within a zone.

        Returns:
            Tuple of (min_z, max_z) for the layer
        """
        zone_height = zone.max_z - zone.min_z

        if layer == VerticalLayer.GROUND:
            # Ground layer: 0-30% of zone height
            return (zone.min_z, zone.min_z + zone_height * 0.3)
        elif layer == VerticalLayer.MID_CANOPY:
            # Mid-canopy: 30-70% of zone height
            return (zone.min_z + zone_height * 0.3, zone.min_z + zone_height * 0.7)
        elif layer == VerticalLayer.UPPER:
            # Upper canopy: 70-100% of zone height
            return (zone.min_z + zone_height * 0.7, zone.max_z)
        else:
            raise ValueError(f"Unknown vertical layer: {layer}")

    def check_collision(self, zone_id: int, position: Coordinate3D,
                       canopy_radius: float, layer: VerticalLayer) -> bool:
        """
        Check if a crop placement would collide with existing crops.

        Args:
            zone_id: The spatial zone ID
            position: Proposed 3D position
            canopy_radius: Canopy radius in meters
            layer: Vertical layer for collision checking

        Returns:
            True if collision detected, False otherwise
        """
        if zone_id not in self.occupied_positions:
            return False

        zone = self.spatial_zones.get(zone_id)
        if not zone:
            return True  # Invalid zone

        # Get layer bounds
        layer_min_z, layer_max_z = self.get_vertical_layer_bounds(zone, layer)

        # Check if position is within layer bounds
        if not (layer_min_z <= position.z <= layer_max_z):
            return True  # Out of layer bounds

        # Check collisions with existing crops in same layer
        collision_distance = canopy_radius * 2  # Minimum distance between canopies

        for existing_pos in self.occupied_positions[zone_id]:
            # Only check collisions within the same vertical layer (±10cm tolerance)
            if abs(existing_pos.z - position.z) > 0.1:
                continue

            if position.distance_to(existing_pos) < collision_distance:
                return True  # Collision detected

        return False

    def find_optimal_position(self, zone_id: int, species_id: int,
                            preferred_position: Optional[Coordinate3D] = None) -> Optional[Coordinate3D]:
        """
        Find the optimal 3D position for a crop species in a zone.

        Uses companion planting rules and spatial optimization.
        """
        zone = self.spatial_zones.get(zone_id)
        profile = self.crop_profiles.get(species_id)

        if not zone or not profile:
            return None

        # Get layer bounds
        layer_min_z, layer_max_z = self.get_vertical_layer_bounds(zone, profile.vertical_layer)

        # Start with preferred position if provided
        if preferred_position:
            # Adjust Z to fit within layer
            adjusted_pos = Coordinate3D(
                preferred_position.x,
                preferred_position.y,
                (layer_min_z + layer_max_z) / 2  # Center of layer
            )

            if not self.check_collision(zone_id, adjusted_pos, profile.canopy_radius_cm / 100, profile.vertical_layer):
                return adjusted_pos

        # Grid search for optimal position
        grid_spacing = profile.canopy_radius_cm / 50  # Fine grid for precision

        for x in self._frange(zone.min_x, zone.max_x, grid_spacing):
            for y in self._frange(zone.min_y, zone.max_y, grid_spacing):
                # Try center of layer first
                z_center = (layer_min_z + layer_max_z) / 2
                position = Coordinate3D(x, y, z_center)

                if not self.check_collision(zone_id, position, profile.canopy_radius_cm / 100, profile.vertical_layer):
                    return position

        return None  # No suitable position found

    def validate_companion_planting(self, zone_id: int, species_id: int,
                                  nearby_species: List[int]) -> Dict[str, any]:
        """
        Validate companion planting relationships for a crop placement.

        Returns:
            Dict with compatibility score and recommendations
        """
        profile = self.crop_profiles.get(species_id)
        if not profile:
            return {"compatible": False, "score": 0, "issues": ["Unknown species"]}

        score = 50  # Base score
        issues = []
        recommendations = []

        for nearby_id in nearby_species:
            if nearby_id in profile.companion_species:
                score += 20
                recommendations.append(f"Good companion with species {nearby_id}")
            elif nearby_id in profile.antagonistic_species:
                score -= 30
                issues.append(f"Antagonistic relationship with species {nearby_id}")

        return {
            "compatible": score >= 40,
            "score": max(0, min(100, score)),
            "issues": issues,
            "recommendations": recommendations
        }

    def optimize_zone_layout(self, zone_id: int, crop_instances: List[Dict]) -> Dict[str, any]:
        """
        Optimize the spatial layout of crops in a zone for maximum yield and health.

        Args:
            zone_id: The spatial zone to optimize
            crop_instances: List of crop instance data

        Returns:
            Optimization results with new positions and scores
        """
        zone = self.spatial_zones.get(zone_id)
        if not zone:
            return {"success": False, "error": "Zone not found"}

        # Reset occupied positions for optimization
        self.occupied_positions[zone_id] = []

        optimized_positions = []
        total_score = 0

        for instance in crop_instances:
            species_id = instance["species_id"]
            profile = self.crop_profiles.get(species_id)

            if not profile:
                continue

            # Find optimal position
            optimal_pos = self.find_optimal_position(zone_id, species_id)

            if optimal_pos:
                # Check companion planting
                nearby_species = self._get_nearby_species(zone_id, optimal_pos, profile.canopy_radius_cm / 100)
                compatibility = self.validate_companion_planting(zone_id, species_id, nearby_species)

                # Record position
                self.occupied_positions[zone_id].append(optimal_pos)

                optimized_positions.append({
                    "instance_id": instance["id"],
                    "position": optimal_pos,
                    "compatibility_score": compatibility["score"],
                    "issues": compatibility["issues"]
                })

                total_score += compatibility["score"]
            else:
                optimized_positions.append({
                    "instance_id": instance["id"],
                    "position": None,
                    "error": "No suitable position found"
                })

        return {
            "success": True,
            "optimized_positions": optimized_positions,
            "average_compatibility_score": total_score / len(crop_instances) if crop_instances else 0,
            "zone_utilization": len(self.occupied_positions[zone_id]) / zone.max_capacity if zone.max_capacity else 0
        }

    def _get_nearby_species(self, zone_id: int, position: Coordinate3D, radius: float) -> List[int]:
        """Get species IDs of crops within a radius (for companion planting analysis)."""
        nearby = []
        # This would query the database in a real implementation
        # For now, return empty list as placeholder
        return nearby

    def _frange(self, start: float, stop: float, step: float):
        """Floating point range generator."""
        current = start
        while current < stop:
            yield current
            current += step


# Global spatial mapping engine instance
spatial_engine = SpatialMappingEngine()