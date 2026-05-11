"""
Succession Planning Module for Syntropic Agriculture

Implements crop rotation, companion planting optimization, and seasonal planning
based on syntropic agriculture principles for the Aegis biosphere system.
"""

import logging
from enum import Enum
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class CropCategory(Enum):
    """Categories of crops based on syntropic agriculture function."""
    NITROGEN_FIXER = "nitrogen_fixer"  # N-fixing legumes
    DEEP_ROOTED = "deep_rooted"  # Tap-root crops for nutrient cycling
    DYNAMIC_ACCUMULATOR = "dynamic_accumulator"  # Nutrient miners
    SHADE_PROVIDER = "shade_provider"  # Upper story, protective
    GROUND_COVER = "ground_cover"  # Lower story, soil protection
    CASH_CROP = "cash_crop"  # Target harvest crops
    FODDER = "fodder"  # Animal feed/biomass
    HERB_MEDICINAL = "herb_medicinal"  # Medicinal and aromatic


class SoilImpact(Enum):
    """Impact of crops on soil health."""
    HEAVILY_DEPLETES = -2  # Nitrogen, phosphorus heavy users
    MODERATELY_DEPLETES = -1  # Standard crops
    NEUTRAL = 0  # Minimal impact
    MODERATELY_ENRICHES = 1  # N-fixers, partial accumulators
    HEAVILY_ENRICHES = 2  # Deep-rooted nutrient miners


@dataclass
class CropProfile:
    """Profile of a crop for succession planning."""
    crop_id: str
    crop_name: str
    category: CropCategory
    soil_impact: SoilImpact
    preferred_season: str  # "spring", "summer", "fall", "winter"
    companion_crops: List[str]  # Beneficial companion crop IDs
    incompatible_crops: List[str]  # Crops to avoid nearby
    min_rotation_years: int  # Minimum years before replanting same location
    yield_potential: float  # Relative yield 0-1
    water_requirements: str  # "low", "medium", "high"
    temperature_range: Tuple[int, int]  # Min/max optimal temperature


@dataclass
class RotationPlan:
    """A complete crop rotation plan for a zone."""
    zone_id: str
    plan_id: str
    crops_sequence: List[str]  # Ordered sequence of crop IDs
    years: int  # Length of rotation cycle in years
    start_date: datetime
    soil_health_projection: float  # Expected soil health 0-1
    predicted_yield: float  # Expected combined yield
    biodiversity_score: float  # Genetic diversity 0-1


@dataclass
class CompanionshipScore:
    """Scoring for companion planting compatibility."""
    crop_a: str
    crop_b: str
    compatibility: float  # -1 (incompatible) to 1 (highly compatible)
    reason: str


class SuccessionPlanner:
    """
    Orchestrates crop succession planning for syntropic agriculture.
    
    Implements algorithms for:
    - Crop rotation based on soil impacts
    - Companion planting optimization
    - Seasonal planning and scheduling
    """
    
    def __init__(self):
        """Initialize the succession planner."""
        self.crop_profiles: Dict[str, CropProfile] = {}
        self.rotation_history: Dict[str, List[Tuple[str, datetime]]] = defaultdict(list)
        logger.info("🌱 Succession Planner initialized")
    
    def register_crop(self, profile: CropProfile) -> None:
        """Register a crop profile for planning."""
        self.crop_profiles[profile.crop_id] = profile
        logger.debug(f"Registered crop: {profile.crop_name}")
    
    def calculate_companionship_score(self, crop_a: str, crop_b: str) -> CompanionshipScore:
        """
        Calculate companionship score between two crops.
        
        Considers:
        - Explicit companion/incompatible lists
        - Functional categories (nitrogen fixers with heavy users)
        - Soil impact compatibility
        """
        if crop_a not in self.crop_profiles or crop_b not in self.crop_profiles:
            raise ValueError(f"Unknown crop: {crop_a} or {crop_b}")
        
        profile_a = self.crop_profiles[crop_a]
        profile_b = self.crop_profiles[crop_b]
        
        # Base compatibility
        if crop_b in profile_a.incompatible_crops:
            compatibility = -1.0
            reason = "Explicitly incompatible"
        elif crop_b in profile_a.companion_crops:
            compatibility = 1.0
            reason = "Explicitly companionable"
        else:
            compatibility = 0.0
            reason = "Neutral relationship"
        
        # Functional synergies
        # N-fixers benefit heavy users
        if profile_a.category == CropCategory.NITROGEN_FIXER:
            if profile_b.soil_impact == SoilImpact.HEAVILY_DEPLETES:
                compatibility += 0.3
                reason = f"{reason} + N-fixer supports heavy feeder"
        
        # Deep-rooted with ground cover
        if profile_a.category == CropCategory.DEEP_ROOTED:
            if profile_b.category == CropCategory.GROUND_COVER:
                compatibility += 0.2
                reason = f"{reason} + Deep-root and ground cover synergy"
        
        # Shade provider with shade-tolerant crops
        if profile_a.category == CropCategory.SHADE_PROVIDER:
            if profile_b.category in [CropCategory.SHADE_PROVIDER, CropCategory.GROUND_COVER]:
                compatibility += 0.2
                reason = f"{reason} + Shade provider synergy"
        
        compatibility = max(-1.0, min(1.0, compatibility))
        
        return CompanionshipScore(
            crop_a=crop_a,
            crop_b=crop_b,
            compatibility=compatibility,
            reason=reason
        )
    
    def generate_rotation_sequence(
        self,
        zone_id: str,
        years: int = 3,
        initial_crop: Optional[str] = None,
        soil_health: float = 0.5
    ) -> RotationPlan:
        """
        Generate an optimal crop rotation sequence for a zone.
        
        Algorithm:
        1. Start with soil health state
        2. Identify crops that match current soil state
        3. Alternate between soil-depleting and soil-enriching crops
        4. Maximize diversity and yield
        """
        if not self.crop_profiles:
            raise ValueError("No crops registered. Use register_crop() first.")
        
        sequence = []
        current_soil_health = soil_health
        annual_yield = 0.0
        
        # Start with initial crop if provided
        if initial_crop:
            if initial_crop in self.crop_profiles:
                sequence.append(initial_crop)
            else:
                raise ValueError(f"Unknown initial crop: {initial_crop}")
        
        # Generate remaining crops in sequence
        remaining_years = years - len(sequence)
        used_crops: Set[str] = set(sequence)
        
        for year in range(remaining_years):
            # Find best next crop
            best_crop = None
            best_score = -999
            
            for crop_id, profile in self.crop_profiles.items():
                # Skip if same as last crop (no consecutive repetition)
                if sequence and crop_id == sequence[-1]:
                    continue
                
                # Skip recently used crops (rotation requirement)
                if crop_id in used_crops:
                    # Check minimum rotation years
                    history = self.rotation_history[zone_id]
                    last_use = next((dt for cid, dt in reversed(history) if cid == crop_id), None)
                    if last_use and (datetime.now() - last_use).days < profile.min_rotation_years * 365:
                        continue
                
                # Calculate suitability score
                score = self._calculate_crop_suitability(
                    profile, current_soil_health, sequence
                )
                
                if score > best_score:
                    best_score = score
                    best_crop = crop_id
            
            if best_crop:
                sequence.append(best_crop)
                used_crops.add(best_crop)
                
                # Update soil health based on crop impact
                impact_value = self.crop_profiles[best_crop].soil_impact.value
                current_soil_health = max(0.0, min(1.0, current_soil_health + impact_value * 0.1))
                annual_yield += self.crop_profiles[best_crop].yield_potential / years
        
        # Calculate plan metrics
        soil_projection = current_soil_health
        biodiversity = self._calculate_biodiversity(sequence)
        
        plan = RotationPlan(
            zone_id=zone_id,
            plan_id=f"rot_{zone_id}_{datetime.now().timestamp()}",
            crops_sequence=sequence,
            years=years,
            start_date=datetime.now(),
            soil_health_projection=soil_projection,
            predicted_yield=annual_yield,
            biodiversity_score=biodiversity
        )
        
        logger.info(
            f"📋 Generated {years}-year rotation for {zone_id}: "
            f"{' → '.join(sequence)} "
            f"(soil health: {soil_projection:.2f}, biodiversity: {biodiversity:.2f})"
        )
        
        return plan
    
    def _calculate_crop_suitability(
        self,
        profile: CropProfile,
        soil_health: float,
        previous_crops: List[str]
    ) -> float:
        """Calculate suitability score for a crop given current conditions."""
        score = 0.0
        
        # Soil health matching
        if profile.category == CropCategory.NITROGEN_FIXER:
            score += 0.3 if soil_health < 0.6 else -0.2
        elif profile.soil_impact == SoilImpact.HEAVILY_DEPLETES:
            score += 0.3 if soil_health > 0.7 else -0.3
        else:
            score += 0.1  # Neutral crops always acceptable
        
        # Companion planting with previous crops
        for prev_crop in previous_crops[-2:]:  # Consider last 2 crops
            compatibility = self.calculate_companionship_score(prev_crop, profile.crop_id).compatibility
            score += compatibility * 0.2
        
        # Yield potential
        score += profile.yield_potential * 0.2
        
        # Diversity bonus (less used)
        used_count = sum(1 for c in previous_crops if c == profile.crop_id)
        score += (1.0 / (used_count + 1)) * 0.1
        
        return score
    
    def _calculate_biodiversity(self, crop_sequence: List[str]) -> float:
        """Calculate biodiversity score for a crop sequence."""
        if not crop_sequence:
            return 0.0
        
        unique_crops = len(set(crop_sequence))
        total_crops = len(crop_sequence)
        
        # Diversity ratio (higher = more diverse)
        diversity_ratio = unique_crops / total_crops if total_crops > 0 else 0.0
        
        # Category diversity
        categories = set()
        for crop_id in crop_sequence:
            if crop_id in self.crop_profiles:
                categories.add(self.crop_profiles[crop_id].category)
        
        category_diversity = len(categories) / len(CropCategory)
        
        # Weighted biodiversity score
        biodiversity = (diversity_ratio * 0.6) + (category_diversity * 0.4)
        
        return biodiversity
    
    def generate_seasonal_schedule(
        self,
        zone_id: str,
        rotation_plan: RotationPlan,
        start_month: int = 3  # March
    ) -> Dict[str, Dict[str, str]]:
        """
        Generate seasonal planting schedule for a rotation plan.
        
        Returns schedule mapping: {year: {crop_id: season}}
        """
        schedule = {}
        season_months = {
            "spring": [3, 4, 5],
            "summer": [6, 7, 8],
            "fall": [9, 10, 11],
            "winter": [12, 1, 2]
        }
        
        current_month = start_month
        
        for year, crop_id in enumerate(rotation_plan.crops_sequence):
            if crop_id not in self.crop_profiles:
                continue
            
            profile = self.crop_profiles[crop_id]
            preferred_season = profile.preferred_season
            
            # Try to match preferred season
            preferred_months = season_months.get(preferred_season, [current_month])
            if current_month not in preferred_months:
                current_month = preferred_months[0]
            
            if year not in schedule:
                schedule[year] = {}
            
            schedule[year][crop_id] = preferred_season
            current_month = (current_month % 12) + 3  # Move to next quarter
        
        logger.info(f"📅 Generated seasonal schedule for {zone_id}")
        return schedule
    
    def record_crop_history(self, zone_id: str, crop_id: str) -> None:
        """Record when a crop was planted in a zone."""
        self.rotation_history[zone_id].append((crop_id, datetime.now()))
        logger.debug(f"Recorded crop {crop_id} in zone {zone_id}")
    
    def get_optimal_companions(self, crop_id: str, top_n: int = 5) -> List[Tuple[str, float]]:
        """Get top N companion crops for a given crop."""
        if crop_id not in self.crop_profiles:
            raise ValueError(f"Unknown crop: {crop_id}")
        
        companions = []
        for other_id in self.crop_profiles:
            if other_id != crop_id:
                score = self.calculate_companionship_score(crop_id, other_id).compatibility
                companions.append((other_id, score))
        
        return sorted(companions, key=lambda x: x[1], reverse=True)[:top_n]
    
    def validate_rotation_plan(self, plan: RotationPlan) -> Tuple[bool, List[str]]:
        """
        Validate a rotation plan for feasibility and best practices.
        
        Checks:
        - No immediate re-planting of same crop
        - Minimum rotation requirements met
        - Seasonal alignment
        - Diversity targets
        """
        issues = []
        
        # Check for consecutive crop repetition
        for i in range(len(plan.crops_sequence) - 1):
            if plan.crops_sequence[i] == plan.crops_sequence[i + 1]:
                issues.append(f"Crop {plan.crops_sequence[i]} cannot be planted consecutively")
        
        # Check minimum rotation years
        for crop_id in set(plan.crops_sequence):
            count = plan.crops_sequence.count(crop_id)
            if crop_id in self.crop_profiles:
                min_years = self.crop_profiles[crop_id].min_rotation_years
                spacing = plan.years / count if count > 0 else 0
                if spacing < min_years:
                    issues.append(
                        f"Crop {crop_id} spacing ({spacing:.1f} years) "
                        f"less than minimum ({min_years} years)"
                    )
        
        # Check biodiversity
        if plan.biodiversity_score < 0.5:
            issues.append(f"Low biodiversity score: {plan.biodiversity_score:.2f}")
        
        is_valid = len(issues) == 0
        
        if is_valid:
            logger.info(f"✅ Rotation plan {plan.plan_id} is valid")
        else:
            logger.warning(f"⚠️ Rotation plan {plan.plan_id} has issues: {issues}")
        
        return is_valid, issues
