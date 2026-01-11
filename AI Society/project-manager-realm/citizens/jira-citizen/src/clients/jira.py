import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import Dict, Any, Optional
from src.utils.observability import get_logger

logger = get_logger(__name__)

class JiraClient:
    """Client for interactions with JIRA REST API."""
    
    def __init__(self, config: Dict[str, str]):
        self.base_url = config.get("jira_url")
        self.username = config.get("jira_username")
        self.token = config.get("jira_token")
        
        if not all([self.base_url, self.username, self.token]):
            raise ValueError("Incomplete JIRA configuration")
            
        self.auth = (self.username, self.token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def create_epic(self, project_key: str, summary: str, description: str) -> Dict[str, Any]:
        """Create an Epic in JIRA."""
        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": "Epic"}
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/rest/api/2/issue",
                auth=self.auth,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def create_story(self, project_key: str, summary: str, description: str, epic_key: Optional[str] = None) -> Dict[str, Any]:
        """Create a User Story in JIRA."""
        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": "Story"}
            }
        }
        
        if epic_key:
            # Note: "customfield_XXXXX" is typical for Epic Link, standard way varies by JIRA version.
            # For simplicity/modern JIRA Cloud, we might use 'parent' field if it's next-gen, 
            # or 'Epic Link' field. Since field IDs are dynamic, we usually need to look them up.
            # Falling back to a standard assumption or just leaving 'parent' for now.
            # Assuming JIRA Cloud standardized 'parent':
            payload["fields"]["parent"] = {"key": epic_key}
            
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/rest/api/2/issue",
                auth=self.auth,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def assign_issue(self, issue_key: str, account_id: str):
        """Assign an issue to a user."""
        payload = {"accountId": account_id}
        
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.base_url}/rest/api/3/issue/{issue_key}/assignee", # API v3 uses accountId
                auth=self.auth,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def start_sprint(self, sprint_id: int):
        """Start a sprint."""
        # This requires moving sprint state usually via Greenhopper/Agile API
        payload = {"state": "active"}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/rest/agile/1.0/sprint/{sprint_id}",
                auth=self.auth,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
