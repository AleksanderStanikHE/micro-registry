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

from typing import Any, Dict, Optional, Union

from fastapi import HTTPException
from pydantic import BaseModel

from micro_registry.component import MicroComponent, create_component
from micro_registry.registry import instance_registry, register_class


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


@register_class
class ComponentRestApi(MicroComponent):
    def __init__(self, name: str, parent):
        super().__init__(name, parent)
        self._get_instance_attributes = parent._get_instance_attributes
        self.app = parent.app
        self.prefix = parent.prefix

        @self.app.get(self.prefix + "/component/{path:path}/hierarchy/")
        def get_component_hierarchy(path: str):
            component = self._get_component_by_path(path)
            if not component:
                raise HTTPException(status_code=404, detail="Component not found")
            return component.get_hierarchy()

        @self.app.get(self.prefix + "/components/")
        def get_all_components():
            components = list(instance_registry.keys())
            return {"components": components}

        @self.app.get(self.prefix + "/component/{path:path}/attributes/")
        def get_component_attributes(path: str):
            component = self._get_component_by_path(path)
            if not component:
                raise HTTPException(status_code=404, detail="Component not found")
            return {
                "attributes": self._get_instance_attributes(
                    component, filter_types=["properties", "attributes"]
                )
            }

        @self.app.get(self.prefix + "/component/{path:path}/properties/")
        def get_component_properties(path: str):
            component = self._get_component_by_path(path)
            if not component:
                raise HTTPException(status_code=404, detail="Component not found")
            return {
                "properties": self._get_instance_attributes(
                    component, filter_types=["properties"]
                )
            }

        @self.app.get(self.prefix + "/component/{path:path}")
        @self.app.get(self.prefix + "/component/{path:path}/")
        @self.app.get(self.prefix + "/component/{path:path}/all/")
        def get_all_component_information(path: str):
            component = self._get_component_by_path(path)
            if not component:
                raise HTTPException(status_code=404, detail="Component not found")
            result = self._get_component_and_children_attributes(component)
            # print(result)
            return result

        @self.app.post(self.prefix + "/create-component/")
        def create_component_api(data: CreateComponentModel):
            try:
                parent_instance_name = (
                    self._get_component_by_path(data.parent_path).name
                    if data.parent_path
                    else None
                )
                create_component(
                    data.class_name,
                    data.instance_name,
                    parent_instance_name,
                    **data.parameters,
                )
                return {
                    "message": f"Component '{data.instance_name}' created successfully",
                    "parent": data.parent_path,
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.post(self.prefix + "/component/{path:path}/prepare/")
        def prepare_component(path: str):
            component = self._get_component_by_path(path)
            if not component:
                raise HTTPException(status_code=404, detail="Component not found")
            component.prepare()
            return {
                "message": f"Component '{component.name}' and its children prepared successfully"
            }

        @self.app.post(self.prefix + "/component/{path:path}/start/")
        def start_component(path: str):
            component = self._get_component_by_path(path)
            if not component:
                raise HTTPException(status_code=404, detail="Component not found")
            component.start()
            return {
                "message": f"Component '{component.name}' and its children started successfully"
            }

        @self.app.post(self.prefix + "/component/{path:path}/pause/")
        def pause_component(path: str):
            component = self._get_component_by_path(path)
            if not component:
                raise HTTPException(status_code=404, detail="Component not found")
            component.pause()
            return {
                "message": f"Component '{component.name}' and its children paused successfully"
            }

        @self.app.post(self.prefix + "/component/{path:path}/stop/")
        def stop_component(path: str):
            component = self._get_component_by_path(path)
            if not component:
                raise HTTPException(status_code=404, detail="Component not found")
            component.stop()
            return {
                "message": f"Component '{component.name}' and its children stopped successfully"
            }

        @self.app.post(self.prefix + "/component/{path:path}/update-property/")
        def update_component_property(path: str, update: UpdatePropertyModel):
            component = self._get_component_by_path(path)
            if not component:
                raise HTTPException(status_code=404, detail="Component not found")

            if hasattr(component, update.property_name):
                try:
                    setattr(component, update.property_name, update.value)
                    return {
                        "message": f"Property '{update.property_name}' updated successfully"
                    }
                except ValueError as e:
                    raise HTTPException(status_code=400, detail=str(e))
                except TypeError as e:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid type for property '{update.property_name}': {str(e)}",
                    )
            else:
                raise HTTPException(status_code=404, detail="Property not found")

        @self.app.post(self.prefix + "/component/{path:path}/update-attributes/")
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
                        errors.append(
                            {attr_name: f"Value must be non-negative: {str(e)}"}
                        )
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

        path_parts = path.split("/")
        root_name = path_parts[0]
        component = instance_registry.get(root_name)
        if not component:
            return None

        for part in path_parts[1:]:
            component = next(
                (child for child in component.get_children() if child.name == part),
                None,
            )
            if not component:
                return None

        return component

    def _get_component_and_children_attributes(
        self, component: MicroComponent
    ) -> Dict[str, Any]:
        """Recursively gather attributes of a component and all its descendants, returning instance names instead of references."""
        result = {
            "name": component.name,
            "attributes": self._get_instance_attributes(component),
            "children": [
                self._get_component_and_children_attributes(child)
                for child in component.get_children()
            ],
        }
        return result
