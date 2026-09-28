from typing import Callable, Dict, Any, List, Optional
from pydantic import BaseModel, Field

class ToolDefinition(BaseModel):
    name: str
    description: str
    provider: str
    is_write: bool = False
    risk_level: str = "low"
    parameters_schema: Dict[str, Any]

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, description: str, provider: str, is_write: bool, risk_level: str, schema: BaseModel):
        def decorator(func: Callable):
            self._tools[name] = {
                "definition": ToolDefinition(
                    name=name,
                    description=description,
                    provider=provider,
                    is_write=is_write,
                    risk_level=risk_level,
                    parameters_schema=schema.model_json_schema()
                ),
                "func": func,
                "schema_cls": schema
            }
            return func
        return decorator

    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        return self._tools.get(name)

    def list_tools(self) -> List[ToolDefinition]:
        return [item["definition"] for item in self._tools.values()]

registry = ToolRegistry()
