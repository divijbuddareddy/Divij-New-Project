from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

class BaseIntegration(ABC):
    def __init__(self, workspace_id: str, credentials: Dict[str, Any]):
        self.workspace_id = workspace_id
        self.credentials = credentials

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """Validates API credentials and access."""
        pass

    @abstractmethod
    async def sync_evidence(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Extracts and returns normalized evidence items."""
        pass

    @abstractmethod
    async def execute_action(self, action_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Executes an approved write action."""
        pass

    @abstractmethod
    async def verify_action(self, action_type: str, parameters: Dict[str, Any], execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """Verifies that an executed action produced the intended effect in the live system."""
        pass
