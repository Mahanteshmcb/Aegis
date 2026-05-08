## Run proto file
python -m grpc_tools.protoc --proto_path=ai/protos --python_out=ai/protos --grpc_python_out=ai/protos ai/protos/sensors.proto