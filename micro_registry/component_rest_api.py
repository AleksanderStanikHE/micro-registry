# component_rest_api.py
import inspect
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Union, Any
from micro_registry.component import MicroComponent, create_component
from micro_registry.registry import instance_registry


class CreateComponentModel(BaseModel):
    class_name: str
    instance_name: str
    parent_path: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = {}


class UpdatePropertyModel(BaseModel):
    property_name: str
    value: Union[int, float, bool, str]


class UpdateAttributesModel(BaseModel):
    attributes: Dict[str, Union[int, float, bool, str]]


class ComponentRestApi:
    def __init__(self):
        self.app = FastAPI()

        @self.app.get("/component/{path:path}/hierarchy/")
        def get_component_hierarchy(path: str):
            component = self._get_component_by_path(path)
            if not component:
                raise HTTPException(status_code=404, detail="Component not found")
            return component.get_hierarchy()

        @self.app.get("/components/")
        def get_all_components():
            components = list(instance_registry.keys())
            return {"components": components}

        @self.app.get("/component/{path:path}/attributes/")
        def get_component_attributes(path: str):
            component = self._get_component_by_path(path)
            if not component:
                raise HTTPException(status_code=404, detail="Component not found")
            return {"attributes": self._get_instance_attributes(component)}

        @self.app.get("/component/{path:path}/all/")
        def get_all_component_information(path: str):
            component = self._get_component_by_path(path)
            if not component:
                raise HTTPException(status_code=404, detail="Component not found")
            return self._get_component_and_children_attributes(component)

        @self.app.post("/create-component/")
        def create_component_api(data: CreateComponentModel):
            try:
                parent_instance_name = self._get_component_by_path(data.parent_path).name if data.parent_path else None
                create_component(data.class_name, data.instance_name, parent_instance_name, **data.parameters)
                return {"message": f"Component '{data.instance_name}' created successfully", "parent": data.parent_path}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.post("/component/{path:path}/prepare/")
        def prepare_component(path: str):
            component = self._get_component_by_path(path)
            if not component:
                raise HTTPException(status_code=404, detail="Component not found")
            component.prepare()
            return {"message": f"Component '{component.name}' and its children prepared successfully"}

        @self.app.post("/component/{path:path}/start/")
        def start_component(path: str):
            component = self._get_component_by_path(path)
            if not component:
                raise HTTPException(status_code=404, detail="Component not found")
            component.start()
            return {"message": f"Component '{component.name}' and its children started successfully"}

        @self.app.post("/component/{path:path}/pause/")
        def pause_component(path: str):
            component = self._get_component_by_path(path)
            if not component:
                raise HTTPException(status_code=404, detail="Component not found")
            component.pause()
            return {"message": f"Component '{component.name}' and its children paused successfully"}

        @self.app.post("/component/{path:path}/stop/")
        def stop_component(path: str):
            component = self._get_component_by_path(path)
            if not component:
                raise HTTPException(status_code=404, detail="Component not found")
            component.stop()
            return {"message": f"Component '{component.name}' and its children stopped successfully"}

        @self.app.post("/component/{path:path}/update-property/")
        def update_component_property(path: str, update: UpdatePropertyModel):
            component = self._get_component_by_path(path)
            if not component:
                raise HTTPException(status_code=404, detail="Component not found")

            if hasattr(component, update.property_name):
                try:
                    setattr(component, update.property_name, update.value)
                    return {"message": f"Property '{update.property_name}' updated successfully"}
                except ValueError as e:
                    raise HTTPException(status_code=400, detail=str(e))
                except TypeError as e:
                    raise HTTPException(status_code=400, detail=f"Invalid type for property '{update.property_name}': {str(e)}")
            else:
                raise HTTPException(status_code=404, detail="Property not found")

        @self.app.post("/component/{path:path}/update-attributes/")
        def update_component_attributes(path: str, update: UpdateAttributesModel):
            component = self._get_component_by_path(path)
            if not component:
                raise HTTPException(status_code=404, detail="Component not found")

            errors = []
            for attr_name, attr_value in update.attributes.items():
                if hasattr(component, attr_name):
                    try:
                        setattr(component, attr_name, attr_value)
                    except ValueError as e:
                        # Ensure the error message is consistently formatted
                        errors.append({attr_name: f"Value must be non-negative: {str(e)}"})
                    except TypeError as e:
                        errors.append({attr_name: f"Invalid type: {str(e)}"})
                else:
                    errors.append({attr_name: "Property not found"})

            if errors:
                raise HTTPException(status_code=400, detail=errors)

            return {"message": "Attributes updated successfully"}

    def _get_component_by_path(self, path: str) -> Optional[MicroComponent]:
        """Helper method to retrieve a component by its path."""
        if not path:
            return None

        path_parts = path.split('/')
        component = instance_registry.get(path_parts[0])
        for part in path_parts[1:]:
            if component:
                component = next((child for child in component.get_children() if child.name == part), None)
            else:
                return None

        return component

    def _get_instance_attributes(self, component: MicroComponent) -> Dict[str, Any]:
        """Return detailed information about the attributes and properties of a component."""
        attributes_info = {}

        for attr_name in dir(component):
            # Exclude private attributes and methods
            if attr_name.startswith('_'):
                continue

            attr_value = getattr(component, attr_name)
            attr_type = type(attr_value).__name__

            if attr_type == 'method':
                # Use inspect to get the method's signature (parameters)
                signature = inspect.signature(attr_value)
                parameters = {}
                for param_name, param in signature.parameters.items():
                    parameters[param_name] = str(param)

                # Include the method's parameters in the attribute info
                attr_value = f"{parameters}"
            elif isinstance(attr_value, MicroComponent):
                attr_value = attr_value.name  # Replace reference with name
            elif isinstance(attr_value, list):
                attr_value = [v.name if isinstance(v, MicroComponent) else v for v in attr_value]

            # Determine if the attribute is a property and if it has a setter
            is_property = isinstance(getattr(type(component), attr_name, None), property)
            has_setter = is_property and getattr(type(component), attr_name).fset is not None

            attributes_info[attr_name] = {
                "value": attr_value,
                "type": attr_type,
                "is_property": is_property,
                "has_setter": has_setter
            }

        return attributes_info

    def _get_component_and_children_attributes(self, component: MicroComponent) -> Dict[str, Any]:
        """Recursively gather attributes of a component and all its descendants, returning instance names instead of references."""
        result = {
            "name": component.name,
            "attributes": self._get_instance_attributes(component),
            "children": [self._get_component_and_children_attributes(child) for child in component.get_children()]
        }
        return result
