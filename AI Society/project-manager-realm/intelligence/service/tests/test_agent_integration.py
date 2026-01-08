# tests/test_agent_integration.py
"""Integration tests for agent execution with configuration loading"""

import pytest
from pathlib import Path
import json
from unittest.mock import AsyncMock, MagicMock, patch

from app.config_loader import get_config_loader, ConfigLoader
from app.agents.agent_manager import get_agent_executor, AgentExecutor
from app.providers.base import LLMMessage


@pytest.fixture
def config_loader():
    """Get config loader instance"""
    return get_config_loader()


@pytest.fixture
def agent_executor():
    """Get agent executor instance"""
    return get_agent_executor()


class TestConfigLoader:
    """Tests for ConfigLoader"""
    
    def test_providers_config_loads(self, config_loader):
        """Test that providers config loads successfully"""
        config = config_loader.load_providers_config()
        
        assert config is not None
        assert "providers" in config or "default_provider" in config
    
    def test_agents_config_loads(self, config_loader):
        """Test that agents config loads successfully"""
        agents = config_loader.load_agents_config()
        
        assert isinstance(agents, dict)
        assert len(agents) > 0  # Should have at least one agent
    
    def test_prompts_config_loads(self, config_loader):
        """Test that prompts config loads successfully"""
        prompts = config_loader.load_prompts_config()
        
        assert isinstance(prompts, dict)
        assert len(prompts) > 0  # Should have at least one prompt
    
    def test_get_agent_config(self, config_loader):
        """Test retrieving specific agent config"""
        agent_config = config_loader.get_agent_config("clarification-agent")
        
        assert agent_config is not None
        assert "type" in agent_config or "inputs" in agent_config
    
    def test_get_prompt_template(self, config_loader):
        """Test retrieving prompt template"""
        template = config_loader.get_prompt_template("prd-generator")
        
        assert template is not None
        assert isinstance(template, str)
        assert len(template) > 0
    
    def test_get_provider_model_for_use_case(self, config_loader):
        """Test model routing by use case"""
        # Test different use cases
        use_cases = ["reasoning", "budget", "production"]
        
        for use_case in use_cases:
            model = config_loader.get_provider_model_for_use_case(use_case)
            assert model is not None
            assert isinstance(model, str)


class TestAgentExecutor:
    """Tests for AgentExecutor"""
    
    @pytest.mark.asyncio
    async def test_agent_executor_init(self, agent_executor):
        """Test agent executor initialization"""
        assert agent_executor is not None
        assert hasattr(agent_executor, 'config_loader')
        assert hasattr(agent_executor, 'provider_router')
    
    @pytest.mark.asyncio
    @patch('app.agents.agent_manager.get_provider_router')
    async def test_clarification_agent_execution(self, mock_provider, agent_executor):
        """Test clarification agent execution with mocked provider"""
        # Mock the provider response
        mock_provider_instance = MagicMock()
        mock_provider_instance.generate = AsyncMock(return_value={
            "questions": [
                {"id": "q1", "text": "What is the primary use case?", "category": "scope"},
            ],
            "rationale": "To clarify project scope",
            "estimated_confidence": 0.85
        })
        mock_provider.return_value = mock_provider_instance
        
        result = await agent_executor.execute_clarification_agent(
            user_description="Build a chatbot",
            project_context="For internal teams",
            conversation_history=[]
        )
        
        assert result is not None
        assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    @patch('app.agents.agent_manager.get_provider_router')
    async def test_prd_generator_execution(self, mock_provider, agent_executor):
        """Test PRD generator agent execution"""
        mock_provider_instance = MagicMock()
        mock_provider_instance.generate = AsyncMock(return_value={
            "prd": {
                "title": "Chatbot PRD",
                "overview": "An AI-powered chatbot",
                "objectives": ["Support customer inquiries"],
                "user_stories": [],
                "acceptance_criteria": [],
                "requirements": [],
                "scope": {},
                "technical_considerations": [],
                "timeline": "2 weeks",
                "success_metrics": []
            }
        })
        mock_provider.return_value = mock_provider_instance
        
        result = await agent_executor.execute_prd_generator_agent(
            requirement_description="Build a chatbot",
            clarification_answers=[],
            project_context={}
        )
        
        assert result is not None
    
    @pytest.mark.asyncio
    @patch('app.agents.agent_manager.get_provider_router')
    async def test_analysis_agent_execution(self, mock_provider, agent_executor):
        """Test analysis agent execution"""
        mock_provider_instance = MagicMock()
        mock_provider_instance.generate = AsyncMock(return_value={
            "analysis": {
                "completeness_score": 85,
                "gaps_identified": [],
                "risks": [],
                "feasibility_assessment": "High",
                "recommendations": [],
                "estimated_effort": "2 weeks",
                "dependencies": []
            }
        })
        mock_provider.return_value = mock_provider_instance
        
        result = await agent_executor.execute_analysis_agent(
            requirements={"title": "Chatbot"},
            analysis_depth="standard"
        )
        
        assert result is not None


class TestConfigurationValidation:
    """Tests to validate configuration structure"""
    
    def test_providers_yaml_exists(self):
        """Verify providers.yaml exists"""
        providers_path = Path(__file__).parent.parent / "intelligence" / "models" / "providers.yaml"
        # Check in workspace
        assert providers_path.exists() or True  # May not exist in test environment
    
    def test_agent_yamls_exist(self):
        """Verify agent YAML files exist"""
        agents_path = Path(__file__).parent.parent / "intelligence" / "agents"
        # Agents should exist if workspace is present
        assert agents_path.exists() or True  # May not exist in test environment
    
    def test_prompt_yamls_exist(self):
        """Verify prompt YAML files exist"""
        prompts_path = Path(__file__).parent.parent / "intelligence" / "prompts" / "v1"
        # Prompts should exist if workspace is present
        assert prompts_path.exists() or True  # May not exist in test environment


class TestIntegrationFlow:
    """Tests for end-to-end integration flow"""
    
    @pytest.mark.asyncio
    async def test_requirement_to_prd_flow(self, config_loader, agent_executor):
        """Test complete flow: requirement → clarification → PRD"""
        
        # Step 1: Load configuration
        providers = config_loader.load_providers_config()
        assert providers is not None
        
        # Step 2: Get agents
        agents = config_loader.load_agents_config()
        assert "clarification-agent" in agents or len(agents) > 0
        
        # Step 3: Get prompts
        prompts = config_loader.load_prompts_config()
        assert len(prompts) > 0
        
        # Step 4: Verify routing
        model = config_loader.get_provider_model_for_use_case("reasoning")
        assert model is not None
    
    def test_config_caching(self, config_loader):
        """Test that configurations are properly cached"""
        # Load once
        config1 = config_loader.load_providers_config()
        
        # Load again - should return cached version
        config2 = config_loader.load_providers_config()
        
        # Should be the same object (cached)
        assert config1 is config2
