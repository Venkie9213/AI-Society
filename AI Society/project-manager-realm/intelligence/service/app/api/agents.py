# app/api/agents.py
"""Agent execution endpoints - Thin HTTP handlers."""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
import structlog
import time

from app.orchestration import get_agent_orchestrator
from app.loaders import (
    get_agent_loader,
    get_prompt_loader,
    get_provider_loader,
)
from app.schemas import AgentExecutionResponse

logger = structlog.get_logger()

router = APIRouter()


@router.post("/agents/clarify", response_model=AgentExecutionResponse)
async def clarify_requirement(
    user_description: str,
    project_context: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """Execute clarification agent to generate clarifying questions."""
    start_time = time.time()
    
    try:
        orchestrator = get_agent_orchestrator()
        result = await orchestrator.execute_clarification_agent(
            user_description=user_description,
            project_context=project_context,
            conversation_history=conversation_history,
        )
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            "clarification_agent_executed",
            duration_ms=duration_ms,
            status="success"
        )
        
        return {
            "agent": "clarification-agent",
            "status": "success",
            "result": result.dict(),
            "duration_ms": duration_ms,
        }
    
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "clarification_agent_failed",
            error=str(e),
            duration_ms=duration_ms
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/generate-prd", response_model=AgentExecutionResponse)
async def generate_prd(
    requirement_description: str,
    clarification_answers: List[Dict[str, str]],
    project_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Execute PRD generator agent to create formal PRD."""
    start_time = time.time()
    
    try:
        orchestrator = get_agent_orchestrator()
        result = await orchestrator.execute_prd_generator_agent(
            requirement_description=requirement_description,
            clarification_answers=clarification_answers,
            project_context=project_context,
        )
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            "prd_generator_agent_executed",
            duration_ms=duration_ms,
            status="success"
        )
        
        return {
            "agent": "prd-generator-agent",
            "status": "success",
            "result": result.dict(),
            "duration_ms": duration_ms,
        }
    
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "prd_generator_agent_failed",
            error=str(e),
            duration_ms=duration_ms
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/analyze", response_model=AgentExecutionResponse)
async def analyze_requirements(
    requirements: Dict[str, Any],
    analysis_depth: str = "standard",
) -> Dict[str, Any]:
    """Execute analysis agent to validate requirements."""
    start_time = time.time()
    
    try:
        orchestrator = get_agent_orchestrator()
        result = await orchestrator.execute_analysis_agent(
            requirements=requirements,
            analysis_depth=analysis_depth,
        )
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            "analysis_agent_executed",
            depth=analysis_depth,
            duration_ms=duration_ms,
            status="success"
        )
        
        return {
            "agent": "analysis-agent",
            "status": "success",
            "result": result.dict(),
            "duration_ms": duration_ms,
        }
    
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "analysis_agent_failed",
            error=str(e),
            depth=analysis_depth,
            duration_ms=duration_ms
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents")
async def list_agents() -> Dict[str, Any]:
    """List available agents."""
    try:
        agent_loader = get_agent_loader()
        agents = agent_loader.list_agents()
        
        agents_list = []
        for agent_name in agents:
            config = agent_loader.get_agent_config(agent_name)
            if config:
                agents_list.append({
                    "name": agent_name,
                    "description": config.get("description", ""),
                    "version": config.get("version"),
                })
        
        logger.info("agents_listed", count=len(agents_list))
        
        return {"agents": agents_list, "total": len(agents_list)}
    
    except Exception as e:
        logger.error("agents_list_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prompts")
async def list_prompts() -> Dict[str, Any]:
    """List available prompt templates."""
    try:
        prompt_loader = get_prompt_loader()
        prompts = prompt_loader.list_prompts()
        
        prompts_list = [{"name": name} for name in prompts]
        
        logger.info("prompts_listed", count=len(prompts_list))
        
        return {"prompts": prompts_list, "total": len(prompts_list)}
    
    except Exception as e:
        logger.error("prompts_list_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/providers")
async def get_providers_config() -> Dict[str, Any]:
    """Get current provider configuration."""
    try:
        provider_loader = get_provider_loader()
        config = provider_loader.load_providers()
        
        logger.info("providers_config_retrieved")
        
        return config
    
    except Exception as e:
        logger.error("providers_config_retrieval_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
