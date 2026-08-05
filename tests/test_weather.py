from ai.weather_integration import get_forecast


def test_get_forecast_structure():
    f = get_forecast(51.5, -0.12)
    assert isinstance(f, list)
    assert len(f) > 0
    assert 'temp_c' in f[0]
