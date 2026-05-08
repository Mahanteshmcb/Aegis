# Day 37: gRPC Integration Testing Framework

## Overview
Comprehensive integration testing suite for validating gRPC contracts in the Aegis Biosphere Protocol. This framework provides end-to-end testing of sensor data streaming, robotic command execution, security validation, and performance benchmarking.

## Architecture

### Mock Clients & Simulators
- **SensorSimulatorManager**: Manages multiple sensor simulators generating realistic data
- **MockMycelialProbe**: Simulates sub-surface mycelial probe data (biomass, pH, nutrients)
- **MockAcousticPestMonitor**: Simulates acoustic pest detection (frequency analysis, classifications)
- **RoboticFleetManager**: Manages mock robotic fleet for testing command execution
- **MockAegisRover**: Simulates heavy overseer rover operations
- **MockAgriSwarmBot**: Simulates micro-bot swarm operations
- **MockCanopyDrone**: Simulates aerial drone operations

### Test Categories

#### 1. Core Integration Tests (`test_grpc_integration.py`)
- **Sensor Registration & Streaming**: Validates sensor registration and real-time data streaming
- **Health Monitoring**: Tests sensor health status reporting and battery/signal monitoring
- **Calibration Procedures**: Validates sensor calibration workflows
- **Emergency Shutdown**: Tests emergency shutdown procedures across sensor networks
- **Concurrent Streaming**: Tests multiple sensors streaming data simultaneously
- **Network Resilience**: Tests error handling and recovery mechanisms
- **Data Throughput**: Measures sensor data processing performance
- **Bulk Operations**: Tests bulk sensor management operations

#### 2. Security Validation
- **Authentication**: Validates access control mechanisms
- **Input Validation**: Tests input sanitization and bounds checking
- **Data Exposure**: Checks for sensitive data protection

#### 3. Performance Benchmarking
- **Throughput Testing**: Measures sensor data generation and processing rates
- **Command Execution**: Benchmarks robotic command execution times
- **Connection Pooling**: Tests concurrent connection handling
- **Load Testing**: Validates system performance under load

## Usage

### Running All Tests
```bash
python run_grpc_integration_tests.py --all
```

### Running Specific Test Categories
```bash
# Performance benchmarks only
python run_grpc_integration_tests.py --performance

# Security validation only
python run_grpc_integration_tests.py --security

# Verbose output
python run_grpc_integration_tests.py --all --verbose
```

### Running Individual Test Files
```bash
# Run core integration tests
pytest tests/test_grpc_integration.py -v

# Run with coverage
pytest tests/test_grpc_integration.py --cov=ai --cov-report=html
```

## Test Data & Scenarios

### Sensor Simulation Parameters
- **Mycelial Probes**: Biomass density (0-1.0), pH levels (4.0-8.0), electrical activity (0-0.5)
- **Acoustic Monitors**: Pest activity levels (0-1.0), frequency spectra, pest classifications
- **Realistic Variations**: Battery drain, signal fluctuations, occasional offline states

### Robotic Command Scenarios
- **Navigation**: Coordinate-based movement with collision avoidance
- **Harvesting**: Payload management and yield tracking
- **Maintenance**: Automated calibration and diagnostics
- **Emergency Protocols**: Safety shutdowns and recovery procedures

## Performance Benchmarks

### Target Metrics
- **Sensor Throughput**: ≥ 10 readings/second per sensor
- **Command Execution**: < 2 seconds average for robotic commands
- **Concurrent Connections**: Support for 100+ simultaneous clients
- **Memory Usage**: Stable memory consumption under load

### Benchmark Results Format
```
Sensor Throughput: 45.23 readings/second
Test Duration: 5.00 seconds
Avg Command Time: 1.234 seconds
Concurrency 100: 98.5% success, 234.56 req/sec
```

## Security Validation

### Current Security Posture
- **Authentication**: Not yet implemented (uses insecure channels)
- **Input Validation**: Basic validation present, needs enhancement
- **Data Protection**: Position coordinates exposed, needs access controls

### Security Recommendations
1. Implement JWT or certificate-based authentication
2. Add comprehensive input sanitization
3. Implement field-level access controls for sensitive data
4. Add rate limiting and DDoS protection

## Error Handling & Resilience

### Tested Failure Scenarios
- **Invalid Sensor IDs**: Proper NOT_FOUND error responses
- **Network Interruptions**: Automatic reconnection and recovery
- **Malformed Requests**: Input validation and error reporting
- **Resource Exhaustion**: Memory and connection pool management

### Recovery Mechanisms
- **Circuit Breakers**: Automatic failure detection and recovery
- **Retry Logic**: Exponential backoff for transient failures
- **Graceful Degradation**: Continued operation with reduced functionality

## Integration with CI/CD

### Automated Testing Pipeline
```yaml
# .github/workflows/grpc-integration.yml
name: gRPC Integration Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio grpcio-tools
      - name: Run integration tests
        run: python run_grpc_integration_tests.py --all
      - name: Upload test reports
        uses: actions/upload-artifact@v3
        with:
          name: test-reports
          path: grpc_integration_report.txt
```

## Monitoring & Observability

### Test Metrics Collection
- **Success Rates**: Pass/fail ratios for all test categories
- **Performance Trends**: Historical performance data tracking
- **Error Patterns**: Common failure modes and root causes
- **Resource Usage**: CPU, memory, and network utilization

### Logging & Reporting
- **Structured Logs**: JSON-formatted logs for analysis
- **Test Reports**: HTML and text reports with detailed results
- **Performance Dashboards**: Real-time monitoring of test metrics
- **Alerting**: Automated alerts for test failures or performance degradation

## Future Enhancements

### Planned Improvements
1. **Real Hardware Integration**: Replace mock clients with actual sensor/robot connections
2. **Distributed Testing**: Multi-node test execution for large-scale scenarios
3. **Chaos Engineering**: Fault injection testing for resilience validation
4. **Performance Profiling**: Detailed performance analysis with flame graphs
5. **Security Penetration Testing**: Automated security vulnerability scanning

### Extended Test Coverage
- **Multi-Zone Scenarios**: Cross-zone communication and coordination
- **Long-Running Tests**: 24/7 stability testing
- **Environmental Simulation**: Weather and environmental condition testing
- **Scale Testing**: 1000+ sensor and robot simulation

## Troubleshooting

### Common Issues
1. **Port Conflicts**: Ensure port 50051 is available
2. **Protobuf Import Errors**: Regenerate protobuf files if needed
3. **Memory Issues**: Reduce simulator count for resource-constrained environments
4. **Network Timeouts**: Adjust timeout values for slower networks

### Debug Mode
```bash
# Enable debug logging
python run_grpc_integration_tests.py --all --verbose

# Run specific test with debug
pytest tests/test_grpc_integration.py::TestGRPCIntegration::test_sensor_registration_and_streaming -s -v
```

## Dependencies

### Required Packages
```
pytest>=7.0.0
pytest-asyncio>=0.21.0
grpcio>=1.50.0
grpcio-tools>=1.50.0
protobuf>=4.21.0
```

### Optional Packages (for enhanced reporting)
```
pytest-cov>=4.0.0
pytest-html>=3.1.0
pytest-xdist>=3.0.0
```

## Contributing

### Adding New Tests
1. Extend `TestGRPCIntegration` class for new integration tests
2. Add mock clients to `ai/mock_clients.py` for new device types
3. Update performance benchmarks for new metrics
4. Document test scenarios and expected behaviors

### Code Standards
- Use descriptive test method names
- Include docstrings for all test methods
- Add performance assertions with reasonable thresholds
- Ensure tests are idempotent and can run in any order

## Protobuf Compilation

### Compile Proto Files
```bash
# Compile sensors.proto
python -m grpc_tools.protoc --proto_path=ai/protos --python_out=ai/protos --grpc_python_out=ai/protos ai/protos/sensors.proto

# Compile robotics.proto
python -m grpc_tools.protoc --proto_path=ai/protos --python_out=ai/protos --grpc_python_out=ai/protos ai/protos/robotics.proto

# Compile vryndara.proto
python -m grpc_tools.protoc --proto_path=ai/protos --python_out=ai/protos --grpc_python_out=ai/protos ai/protos/vryndara.proto
```

### Generated Files
- `sensors_pb2.py`: Protocol buffer message classes
- `sensors_pb2_grpc.py`: gRPC service stubs and servicer classes
- `robotics_pb2.py`: Robotics protocol buffer messages
- `robotics_pb2_grpc.py`: Robotics gRPC service classes
- `vryndara_pb2.py`: Vryndara AI kernel messages
- `vryndara_pb2_grpc.py`: Vryndara gRPC service classes