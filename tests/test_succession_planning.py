"""
Tests for Succession Planning Module

Validates crop rotation, companion planting optimization, and seasonal planning.
"""

import pytest
from datetime import datetime, timedelta

from ai.succession_planner import (
    SuccessionPlanner, CropProfile, CropCategory, SoilImpact,
    CompanionshipScore, RotationPlan
)


class TestCropRegistration:
    """Test crop profile registration."""
    
    @pytest.fixture
    def planner(self):
        """Create a succession planner instance."""
        return SuccessionPlanner()
    
    def test_register_crop(self, planner):
        """Test registering a single crop."""
        profile = CropProfile(
            crop_id="tomato_001",
            crop_name="Tomato",
            category=CropCategory.CASH_CROP,
            soil_impact=SoilImpact.MODERATELY_DEPLETES,
            preferred_season="summer",
            companion_crops=["basil", "carrot"],
            incompatible_crops=["brassica"],
            min_rotation_years=2,
            yield_potential=0.8,
            water_requirements="high",
            temperature_range=(20, 28)
        )
        
        planner.register_crop(profile)
        
        assert "tomato_001" in planner.crop_profiles
        assert planner.crop_profiles["tomato_001"].crop_name == "Tomato"
        assert planner.crop_profiles["tomato_001"].category == CropCategory.CASH_CROP
    
    def test_register_multiple_crops(self, planner):
        """Test registering multiple crops."""
        crops = [
            CropProfile(
                crop_id=f"crop_{i}",
                crop_name=f"Crop {i}",
                category=CropCategory.NITROGEN_FIXER,
                soil_impact=SoilImpact.HEAVILY_ENRICHES,
                preferred_season="spring",
                companion_crops=[],
                incompatible_crops=[],
                min_rotation_years=1,
                yield_potential=0.6,
                water_requirements="medium",
                temperature_range=(15, 25)
            )
            for i in range(5)
        ]
        
        for crop in crops:
            planner.register_crop(crop)
        
        assert len(planner.crop_profiles) == 5


class TestCompanionPlanting:
    """Test companion planting optimization."""
    
    @pytest.fixture
    def planner_with_crops(self):
        """Create planner with test crops."""
        planner = SuccessionPlanner()
        
        # Register test crops
        planner.register_crop(CropProfile(
            crop_id="nitrogen_fixer",
            crop_name="Legume",
            category=CropCategory.NITROGEN_FIXER,
            soil_impact=SoilImpact.HEAVILY_ENRICHES,
            preferred_season="spring",
            companion_crops=["heavy_feeder"],
            incompatible_crops=[],
            min_rotation_years=1,
            yield_potential=0.7,
            water_requirements="medium",
            temperature_range=(15, 25)
        ))
        
        planner.register_crop(CropProfile(
            crop_id="heavy_feeder",
            crop_name="Tomato",
            category=CropCategory.CASH_CROP,
            soil_impact=SoilImpact.HEAVILY_DEPLETES,
            preferred_season="summer",
            companion_crops=["nitrogen_fixer"],
            incompatible_crops=[],
            min_rotation_years=2,
            yield_potential=0.8,
            water_requirements="high",
            temperature_range=(20, 28)
        ))
        
        planner.register_crop(CropProfile(
            crop_id="deep_root",
            crop_name="Alfalfa",
            category=CropCategory.DEEP_ROOTED,
            soil_impact=SoilImpact.MODERATELY_ENRICHES,
            preferred_season="spring",
            companion_crops=[],
            incompatible_crops=[],
            min_rotation_years=2,
            yield_potential=0.6,
            water_requirements="low",
            temperature_range=(15, 25)
        ))
        
        return planner
    
    def test_companion_score_beneficial(self, planner_with_crops):
        """Test companionship score for beneficial pairing."""
        score = planner_with_crops.calculate_companionship_score(
            "nitrogen_fixer", "heavy_feeder"
        )
        
        assert isinstance(score, CompanionshipScore)
        assert score.crop_a == "nitrogen_fixer"
        assert score.crop_b == "heavy_feeder"
        assert score.compatibility > 0.5  # Should be high compatibility
    
    def test_get_optimal_companions(self, planner_with_crops):
        """Test getting optimal companions for a crop."""
        companions = planner_with_crops.get_optimal_companions("heavy_feeder", top_n=2)
        
        assert len(companions) <= 2
        assert all(isinstance(c, tuple) and len(c) == 2 for c in companions)
        # Heavy feeder should have high compatibility with nitrogen fixer
        assert companions[0][1] > 0  # Positive compatibility


class TestRotationGeneration:
    """Test crop rotation sequence generation."""
    
    @pytest.fixture
    def planner_with_crops(self):
        """Create planner with diverse test crops."""
        planner = SuccessionPlanner()
        
        # Register diverse crops
        planner.register_crop(CropProfile(
            crop_id="legume_1",
            crop_name="Beans",
            category=CropCategory.NITROGEN_FIXER,
            soil_impact=SoilImpact.HEAVILY_ENRICHES,
            preferred_season="spring",
            companion_crops=[],
            incompatible_crops=[],
            min_rotation_years=1,
            yield_potential=0.7,
            water_requirements="medium",
            temperature_range=(15, 25)
        ))
        
        planner.register_crop(CropProfile(
            crop_id="cereal_1",
            crop_name="Wheat",
            category=CropCategory.CASH_CROP,
            soil_impact=SoilImpact.MODERATELY_DEPLETES,
            preferred_season="winter",
            companion_crops=[],
            incompatible_crops=[],
            min_rotation_years=2,
            yield_potential=0.8,
            water_requirements="medium",
            temperature_range=(5, 20)
        ))
        
        planner.register_crop(CropProfile(
            crop_id="accumulator_1",
            crop_name="Comfrey",
            category=CropCategory.DYNAMIC_ACCUMULATOR,
            soil_impact=SoilImpact.MODERATELY_ENRICHES,
            preferred_season="spring",
            companion_crops=[],
            incompatible_crops=[],
            min_rotation_years=1,
            yield_potential=0.5,
            water_requirements="medium",
            temperature_range=(10, 25)
        ))
        
        planner.register_crop(CropProfile(
            crop_id="cash_1",
            crop_name="Tomato",
            category=CropCategory.CASH_CROP,
            soil_impact=SoilImpact.HEAVILY_DEPLETES,
            preferred_season="summer",
            companion_crops=[],
            incompatible_crops=[],
            min_rotation_years=2,
            yield_potential=0.9,
            water_requirements="high",
            temperature_range=(20, 28)
        ))
        
        return planner
    
    def test_generate_3year_rotation(self, planner_with_crops):
        """Test generating a 3-year rotation plan."""
        plan = planner_with_crops.generate_rotation_sequence(
            zone_id="zone_001",
            years=3,
            soil_health=0.5
        )
        
        assert isinstance(plan, RotationPlan)
        assert plan.zone_id == "zone_001"
        assert len(plan.crops_sequence) == 3
        assert plan.years == 3
        assert plan.soil_health_projection >= 0.0
        assert plan.soil_health_projection <= 1.0
        assert plan.biodiversity_score >= 0.0
        assert plan.biodiversity_score <= 1.0
    
    def test_rotation_with_initial_crop(self, planner_with_crops):
        """Test rotation generation with specified initial crop."""
        plan = planner_with_crops.generate_rotation_sequence(
            zone_id="zone_002",
            years=3,
            initial_crop="legume_1",
            soil_health=0.4
        )
        
        assert plan.crops_sequence[0] == "legume_1"
        assert len(plan.crops_sequence) == 3
    
    def test_no_consecutive_repetition(self, planner_with_crops):
        """Test that crops aren't repeated consecutively."""
        plan = planner_with_crops.generate_rotation_sequence(
            zone_id="zone_003",
            years=5,
            soil_health=0.5
        )
        
        for i in range(len(plan.crops_sequence) - 1):
            assert plan.crops_sequence[i] != plan.crops_sequence[i + 1]


class TestSeasonalScheduling:
    """Test seasonal planting schedule generation."""
    
    @pytest.fixture
    def planner_with_crops(self):
        """Create planner with seasonal crop information."""
        planner = SuccessionPlanner()
        
        planner.register_crop(CropProfile(
            crop_id="spring_crop",
            crop_name="Peas",
            category=CropCategory.NITROGEN_FIXER,
            soil_impact=SoilImpact.MODERATELY_ENRICHES,
            preferred_season="spring",
            companion_crops=[],
            incompatible_crops=[],
            min_rotation_years=2,
            yield_potential=0.7,
            water_requirements="medium",
            temperature_range=(10, 20)
        ))
        
        planner.register_crop(CropProfile(
            crop_id="summer_crop",
            crop_name="Tomato",
            category=CropCategory.CASH_CROP,
            soil_impact=SoilImpact.MODERATELY_DEPLETES,
            preferred_season="summer",
            companion_crops=[],
            incompatible_crops=[],
            min_rotation_years=2,
            yield_potential=0.8,
            water_requirements="high",
            temperature_range=(20, 30)
        ))
        
        planner.register_crop(CropProfile(
            crop_id="fall_crop",
            crop_name="Kale",
            category=CropCategory.CASH_CROP,
            soil_impact=SoilImpact.MODERATELY_DEPLETES,
            preferred_season="fall",
            companion_crops=[],
            incompatible_crops=[],
            min_rotation_years=1,
            yield_potential=0.7,
            water_requirements="medium",
            temperature_range=(5, 20)
        ))
        
        return planner
    
    def test_generate_seasonal_schedule(self, planner_with_crops):
        """Test generating seasonal planting schedule."""
        rotation = planner_with_crops.generate_rotation_sequence(
            zone_id="zone_seasonal",
            years=3,
            soil_health=0.5
        )
        
        schedule = planner_with_crops.generate_seasonal_schedule(
            zone_id="zone_seasonal",
            rotation_plan=rotation,
            start_month=3  # March
        )
        
        assert isinstance(schedule, dict)
        assert len(schedule) == 3
        
        for year, crops in schedule.items():
            assert isinstance(year, int)
            assert isinstance(crops, dict)


class TestPlanValidation:
    """Test rotation plan validation."""
    
    @pytest.fixture
    def planner_with_crops(self):
        """Create planner with test crops."""
        planner = SuccessionPlanner()
        
        for i in range(4):
            planner.register_crop(CropProfile(
                crop_id=f"crop_{i}",
                crop_name=f"Crop {i}",
                category=CropCategory.CASH_CROP,
                soil_impact=SoilImpact.MODERATELY_DEPLETES,
                preferred_season="spring",
                companion_crops=[],
                incompatible_crops=[],
                min_rotation_years=2,
                yield_potential=0.7,
                water_requirements="medium",
                temperature_range=(15, 25)
            ))
        
        return planner
    
    def test_validate_valid_plan(self, planner_with_crops):
        """Test validation of a valid rotation plan."""
        plan = planner_with_crops.generate_rotation_sequence(
            zone_id="zone_valid",
            years=3,
            soil_health=0.5
        )
        
        is_valid, issues = planner_with_crops.validate_rotation_plan(plan)
        
        assert isinstance(is_valid, bool)
        assert isinstance(issues, list)
    
    def test_validate_low_biodiversity(self, planner_with_crops):
        """Test detection of low biodiversity."""
        # Create plan with low diversity
        plan = RotationPlan(
            zone_id="zone_low_div",
            plan_id="plan_low_div",
            crops_sequence=["crop_0", "crop_0"],  # Repeated crop
            years=2,
            start_date=datetime.now(),
            soil_health_projection=0.5,
            predicted_yield=0.6,
            biodiversity_score=0.3  # Low diversity
        )
        
        is_valid, issues = planner_with_crops.validate_rotation_plan(plan)
        
        # Should have issues
        assert len(issues) > 0


class TestBiodiversityCalculation:
    """Test biodiversity scoring."""
    
    @pytest.fixture
    def planner(self):
        """Create a succession planner instance."""
        planner = SuccessionPlanner()
        
        # Register crops with different categories
        categories = [
            CropCategory.NITROGEN_FIXER,
            CropCategory.CASH_CROP,
            CropCategory.DEEP_ROOTED,
            CropCategory.GROUND_COVER
        ]
        
        for i, category in enumerate(categories):
            planner.register_crop(CropProfile(
                crop_id=f"crop_{i}",
                crop_name=f"Crop {i}",
                category=category,
                soil_impact=SoilImpact.NEUTRAL,
                preferred_season="spring",
                companion_crops=[],
                incompatible_crops=[],
                min_rotation_years=1,
                yield_potential=0.7,
                water_requirements="medium",
                temperature_range=(15, 25)
            ))
        
        return planner
    
    def test_high_biodiversity_sequence(self, planner):
        """Test biodiversity score for diverse sequence."""
        sequence = ["crop_0", "crop_1", "crop_2", "crop_3"]
        biodiversity = planner._calculate_biodiversity(sequence)
        
        assert biodiversity > 0.5
        assert biodiversity <= 1.0
    
    def test_low_biodiversity_sequence(self, planner):
        """Test biodiversity score for low diversity sequence."""
        sequence = ["crop_0", "crop_0", "crop_0", "crop_0"]
        biodiversity = planner._calculate_biodiversity(sequence)
        
        assert biodiversity < 0.5
    
    def test_empty_sequence(self, planner):
        """Test biodiversity score for empty sequence."""
        sequence = []
        biodiversity = planner._calculate_biodiversity(sequence)
        
        assert biodiversity == 0.0
