from pydantic import BaseModel, Field

class ConfluenceConfig(BaseModel):
    """Configuration for a specific Confluence instance/workspace."""
    url: str = Field(..., description="Base URL of the Confluence Cloud instance")
    username: str = Field(..., description="Email address for Atlassian account")
    api_token: str = Field(..., description="Atlassian API Token")
    space_key: str = Field(default="~", description="Default space key for page creation")
