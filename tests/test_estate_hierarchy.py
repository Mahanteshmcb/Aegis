from backend.models.estate_hierarchy import Estate, EstateNode


def test_estate_hierarchy_parent_chain(db):
    estate = Estate(tenant_id=1, name="Innovation Estate")
    db.add(estate)
    db.commit()
    db.refresh(estate)

    zone = EstateNode(estate_id=estate.id, node_type="zone", name="Agricultural Biosphere")
    db.add(zone)
    db.commit()
    db.refresh(zone)

    building = EstateNode(
        estate_id=estate.id,
        parent_id=zone.id,
        node_type="building",
        name="R&D Laboratory",
    )
    db.add(building)
    db.commit()

    assert building.parent_id == zone.id
    assert db.query(EstateNode).filter_by(estate_id=estate.id).count() == 2
