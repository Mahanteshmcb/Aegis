"""
Aegis Backend - Vryndara Integration Tests
"""
import pytest
from unittest.mock import patch

# Patch VryndaraConnector for all tests in this file
def test_vryndara_health_check_fallback():
    from ai.vryndara_connector import VryndaraConnector
    connector = VryndaraConnector(fallback_mode=True)
    # Simulate fallback mode
    connector.is_connected = False
    assert connector.health_check() is False
    # Should return fallback data for research
    result = connector.research_compliance_framework(standard="ISO27001", project_id="TEST-001")
    assert result["framework"] == "ISO27001"
    assert result["status"] == "fallback_mode"


def test_vryndara_health_check_connected():
    from ai.vryndara_connector import VryndaraConnector
    connector = VryndaraConnector(fallback_mode=False)
    connector.is_connected = True
    assert connector.health_check() is True
