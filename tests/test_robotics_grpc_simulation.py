import pytest

from ai.protos import robotics_pb2
from ai.robotics_services import DemoRoboticFleetService


class AbortContext:
    def abort(self, code, detail):
        raise RuntimeError(f"{code.name}: {detail}")


def test_navigation_targets_registered_robot_not_zone_id():
    service = DemoRoboticFleetService()
    service.RegisterRobot(robotics_pb2.RobotIdentity(robot_id="rover-1"), None)
    request = robotics_pb2.NavigationCommand(
        command_id="nav-1",
        zone_id="zone-7",
    )
    request.target.destination.CopyFrom(robotics_pb2.Coordinate3D(x=3, y=4, z=0))

    result = service.NavigateTo(request, AbortContext())

    assert result.command_id == "nav-1"
    assert result.current_position.x == 3
    assert service.positions["rover-1"].y == 4
    assert "zone-7" not in service.positions


def test_navigation_rejects_missing_robot_registration():
    service = DemoRoboticFleetService()
    request = robotics_pb2.NavigationCommand(command_id="nav-2")

    with pytest.raises(RuntimeError, match="No robot is registered"):
        service.NavigateTo(request, AbortContext())
