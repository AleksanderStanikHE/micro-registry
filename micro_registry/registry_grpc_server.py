import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import grpc
import signal
from concurrent import futures
from micro_registry.component import MicroComponent
from registry_pb2 import (
    RegisterClassResponse,
    CreateInstanceResponse,
    GetInstanceAttributesResponse,
    ListRegisteredClassesResponse,
    ListRegisteredInstancesResponse
)
import registry_pb2_grpc
from micro_registry.registry import (
    class_registry,
    instance_registry,
    register_class,
    create_instance
)


class RegistryServiceServicer(MicroComponent, registry_pb2_grpc.RegistryServiceServicer):
    def __init__(self, name: str, parent: MicroComponent = None, host: str = '[::]', port: int = 50051):
        super().__init__(name, parent)
        self.host = host
        self.port = port
        self.server = None

    def RegisterClass(self, request, context):
        try:
            cls = type(request.class_name, (object,), {})
            register_class(cls)
            return RegisterClassResponse(message=f"Class {request.class_name} registered successfully.")
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return RegisterClassResponse(message="Failed to register class.")

    def CreateInstance(self, request, context):
        try:
            parameters = dict(request.parameters)
            instance = create_instance(request.class_name, **parameters)
            instance_registry[request.instance_name] = instance
            return CreateInstanceResponse(message=f"Instance {request.instance_name} created successfully.")
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return CreateInstanceResponse(message="Failed to create instance.")

    def GetInstanceAttributes(self, request, context):
        instance = instance_registry.get(request.instance_name)
        if not instance:
            context.set_details("Instance not found")
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return GetInstanceAttributesResponse()

        attributes = {key: str(value) for key, value in instance.__dict__.items()}
        return GetInstanceAttributesResponse(attributes=attributes)

    def ListRegisteredClasses(self, request, context):
        class_names = list(class_registry.keys())
        return ListRegisteredClassesResponse(class_names=class_names)

    def ListRegisteredInstances(self, request, context):
        instance_names = list(instance_registry.keys())
        return ListRegisteredInstancesResponse(instance_names=instance_names)

    def start(self):
        """Start the gRPC server with SSL/TLS."""
        with open('server.crt', 'rb') as f:
            server_cert = f.read()
        with open('server.key', 'rb') as f:
            server_key = f.read()

        # Create server credentials
        server_credentials = grpc.ssl_server_credentials([(server_key, server_cert)])

        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        registry_pb2_grpc.add_RegistryServiceServicer_to_server(self, self.server)
        self.server.add_secure_port(f'{self.host}:{self.port}', server_credentials)
        self.server.start()
        print(f"gRPC server started securely on {self.host}:{self.port}")

        # Handle shutdown signals
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

        self.server.wait_for_termination()

    def stop(self):
        """Stop the gRPC server."""
        if self.server:
            self.server.stop(None)
            print(f"gRPC server stopped on {self.host}:{self.port}")

    def shutdown(self, signum, frame):
        """Shutdown the gRPC server gracefully."""
        if self.server:
            self.server.stop(0)
            print(f"gRPC server stopped on {self.host}:{self.port}")
        sys.exit(0)


if __name__ == "__main__":
    registry_service = RegistryServiceServicer(name="RegistryService")
    registry_service.start()
