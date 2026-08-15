"""
Day 73 starter: scaffold for extending the 3D scene and simulation connectors.
This script seeds a couple of virtual assets and prints a quick summary.
"""
from backend.database import init_db, SessionLocal
from backend import crud
from backend import models_scene

# try to use requests for HTTP seeding; fall back to urllib if unavailable
try:
    import requests  # type: ignore
except Exception:
    requests = None


def seed_entities(db):
    # Ensure related model modules are imported so SQLAlchemy can resolve relationship names
    try:
        import backend.models.environmental as _env_mod  # noqa: F401
    except Exception:
        pass
    demo = [
        {
            "name": "Tractor Alpha",
            "type": "robot",
            "x": 12.5,
            "y": 3.2,
            "z": 0.0,
            "rotation": 45.0,
            "state": {"status": "idle"},
        },
        {
            "name": "Irrigation Pump 1",
            "type": "pump",
            "x": -4.0,
            "y": 8.1,
            "z": 0.0,
            "rotation": 0.0,
            "state": {"running": False},
        },
        {
            "name": "Soil Sensor A",
            "type": "sensor",
            "x": 0.5,
            "y": -2.2,
            "z": 0.0,
            "rotation": 0.0,
            "state": {"moisture": 42},
        },
    ]

    created = []
    for item in demo:
        ent = models_scene.SceneEntity(
            name=item["name"],
            type=item["type"],
            x=item["x"],
            y=item["y"],
            z=item["z"],
            rotation=item["rotation"],
            state=item.get("state", {}),
        )
        db.add(ent)
        db.commit()
        db.refresh(ent)
        created.append(ent)
        # best-effort broadcast: import service lazily to avoid importing socketio at module import time
        try:
            from backend.services import scene as scene_service
            import asyncio

            try:
                asyncio.get_event_loop().run_until_complete(
                    scene_service.broadcast_entity_update(
                        {
                            "id": ent.id,
                            "name": ent.name,
                            "type": ent.type,
                            "x": ent.x,
                            "y": ent.y,
                            "z": ent.z,
                            "rotation": ent.rotation,
                            "state": ent.state or {},
                        }
                    )
                )
            except Exception:
                # if runtime loop or broadcast fails, ignore and continue
                pass
        except Exception:
            # scene service (and thereby socketio/aiohttp) may be unavailable in this environment
            pass

    return created


def seed_entities_via_api(base_url: str = "http://127.0.0.1:8000"):
    demo = [
        {
            "name": "Tractor Alpha",
            "type": "robot",
            "x": 12.5,
            "y": 3.2,
            "z": 0.0,
            "rotation": 45.0,
            "state": {"status": "idle"},
        },
        {
            "name": "Irrigation Pump 1",
            "type": "pump",
            "x": -4.0,
            "y": 8.1,
            "z": 0.0,
            "rotation": 0.0,
            "state": {"running": False},
        },
        {
            "name": "Soil Sensor A",
            "type": "sensor",
            "x": 0.5,
            "y": -2.2,
            "z": 0.0,
            "rotation": 0.0,
            "state": {"moisture": 42},
        },
    ]

    created = []
    for item in demo:
        try:
            if requests is not None:
                resp = requests.post(f"{base_url}/api/v1/scene/entities", json=item, timeout=3)
                resp.raise_for_status()
                created.append(resp.json())
            else:
                # fallback to urllib
                import json as _json
                from urllib.request import Request, urlopen

                req = Request(
                    f"{base_url}/api/v1/scene/entities",
                    data=_json.dumps(item).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )
                with urlopen(req, timeout=3) as r:
                    body = r.read()
                    created.append(_json.loads(body))
        except Exception as e:
            print(f"API seed failed for {item['name']}: {e}")
            # signal failure to caller
            return None

    return created


def run():
    init_db()
    # prefer POSTing to the running API so the app's routers and realtime broadcast are used
    api_created = None
    try:
        api_created = seed_entities_via_api("http://127.0.0.1:8000")
    except Exception:
        api_created = None

    if api_created:
        print(f"Seeded {len(api_created)} scene entities via API:")
        for e in api_created:
            # response may be dict
            if isinstance(e, dict):
                print(f" - {e.get('id')}: {e.get('name')} ({e.get('type')}) @ ({e.get('x')},{e.get('y')},{e.get('z')})")
            else:
                print(f" - {e}")
        return

    # fallback: seed directly into DB
    with SessionLocal() as db:
        created = seed_entities(db)
        print(f"Seeded {len(created)} scene entities:")
        for e in created:
            print(f" - {e.id}: {e.name} ({e.type}) @ ({e.x},{e.y},{e.z})")


if __name__ == '__main__':
    run()
