"""
Succession Planning Router

REST API endpoints for crop rotation, companion planting, and seasonal planning.
Integrates the SuccessionPlanner algorithm engine with the Aegis backend.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.dependencies import get_db, get_current_user
from backend.models_db import (
    User, Tenant, SpatialZone, BiologicalSpecies,
    CropRotationPlan, SeasonalPlantingSchedule, CompanionPlanting, CropSuccessionHistory
)
from ai.succession_planner import (
    SuccessionPlanner, CropProfile, CropCategory, SoilImpact,
    CompanionshipScore, RotationPlan
)

router = APIRouter(prefix="/api/v1/succession", tags=["succession"])
logger = logging.getLogger(__name__)

# Global succession planner instance
planner = SuccessionPlanner()


@router.post("/register-crop")
def register_crop(
    tenant_id: int,
    species_id: int,
    category: str,
    soil_impact: int,
    preferred_season: str = "spring",
    companion_crops: List[str] = None,
    incompatible_crops: List[str] = None,
    min_rotation_years: int = 2,
    yield_potential: float = 0.7,
    water_requirements: str = "medium",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Register a crop profile in the succession planner.
    
    Parameters:
    - tenant_id: Tenant ID
    - species_id: BiologicalSpecies ID
    - category: Crop category (nitrogen_fixer, deep_rooted, etc.)
    - soil_impact: Impact on soil (-2 to 2)
    - preferred_season: Spring/Summer/Fall/Winter
    - companion_crops: List of compatible crop IDs
    - incompatible_crops: List of incompatible crop IDs
    - min_rotation_years: Minimum years before replanting
    - yield_potential: Relative yield (0-1)
    - water_requirements: low/medium/high
    """
    try:
        # Verify species exists
        species = db.query(BiologicalSpecies).filter(
            BiologicalSpecies.id == species_id
        ).first()
        if not species:
            raise HTTPException(status_code=404, detail="Species not found")
        
        # Convert strings to enums
        try:
            category_enum = CropCategory[category.upper()]
            soil_impact_enum = SoilImpact(soil_impact)
        except (KeyError, ValueError):
            raise HTTPException(status_code=400, detail="Invalid category or soil impact")
        
        # Create crop profile
        profile = CropProfile(
            crop_id=f"species_{species_id}",
            crop_name=species.common_name,
            category=category_enum,
            soil_impact=soil_impact_enum,
            preferred_season=preferred_season.lower(),
            companion_crops=companion_crops or [],
            incompatible_crops=incompatible_crops or [],
            min_rotation_years=min_rotation_years,
            yield_potential=yield_potential,
            water_requirements=water_requirements.lower(),
            temperature_range=(species.optimal_temp_min_c or 15, species.optimal_temp_max_c or 30)
        )
        
        # Register in planner
        planner.register_crop(profile)
        
        logger.info(f"✅ Registered crop: {species.common_name} for tenant {tenant_id}")
        
        return {
            "success": True,
            "message": f"Crop '{species.common_name}' registered successfully",
            "data": {"crop_id": profile.crop_id}
        }
    
    except Exception as e:
        logger.error(f"Error registering crop: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-rotation")
def generate_rotation_plan(
    tenant_id: int,
    spatial_zone_id: int,
    years: int = Query(3, ge=1, le=10),
    initial_crop: Optional[str] = None,
    soil_health: float = Query(0.5, ge=0.0, le=1.0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Generate an optimal crop rotation sequence for a spatial zone.
    
    Uses syntropic agriculture principles to balance:
    - Soil health restoration
    - Biodiversity
    - Yield optimization
    - Companion planting synergies
    
    Parameters:
    - tenant_id: Tenant ID
    - spatial_zone_id: SpatialZone ID
    - years: Length of rotation cycle (1-10)
    - initial_crop: Optional starting crop ID
    - soil_health: Current soil health (0-1)
    """
    try:
        # Verify spatial zone exists
        zone = db.query(SpatialZone).filter(
            SpatialZone.id == spatial_zone_id,
            SpatialZone.tenant_id == tenant_id
        ).first()
        if not zone:
            raise HTTPException(status_code=404, detail="Spatial zone not found")
        
        # Verify crops are registered
        if not planner.crop_profiles:
            raise HTTPException(
                status_code=400,
                detail="No crops registered. Register crops first using /register-crop"
            )
        
        # Generate rotation
        rotation = planner.generate_rotation_sequence(
            zone_id=f"zone_{spatial_zone_id}",
            years=years,
            initial_crop=initial_crop,
            soil_health=soil_health
        )
        
        # Save to database
        db_plan = CropRotationPlan(
            tenant_id=tenant_id,
            spatial_zone_id=spatial_zone_id,
            plan_name=f"Rotation Plan {datetime.now().strftime('%Y-%m-%d')}",
            description=f"{years}-year syntropic rotation",
            crop_sequence=rotation.crops_sequence,
            years=years,
            start_date=rotation.start_date,
            soil_health_projection=rotation.soil_health_projection,
            predicted_avg_yield=rotation.predicted_yield,
            biodiversity_score=rotation.biodiversity_score
        )
        db.add(db_plan)
        db.commit()
        db.refresh(db_plan)
        
        logger.info(
            f"📋 Generated {years}-year rotation for zone {spatial_zone_id}: "
            f"{' → '.join(rotation.crops_sequence)}"
        )
        
        return {
            "success": True,
            "message": "Rotation plan generated successfully",
            "plan_id": rotation.plan_id,
            "zone_id": f"zone_{spatial_zone_id}",
            "crops_sequence": rotation.crops_sequence,
            "years": years,
            "soil_health_projection": rotation.soil_health_projection,
            "predicted_yield": rotation.predicted_yield,
            "biodiversity_score": rotation.biodiversity_score
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating rotation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/companionship/{crop_a}/{crop_b}")
def check_companionship(
    crop_a: str,
    crop_b: str,
    tenant_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Calculate companionship score between two crops.
    
    Returns compatibility score (-1 to 1) and the reasoning.
    
    Parameters:
    - crop_a: First crop ID (species_ID format)
    - crop_b: Second crop ID (species_ID format)
    - tenant_id: Tenant ID for verification
    """
    try:
        # Calculate compatibility
        score = planner.calculate_companionship_score(crop_a, crop_b)
        
        logger.info(f"🤝 Companionship: {crop_a} + {crop_b} = {score.compatibility:.2f}")
        
        return {
            "success": True,
            "message": "Companionship score calculated",
            "crop_a": score.crop_a,
            "crop_b": score.crop_b,
            "compatibility": score.compatibility,
            "reason": score.reason
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error calculating companionship: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/companions/{crop_id}")
def get_best_companions(
    crop_id: str,
    top_n: int = Query(5, ge=1, le=20),
    tenant_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the top N best companion crops for a given crop.
    
    Sorted by compatibility score (highest first).
    
    Parameters:
    - crop_id: Crop ID to find companions for
    - top_n: Number of top companions to return
    - tenant_id: Tenant ID for verification
    """
    try:
        companions = planner.get_optimal_companions(crop_id, top_n)
        
        companion_data = [
            {"crop_id": cid, "compatibility_score": score}
            for cid, score in companions
        ]
        
        return {
            "success": True,
            "message": f"Found {len(companions)} companion crops",
            "data": {"companions": companion_data}
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting companions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/seasonal-schedule/{rotation_plan_id}")
def generate_seasonal_schedule(
    rotation_plan_id: int,
    start_month: int = Query(3, ge=1, le=12),
    tenant_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate seasonal planting schedule for a rotation plan.
    
    Maps each crop to optimal planting season and month.
    
    Parameters:
    - rotation_plan_id: CropRotationPlan ID
    - start_month: Starting month (1-12, default March=3)
    - tenant_id: Tenant ID for verification
    """
    try:
        # Fetch rotation plan
        db_plan = db.query(CropRotationPlan).filter(
            CropRotationPlan.id == rotation_plan_id,
            CropRotationPlan.tenant_id == tenant_id
        ).first()
        if not db_plan:
            raise HTTPException(status_code=404, detail="Rotation plan not found")
        
        # Create RotationPlan object for planner
        rotation = RotationPlan(
            zone_id=f"zone_{db_plan.spatial_zone_id}",
            plan_id=f"rot_{db_plan.id}",
            crops_sequence=db_plan.crop_sequence,
            years=db_plan.years,
            start_date=db_plan.start_date,
            soil_health_projection=db_plan.soil_health_projection,
            predicted_yield=db_plan.predicted_avg_yield,
            biodiversity_score=db_plan.biodiversity_score
        )
        
        # Generate schedule
        schedule = planner.generate_seasonal_schedule(
            zone_id=f"zone_{db_plan.spatial_zone_id}",
            rotation_plan=rotation,
            start_month=start_month
        )
        
        logger.info(f"📅 Generated seasonal schedule for plan {rotation_plan_id}")
        
        return {
            "success": True,
            "message": "Seasonal schedule generated",
            "data": {"schedule": schedule}
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-plan/{rotation_plan_id}")
def validate_rotation_plan(
    rotation_plan_id: int,
    tenant_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Validate a rotation plan for feasibility and best practices.
    
    Checks for:
    - No immediate crop repetition
    - Minimum rotation requirements
    - Seasonal alignment
    - Diversity targets
    
    Parameters:
    - rotation_plan_id: CropRotationPlan ID to validate
    - tenant_id: Tenant ID for verification
    """
    try:
        # Fetch rotation plan
        db_plan = db.query(CropRotationPlan).filter(
            CropRotationPlan.id == rotation_plan_id,
            CropRotationPlan.tenant_id == tenant_id
        ).first()
        if not db_plan:
            raise HTTPException(status_code=404, detail="Rotation plan not found")
        
        # Create RotationPlan object
        rotation = RotationPlan(
            zone_id=f"zone_{db_plan.spatial_zone_id}",
            plan_id=f"rot_{db_plan.id}",
            crops_sequence=db_plan.crop_sequence,
            years=db_plan.years,
            start_date=db_plan.start_date,
            soil_health_projection=db_plan.soil_health_projection,
            predicted_yield=db_plan.predicted_avg_yield,
            biodiversity_score=db_plan.biodiversity_score
        )
        
        # Validate
        is_valid, issues = planner.validate_rotation_plan(rotation)
        
        return {
            "success": is_valid,
            "message": "Rotation plan validation complete" if is_valid else "Validation issues found",
            "data": {
                "is_valid": is_valid,
                "issues": issues,
                "biodiversity_score": rotation.biodiversity_score,
                "soil_health_projection": rotation.soil_health_projection
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating plan: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plans/{spatial_zone_id}")
def list_rotation_plans(
    spatial_zone_id: int,
    tenant_id: int = Query(...),
    is_active: bool = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all rotation plans for a spatial zone.
    
    Parameters:
    - spatial_zone_id: SpatialZone ID
    - tenant_id: Tenant ID for verification
    - is_active: Filter by active/inactive plans (optional)
    """
    try:
        query = db.query(CropRotationPlan).filter(
            CropRotationPlan.spatial_zone_id == spatial_zone_id,
            CropRotationPlan.tenant_id == tenant_id
        )
        
        if is_active is not None:
            query = query.filter(CropRotationPlan.is_active == is_active)
        
        plans = query.all()
        
        plan_data = [
            {
                "id": p.id,
                "name": p.plan_name,
                "crops_sequence": p.crop_sequence,
                "years": p.years,
                "soil_health_projection": p.soil_health_projection,
                "biodiversity_score": p.biodiversity_score,
                "is_active": p.is_active,
                "is_approved": p.is_approved,
                "created_at": p.created_at.isoformat()
            }
            for p in plans
        ]
        
        return {
            "success": True,
            "message": f"Found {len(plans)} rotation plans",
            "data": {"plans": plan_data}
        }
    
    except Exception as e:
        logger.error(f"Error listing plans: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
