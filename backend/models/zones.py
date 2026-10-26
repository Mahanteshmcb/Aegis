from backend.database import Base, Zone
from sqlalchemy import Column, String, Text, DateTime, JSON
from datetime import datetime

# Re-export the database Zone class with to_dict enhancement
# This ensures all services use the same Zone class reference
Zone.__module__ = __name__  # Help with module resolution

# Additional fields for the Zone model (already defined in database.Zone,
# but re-exported here for consistency and to_dict method)
coordinates = Column(JSON, default=lambda: {"x": 0.0, "y": 0.0, "z": 0.0})
asset_ratio = Column(String, default="1:1", nullable=False)
position_ratio = Column(String, default="50:50", nullable=False)
target_metrics = Column(JSON, default=dict)
created_at = Column(DateTime, default=datetime.utcnow)
updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Add to_dict method if not already present
if not hasattr(Zone, 'to_dict'):
    def to_dict(self):
        """Convert zone to dictionary for API responses."""
        base_dict = {
            "zone_id": self.zone_id,
            "name": self.name,
            "description": self.description,
        }
        return {**base_dict, **{
            "coordinates": self.coordinates,
            "asset_ratio": self.asset_ratio,
            "position_ratio": self.position_ratio,
            "target_metrics": self.target_metrics,
            "created_at": str(self.created_at) if self.created_at else None,
            "updated_at": str(self.updated_at) if self.updated_at else None,
        }}
    Zone.to_dict = to_dict

# Re-export from database for backward compatibility
__all__ = ["Zone"]
