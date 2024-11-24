#
# MIT License
#
# Copyright (c) 2024 Aleksander(Olek) Stanik
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction.
#
# See the LICENSE file for full license details.

import inspect
import json
from threading import Thread
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from uvicorn import Config, Server

from micro_registry.component import MicroComponent
from micro_registry.registry import (
    class_registry,
    filter_instances_by_base_class_name,
    get_class_names_by_base,
    get_classes_by_base,
    instance_registry,
    load_instances_from_yaml,
    load_instances_from_yaml_data,
    load_module_from_path,
    load_modules_from_directory,
    register_class,
)


class CreateInstanceRequest(BaseModel):
    class_name: str
    instance_name: str
    parameters: Optional[Dict[str, Any]] = None


# Define the Pydantic model for the request body
class SetAttributeRequest(BaseModel):
    value: Any


# Define the Pydantic model for the request body
class LoadInstancesRequest(BaseModel):
    yaml_content: str


# Define the Pydantic model for the request body
class LoadModuleRequest(BaseModel):
    file_path: str
    module_name: Optional[str] = None


# Define the Pydantic model for the request body
class LoadModulesRequest(BaseModel):
    directory: str


class BatchUpdateRequest(BaseModel):
    attributes: Dict[str, Any] = Field(
        ..., description="A dictionary of attributes to update with their new values."
    )


def is_serializable(value):
    try:
        json.dumps(value)
        return True
    except (TypeError, ValueError):
        return False


def safe_stringify(value):
    if is_serializable(value):
        return value
    elif isinstance(value, (str, int, float, bool, type(None))):
        return value
    else:
        return f"<non-serializable: {type(value).__name__}>"


@register_class
class RegistryRestApi(MicroComponent):
    def __init__(
        self, name: str, parent=None, host="0.0.0.0", port=8000, start_server=True
    ):
        super().__init__(name, parent)
        # Initialize FastAPI application
        self.app = FastAPI()
        self.host = host
        self.port = port
        self.version = "v1"
        self.prefix = f"/api/{self.version}"
        self.start_server = start_server  # Control whether to start Uvicorn

        # Define API endpoints
        @self.app.get(self.prefix)
        @self.app.get(self.prefix + "/")
        def get_api_root():
            return {"message": f"Welcome to Registry API version {self.version}"}

        @self.app.get(self.prefix + "/classes")
        @self.app.get(self.prefix + "/classes/")
        def list_registered_classes():
            return {"classes": list(class_registry.keys())}

        @self.app.get(self.prefix + "/instances")
        @self.app.get(self.prefix + "/instances/")
        def list_registered_instances():
            return {"instances": list(instance_registry.keys())}

        @self.app.post(self.prefix + "/create-instance")
        @self.app.post(self.prefix + "/create-instance/")
        def create_instance_api(request: CreateInstanceRequest):
            if request.class_name not in class_registry:
                raise HTTPException(status_code=404, detail="Class not found")
            parameters = request.parameters or {}
            try:
                instance = class_registry[request.class_name]["class"](**parameters)
                instance_registry[request.instance_name] = instance
                return {
                    "message": f"Instance '{request.instance_name}' created successfully"
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get(self.prefix + "/instance/{instance_name}/attributes")
        @self.app.get(self.prefix + "/instance/{instance_name}/attributes/")
        def get_instance_attributes(instance_name: str):
            instance = instance_registry.get(instance_name)
            if not instance:
                raise HTTPException(status_code=404, detail="Instance not found")
            return {
                "attributes": self._get_instance_attributes(
                    instance, filter_types=["properties", "attributes"]
                )
            }

        @self.app.get(self.prefix + "/instance/{instance_name}/properties")
        @self.app.get(self.prefix + "/instance/{instance_name}/properties/")
        def get_instance_properties(instance_name: str):
            instance = instance_registry.get(instance_name)
            if not instance:
                raise HTTPException(status_code=404, detail="Instance not found")
            return {
                "properties": self._get_instance_attributes(
                    instance, filter_types=["properties"]
                )
            }

        @self.app.get(
            self.prefix + "/instance/{instance_name}/attribute/{attribute_name}"
        )
        def get_instance_attribute(instance_name: str, attribute_name: str):
            instance = instance_registry.get(instance_name)
            if not instance:
                raise HTTPException(status_code=404, detail="Instance not found")

            if hasattr(instance, attribute_name):
                return {attribute_name: getattr(instance, attribute_name)}
            else:
                raise HTTPException(status_code=404, detail="Attribute not found")

        @self.app.post(
            self.prefix + "/instance/{instance_name}/attribute/{attribute_name}"
        )
        def set_instance_attribute(
            instance_name: str, attribute_name: str, request: SetAttributeRequest
        ):
            instance = instance_registry.get(instance_name)
            if not instance:
                raise HTTPException(status_code=404, detail="Instance not found")

            if hasattr(instance, attribute_name):
                setattr(instance, attribute_name, request.value)
                return {"message": f"Attribute '{attribute_name}' updated successfully"}
            else:
                raise HTTPException(status_code=404, detail="Attribute not found")

        @self.app.post(self.prefix + "/instance/{instance_name}/attributes/update")
        @self.app.post(self.prefix + "/instance/{instance_name}/attributes/update/")
        def batch_update_attributes(instance_name: str, request: BatchUpdateRequest):
            instance = instance_registry.get(instance_name)
            if not instance:
                raise HTTPException(status_code=404, detail="Instance not found")

            updated_attributes = []
            error_messages = []

            for attr, attr_data in request.attributes.items():
                if hasattr(instance, attr):
                    current_value = getattr(instance, attr)
                    new_value = attr_data.get("value")
                    if current_value != new_value:  # Only update if values differ
                        try:
                            setattr(instance, attr, new_value)
                            updated_attributes.append(attr)
                        except Exception as e:
                            error_messages.append(
                                f"Failed to update '{attr}': {str(e)}"
                            )
                else:
                    error_messages.append(
                        f"Attribute '{attr}' not found on instance '{instance_name}'"
                    )

            if error_messages:
                raise HTTPException(status_code=400, detail=error_messages)

            return {
                "message": f"Attributes {updated_attributes} updated successfully",
                "updated_attributes": updated_attributes,
            }

        @self.app.post(self.prefix + "/load-instances-from-yaml")
        @self.app.post(self.prefix + "/load-instances-from-yaml/")
        def load_instances_from_yaml_string_api(request: LoadInstancesRequest):
            try:
                load_instances_from_yaml_data(request.yaml_content)
                return {"message": "Instances loaded from YAML string successfully."}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.post(self.prefix + "/load-instances-from-yaml-file")
        @self.app.post(self.prefix + "/load-instances-from-yaml-file/")
        def load_instances_from_yaml_file_api(request: LoadInstancesRequest):
            try:
                load_instances_from_yaml(request.yaml_content)
                return {"message": "Instances loaded from YAML string successfully."}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.post(self.prefix + "/load-module")
        @self.app.post(self.prefix + "/load-module/")
        def load_module(request: LoadModuleRequest):
            try:
                load_module_from_path(request.file_path, request.module_name)
                return {
                    "message": f"Module '{request.module_name}' from '{request.file_path}' loaded successfully."
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.post(self.prefix + "/load-modules-from-directory")
        @self.app.post(self.prefix + "/load-modules-from-directory/")
        def load_modules(request: LoadModulesRequest):
            try:
                load_modules_from_directory(request.directory)
                return {
                    "message": f"Modules from directory '{request.directory}' loaded successfully."
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get(self.prefix + "/classes-by-base")
        @self.app.get(self.prefix + "/classes-by-base/")
        def get_classes_by_base_class(base_class_name: str):
            try:
                classes = get_classes_by_base(base_class_name)
                return {"classes": list(classes.keys())}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get(self.prefix + "/class-names-by-base")
        @self.app.get(self.prefix + "/class-names-by-base/")
        def get_class_names_by_base_class(base_class_name: str):
            try:
                class_names = get_class_names_by_base(base_class_name)
                return {"class_names": class_names}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get(self.prefix + "/filter-instances-by-base-class")
        @self.app.get(self.prefix + "/filter-instances-by-base-class/")
        def filter_instances(base_class_name: str):
            try:
                filtered_instances = filter_instances_by_base_class_name(
                    base_class_name
                )
                return {"instances": list(filtered_instances.keys())}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

    def _get_instance_attributes(
        self, component: MicroComponent, filter_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Return detailed information about the attributes and properties of a component.

        Parameters:
        - component: The component to inspect.
        - filter_types: A list of attribute types to include in the output.
                    Options are 'all', 'properties', 'attributes', 'methods'.
                    If None, defaults to 'all'.

        Returns:
        - A dictionary with detailed information about the selected attributes.
        """
        if filter_types is None:
            filter_types = ["all"]

        attributes_info = {}

        for attr_name in dir(component):
            # Exclude private attributes and methods
            if attr_name.startswith("_"):
                continue

            attr_value = getattr(component, attr_name)
            attr_type = type(attr_value).__name__

            is_property = isinstance(
                getattr(type(component), attr_name, None), property
            )
            is_method = inspect.ismethod(attr_value) or inspect.isfunction(attr_value)

            # Apply filters based on the filter_types list
            if "all" not in filter_types:
                if "properties" not in filter_types and is_property:
                    continue
                if (
                    "attributes" not in filter_types
                    and not is_property
                    and not is_method
                ):
                    continue
                if "methods" not in filter_types and is_method:
                    continue

            if is_method:
                # For methods, provide detailed signature information
                signature = inspect.signature(attr_value)
                parameters = {
                    param_name: str(param)
                    for param_name, param in signature.parameters.items()
                }

                attributes_info[attr_name] = {
                    "type": "method",
                    "parameters": parameters,
                    "doc": attr_value.__doc__,  # Include the docstring if available
                }
            elif isinstance(attr_value, MicroComponent):
                # For MicroComponent instances, only include the name
                attributes_info[attr_name] = {
                    "type": "MicroComponent",
                    "component_name": attr_value.name,
                }
            elif is_property:
                # For properties, determine if it has a setter
                has_setter = (
                    is_property and getattr(type(component), attr_name).fset is not None
                )

                attributes_info[attr_name] = {
                    "type": attr_type,
                    "value": safe_stringify(attr_value),
                    "is_property": True,
                    "has_setter": has_setter,
                }
            elif isinstance(attr_value, list):
                # For lists, check the types of elements
                list_info = []
                for item in attr_value:
                    if isinstance(item, MicroComponent):
                        list_info.append(
                            {"type": "MicroComponent", "component_name": item.name}
                        )
                    else:
                        list_info.append(
                            {"type": type(item).__name__, "value": safe_stringify(item)}
                        )

                attributes_info[attr_name] = {"type": "list", "items": list_info}
            else:
                # For other types, just serialize the value
                attributes_info[attr_name] = {
                    "type": attr_type,
                    "value": safe_stringify(attr_value),
                }

        return attributes_info

    def start(self):
        if self.start_server:
            # Use Uvicorn's Server class to start the server
            config = Config(
                app=self.app, host=self.host, port=self.port, log_level="info"
            )
            self.server = Server(config)
            self.server_thread = Thread(target=self.server.run)
            self.server_thread.start()
        else:
            print("RegistryRestApi server not started (start_server=False)")

    def stop(self):
        # Stop the Uvicorn server
        if hasattr(self, "server"):
            self.server.should_exit = True
            self.server_thread.join()
