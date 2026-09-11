from backend.models.estate_hierarchy import Estate, EstateNode
from backend.routers.estate_hierarchy import THREE_ACRE_LAYOUT, THREE_ACRE_TEMPLATE


def test_three_acre_layout_measurement_and_template_shape(db):
    assert THREE_ACRE_LAYOUT["width_m"] * THREE_ACRE_LAYOUT["depth_m"] == 12150.0
    assert abs(THREE_ACRE_LAYOUT["area_acres"] - 3.0) < 0.01
    estate = Estate(tenant_id=1, name="Measured Estate", layout=THREE_ACRE_LAYOUT)
    db.add(estate)
    db.commit()
    assert len(THREE_ACRE_TEMPLATE) == 5
    assert db.query(EstateNode).filter_by(estate_id=estate.id).count() == 0