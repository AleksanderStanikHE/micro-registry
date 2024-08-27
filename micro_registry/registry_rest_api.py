from fastapi import FastAPI, HTTPException
import uvicorn
from threading import Thread
from typing import Any, Dict, Optional
from micro_registry.component import MicroComponent
from micro_registry.registry import (
    instance_registry, class_registry,
    register_class, load_module_from_path,
    load_modules_from_directory, load_instances_from_yaml, load_instances_from_yaml_data,
    get_classes_by_base, get_class_names_by_base, filter_instances_by_base_class_name
)
from pydantic import BaseModel, Field


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


@register_class
class RegistryRestApi(MicroComponent):
    def __init__(self, name: str, parent=None, host="0.0.0.0", port=8000):
        super().__init__(name, parent)
        self.app = FastAPI()
        self.host = host
        self.port = port
        self._setup_routes()

    def _setup_routes(self):
        @self.app.get("/classes/")
        def list_registered_classes():
            return {"classes": list(class_registry.keys())}

        @self.app.get("/instances/")
        def list_registered_instances():
            return {"instances": list(instance_registry.keys())}

        @self.app.post("/create-instance/")
        def create_instance_api(request: CreateInstanceRequest):
            if request.class_name not in class_registry:
                raise HTTPException(status_code=404, detail="Class not found")
            parameters = request.parameters or {}
            try:
                instance = class_registry[request.class_name]['class'](**parameters)
                instance_registry[request.instance_name] = instance
                return {"message": f"Instance '{request.instance_name}' created successfully"}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get("/instance/{instance_name}/attributes/")
        def get_instance_attributes(instance_name: str):
            instance = instance_registry.get(instance_name)
            if not instance:
                raise HTTPException(status_code=404, detail="Instance not found")
            return {"attributes": instance.__dict__}

        @self.app.get("/instance/{instance_name}/attribute/{attribute_name}")
        def get_instance_attribute(instance_name: str, attribute_name: str):
            instance = instance_registry.get(instance_name)
            if not instance:
                raise HTTPException(status_code=404, detail="Instance not found")

            if hasattr(instance, attribute_name):
                return {attribute_name: getattr(instance, attribute_name)}
            else:
                raise HTTPException(status_code=404, detail="Attribute not found")

        @self.app.post("/instance/{instance_name}/attribute/{attribute_name}")
        def set_instance_attribute(instance_name: str, attribute_name: str, request: SetAttributeRequest):
            instance = instance_registry.get(instance_name)
            if not instance:
                raise HTTPException(status_code=404, detail="Instance not found")

            if hasattr(instance, attribute_name):
                setattr(instance, attribute_name, request.value)
                return {"message": f"Attribute '{attribute_name}' updated successfully"}
            else:
                raise HTTPException(status_code=404, detail="Attribute not found")

        @self.app.post("/instance/{instance_name}/attributes/update/")
        def batch_update_attributes(instance_name: str, request: BatchUpdateRequest):
            instance = instance_registry.get(instance_name)
            if not instance:
                raise HTTPException(status_code=404, detail="Instance not found")

            updated_attributes = []
            for attr, new_value in request.attributes.items():
                if hasattr(instance, attr):
                    current_value = getattr(instance, attr)
                    if current_value != new_value:  # Only update if values differ
                        setattr(instance, attr, new_value)
                        updated_attributes.append(attr)
                else:
                    raise HTTPException(status_code=400, detail=f"Attribute '{attr}' not found on instance '{instance_name}'")

            return {
                "message": f"Attributes {updated_attributes} updated successfully",
                "updated_attributes": updated_attributes,
            }

        @self.app.post("/load-instances-from-yaml/")
        def load_instances_from_yaml_string_api(request: LoadInstancesRequest):
            try:
                load_instances_from_yaml_data(request.yaml_content)
                return {"message": "Instances loaded from YAML string successfully."}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.post("/load-instances-from-yaml-file/")
        def load_instances_from_yaml_file_api(request: LoadInstancesRequest):
            try:
                load_instances_from_yaml(request.yaml_content)
                return {"message": "Instances loaded from YAML string successfully."}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.post("/load-module/")
        def load_module(request: LoadModuleRequest):
            try:
                load_module_from_path(request.file_path, request.module_name)
                return {"message": f"Module '{request.module_name}' from '{request.file_path}' loaded successfully."}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.post("/load-modules-from-directory/")
        def load_modules(request: LoadModulesRequest):
            try:
                load_modules_from_directory(request.directory)
                return {"message": f"Modules from directory '{request.directory}' loaded successfully."}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get("/classes-by-base/")
        def get_classes_by_base_class(base_class_name: str):
            try:
                classes = get_classes_by_base(base_class_name)
                return {"classes": list(classes.keys())}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get("/class-names-by-base/")
        def get_class_names_by_base_class(base_class_name: str):
            try:
                class_names = get_class_names_by_base(base_class_name)
                return {"class_names": class_names}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get("/filter-instances-by-base-class/")
        def filter_instances(base_class_name: str):
            try:
                filtered_instances = filter_instances_by_base_class_name(base_class_name)
                return {"instances": list(filtered_instances.keys())}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

    def start(self):
        def run():
            uvicorn.run(self.app, host=self.host, port=self.port)

        thread = Thread(target=run)
        thread.start()
