# Tests for Orchestration Engine
# Comprehensive testing of the Succession & Orchestration Engine

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from ai.orchestrator import (
    SuccessionOrchestrationEngine,
    SuccessionEvent,
    RoboticAction,
    OrchestrationTrigger,
    DecisionContext,
    SuccessionPlan
)
from ai.vryndara_connector import VryndaraConnector
from ai.robotics_connector import RoboticsConnector


class TestSuccessionOrchestrationEngine:
    """Test suite for the Succession & Orchestration Engine."""

    @pytest_asyncio.fixture
    async def setup_engine(self):
        """Set up test orchestration engine with mocked connectors."""
        vryndara_mock = AsyncMock(spec=VryndaraConnector)
        robotics_mock = AsyncMock(spec=RoboticsConnector)

        engine = SuccessionOrchestrationEngine(vryndara_mock, robotics_mock)

        # Mock the spatial engine
        with patch('ai.orchestrator.spatial_engine') as spatial_mock:
            spatial_mock.find_optimal_position.return_value = type('Coord', (), {'x': 5.0, 'y': 5.0, 'z': 1.0})()
            spatial_mock.get_zone_utilization.return_value = {'utilization': 0.7}

            yield engine, vryndara_mock, robotics_mock, spatial_mock

    @pytest.mark.asyncio
    async def test_initialization(self, setup_engine):
        """Test engine initialization with zone configurations."""
        engine, _, _, _ = setup_engine

        zone_configs = [
            {
                'zone_id': 1,
                'crop_sequence': [{'species_id': 1, 'quantity': 10}],
                'companion_pairs': [(1, 2)],
                'rotation_cycle_days': 90,
                'last_rotation': datetime.now() - timedelta(days=100),
                'soil_health_targets': {'nitrogen': 0.6, 'phosphorus': 0.5},
                'pest_monitoring_days': 7
            }
        ]

        await engine.initialize_succession_plans(zone_configs)

        assert 1 in engine.succession_plans
        plan = engine.succession_plans[1]
        assert plan.zone_id == 1
        assert plan.rotation_cycle_days == 90
        assert len(plan.crop_sequence) == 1

    @pytest.mark.asyncio
    async def test_decision_context_analysis(self, setup_engine):
        """Test comprehensive decision context gathering."""
        engine, _, _, _ = setup_engine

        context = await engine.analyze_decision_context(1)

        assert context.zone_id == 1
        assert isinstance(context.current_time, datetime)
        assert isinstance(context.sensor_data, dict)
        assert isinstance(context.spatial_data, dict)
        assert isinstance(context.weather_forecast, dict)
        assert isinstance(context.crop_health, dict)
        assert isinstance(context.soil_conditions, dict)

    @pytest.mark.asyncio
    async def test_planting_opportunities_evaluation(self, setup_engine):
        """Test evaluation of planting season triggers."""
        engine, _, _, spatial_mock = setup_engine

        # Set up succession plan that's ready for rotation
        plan = SuccessionPlan(
            zone_id=1,
            crop_sequence=[{'species_id': 1, 'quantity': 5}],
            companion_pairs=[],
            rotation_cycle_days=30,
            last_rotation=datetime.now() - timedelta(days=35),  # Past rotation time
            soil_health_targets={},
            pest_monitoring_schedule=timedelta(days=7)
        )
        engine.succession_plans[1] = plan

        context = DecisionContext(
            zone_id=1,
            current_time=datetime.now(),
            sensor_data={},
            spatial_data={},
            weather_forecast={},
            crop_health={},
            soil_conditions={}
        )

        triggers = await engine._evaluate_planting_opportunities(context)

        assert len(triggers) == 1
        trigger = triggers[0]
        assert trigger.event_type == SuccessionEvent.PLANTING_SEASON
        assert trigger.zone_id == 1
        assert trigger.priority == 8
        assert RoboticAction.PLANT_SEED in trigger.robotic_actions

    @pytest.mark.asyncio
    async def test_harvest_readiness_evaluation(self, setup_engine):
        """Test evaluation of harvest-ready crops."""
        engine, _, _, _ = setup_engine

        context = DecisionContext(
            zone_id=1,
            current_time=datetime.now(),
            sensor_data={},
            spatial_data={},
            weather_forecast={},
            crop_health={1: 0.95, 2: 0.85},  # Crop 1 ready for harvest
            soil_conditions={}
        )

        triggers = await engine._evaluate_harvest_readiness(context)

        assert len(triggers) == 1
        trigger = triggers[0]
        assert trigger.event_type == SuccessionEvent.HARVEST_READY
        assert trigger.crop_instance_id == 1
        assert trigger.priority == 9
        assert RoboticAction.HARVEST_CROP in trigger.robotic_actions

    @pytest.mark.asyncio
    async def test_soil_depletion_evaluation(self, setup_engine):
        """Test evaluation of soil nutrient depletion."""
        engine, _, _, _ = setup_engine

        # Set up succession plan with soil targets
        plan = SuccessionPlan(
            zone_id=1,
            crop_sequence=[],
            companion_pairs=[],
            rotation_cycle_days=90,
            last_rotation=datetime.now(),
            soil_health_targets={'nitrogen': 0.6, 'phosphorus': 0.5},
            pest_monitoring_schedule=timedelta(days=7)
        )
        engine.succession_plans[1] = plan

        context = DecisionContext(
            zone_id=1,
            current_time=datetime.now(),
            sensor_data={},
            spatial_data={},
            weather_forecast={},
            crop_health={},
            soil_conditions={'nitrogen': 0.3, 'phosphorus': 0.6}  # Nitrogen depleted
        )

        triggers = await engine._evaluate_soil_depletion(context)

        assert len(triggers) == 1
        trigger = triggers[0]
        assert trigger.event_type == SuccessionEvent.SOIL_DEPLETION
        assert trigger.parameters['nutrient'] == 'nitrogen'
        assert RoboticAction.APPLY_FERTILIZER in trigger.robotic_actions

    @pytest.mark.asyncio
    async def test_pest_detection_evaluation(self, setup_engine):
        """Test evaluation of pest detection from sensor data."""
        engine, _, _, _ = setup_engine

        context = DecisionContext(
            zone_id=1,
            current_time=datetime.now(),
            sensor_data={
                'acoustic_anomalies': [{
                    'pest_type': 'aphids',
                    'location': {'x': 10, 'y': 5},
                    'confidence': 0.9,
                    'severity': 'high'
                }]
            },
            spatial_data={},
            weather_forecast={},
            crop_health={},
            soil_conditions={}
        )

        triggers = await engine._evaluate_pest_detection(context)

        assert len(triggers) == 1
        trigger = triggers[0]
        assert trigger.event_type == SuccessionEvent.PEST_DETECTION
        assert trigger.priority == 10  # Highest priority
        assert trigger.parameters['pest_type'] == 'aphids'
        assert RoboticAction.PEST_CONTROL in trigger.robotic_actions

    @pytest.mark.asyncio
    async def test_companion_planting_needs(self, setup_engine):
        """Test evaluation of companion planting requirements."""
        engine, _, _, spatial_mock = setup_engine

        # Set up succession plan with companion pairs
        plan = SuccessionPlan(
            zone_id=1,
            crop_sequence=[],
            companion_pairs=[(1, 2)],  # Tomato (1) and Basil (2) are companions
            rotation_cycle_days=90,
            last_rotation=datetime.now(),
            soil_health_targets={},
            pest_monitoring_schedule=timedelta(days=7)
        )
        engine.succession_plans[1] = plan

        context = DecisionContext(
            zone_id=1,
            current_time=datetime.now(),
            sensor_data={},
            spatial_data={},
            weather_forecast={},
            crop_health={1: 0.7},  # Tomato struggling
            soil_conditions={}
        )

        # Mock crop species lookup
        with patch.object(engine, '_get_crop_species', return_value=1):  # Tomato
            triggers = await engine._evaluate_companion_needs(context)

        assert len(triggers) == 1
        trigger = triggers[0]
        assert trigger.event_type == SuccessionEvent.COMPANION_NEEDED
        assert trigger.crop_instance_id == 1
        assert trigger.parameters['companion_species'] == 2  # Basil

    @pytest.mark.asyncio
    async def test_maintenance_needs_evaluation(self, setup_engine):
        """Test evaluation of maintenance requirements."""
        engine, _, _, _ = setup_engine

        context = DecisionContext(
            zone_id=1,
            current_time=datetime.now(),
            sensor_data={
                'growth_metrics': {
                    1: {'needs_pruning': True}
                }
            },
            spatial_data={},
            weather_forecast={'precipitation_mm': 1.0},  # Low rainfall
            crop_health={},
            soil_conditions={}
        )

        triggers = await engine._evaluate_maintenance_needs(context)

        # Should generate both irrigation and pruning triggers
        irrigation_trigger = next((t for t in triggers if t.parameters.get('maintenance_type') == 'irrigation'), None)
        pruning_trigger = next((t for t in triggers if t.parameters.get('maintenance_type') == 'pruning'), None)

        assert irrigation_trigger is not None
        assert pruning_trigger is not None
        assert irrigation_trigger.event_type == SuccessionEvent.MAINTENANCE_REQUIRED
        assert RoboticAction.IRRIGATION in irrigation_trigger.robotic_actions

    @pytest.mark.asyncio
    async def test_trigger_prioritization_and_execution(self, setup_engine):
        """Test trigger prioritization and execution."""
        engine, _, robotics_mock, _ = setup_engine

        # Create test triggers with different priorities
        triggers = [
            OrchestrationTrigger(
                event_type=SuccessionEvent.PLANTING_SEASON,
                zone_id=1,
                crop_instance_id=None,
                priority=6,
                trigger_time=datetime.now(),
                parameters={},
                robotic_actions=[RoboticAction.PLANT_SEED]
            ),
            OrchestrationTrigger(
                event_type=SuccessionEvent.PEST_DETECTION,
                zone_id=1,
                crop_instance_id=1,
                priority=10,
                trigger_time=datetime.now(),
                parameters={},
                robotic_actions=[RoboticAction.PEST_CONTROL]
            )
        ]

        await engine._prioritize_and_schedule_triggers(triggers)

        # Check that triggers were added and sorted by priority
        assert len(engine.active_triggers) == 2
        assert engine.active_triggers[0].priority == 10  # Highest priority first
        assert engine.active_triggers[1].priority == 6

        # Execute pending triggers (only high priority >= 8)
        await engine._execute_pending_triggers()

        # Verify high-priority trigger was executed
        robotics_mock.dispatch_action.assert_called_once()
        call_args = robotics_mock.dispatch_action.call_args
        assert call_args[1]['action_type'] == RoboticAction.PEST_CONTROL.value

        # Only high-priority trigger should remain
        assert len(engine.active_triggers) == 1
        assert engine.active_triggers[0].priority == 6

    @pytest.mark.asyncio
    async def test_full_orchestration_cycle(self, setup_engine):
        """Test complete orchestration cycle execution."""
        engine, vryndara_mock, robotics_mock, spatial_mock = setup_engine

        # Set up a basic succession plan
        plan = SuccessionPlan(
            zone_id=1,
            crop_sequence=[{'species_id': 1}],
            companion_pairs=[],
            rotation_cycle_days=90,
            last_rotation=datetime.now() - timedelta(days=100),
            soil_health_targets={'nitrogen': 0.5},
            pest_monitoring_schedule=timedelta(days=7)
        )
        engine.succession_plans[1] = plan

        # Mock context data to trigger some actions
        with patch.object(engine, '_gather_sensor_data', return_value={'acoustic_anomalies': []}), \
             patch.object(engine, '_analyze_spatial_layout', return_value={}), \
             patch.object(engine, '_get_weather_forecast', return_value={'precipitation_mm': 1.0}), \
             patch.object(engine, '_assess_crop_health', return_value={1: 0.95}), \
             patch.object(engine, '_analyze_soil_conditions', return_value={'nitrogen': 0.3}):

            await engine.execute_orchestration_cycle(1)

        # Verify that some actions were triggered
        assert len(engine.decision_history) == 1
        decision = engine.decision_history[0]
        assert decision['zone_id'] == 1
        assert 'triggers_generated' in decision

    def test_decision_logging(self, setup_engine):
        """Test decision context logging for learning."""
        engine, _, _, _ = setup_engine

        context = DecisionContext(
            zone_id=1,
            current_time=datetime.now(),
            sensor_data={'temp': 25.0},
            spatial_data={},
            weather_forecast={},
            crop_health={1: 0.8},
            soil_conditions={'nitrogen': 0.6}
        )

        triggers = [
            OrchestrationTrigger(
                event_type=SuccessionEvent.PLANTING_SEASON,
                zone_id=1,
                crop_instance_id=None,
                priority=8,
                trigger_time=datetime.now(),
                parameters={},
                robotic_actions=[]
            )
        ]

        engine._log_decision(context, triggers)

        assert len(engine.decision_history) == 1
        logged = engine.decision_history[0]
        assert logged['zone_id'] == 1
        assert logged['triggers_generated'] == 1
        assert logged['trigger_types'] == ['planting_season']

    @pytest.mark.asyncio
    async def test_error_handling_in_cycle(self, setup_engine):
        """Test error handling during orchestration cycle."""
        engine, _, _, _ = setup_engine

        # Mock a method to raise an exception
        with patch.object(engine, 'analyze_decision_context', side_effect=Exception("Test error")):
            # Should not raise exception, but log error
            await engine.execute_orchestration_cycle(1)

        # Decision history should still be empty due to error
        assert len(engine.decision_history) == 0


# Integration tests for the orchestration router would go here
# These would test the FastAPI endpoints with a test client

if __name__ == "__main__":
    pytest.main([__file__])