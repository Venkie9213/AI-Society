"""Slack message formatting utilities"""

from typing import Dict, Any, List, Optional
import json


def format_clarification_questions_for_slack(
    questions: List[Dict[str, Any]],
    rationale: str = "",
) -> tuple[str, List[Dict[str, Any]]]:
    """
    Format clarification questions for Slack display
    
    Returns: (text, blocks)
    """
    text_lines = ["🤔 **Clarification Questions**"]
    
    if rationale:
        text_lines.append(f"\n_{rationale}_\n")
    
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Clarification Questions*"
            }
        }
    ]
    
    if rationale:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"_{rationale}_"
            }
        })
    
    # Add each question
    for i, q in enumerate(questions, 1):
        question_text = q.get("text", "")
        category = q.get("category", "")
        priority = q.get("priority", "")
        
        text_lines.append(f"\n{i}. {question_text}")
        if category or priority:
            text_lines.append(f"   [{category} • {priority}]")
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{i}. {question_text}*\n_Category: {category} • Priority: {priority}_"
            }
        })
    
    text = "\n".join(text_lines)
    return text, blocks


def format_prd_for_slack(prd: Dict[str, Any]) -> tuple[str, List[Dict[str, Any]]]:
    """
    Format PRD for Slack display
    
    Returns: (text, blocks)
    """
    text_lines = ["📋 **Product Requirements Document (PRD)**"]
    
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*📋 Product Requirements Document*"
            }
        }
    ]
    
    # Add title
    if "title" in prd:
        text_lines.append(f"\n*Title:* {prd['title']}")
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Title:* {prd['title']}"
            }
        })
    
    # Add overview
    if "overview" in prd:
        text_lines.append(f"\n*Overview:* {prd['overview'][:200]}...")
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Overview:*\n{prd['overview'][:500]}"
            }
        })
    
    # Add sections
    sections = [
        ("objectives", "🎯 Objectives"),
        ("user_stories", "👥 User Stories"),
        ("acceptance_criteria", "✓ Acceptance Criteria"),
        ("requirements", "📋 Requirements"),
        ("scope", "📐 Scope"),
        ("timeline", "⏱️ Timeline"),
    ]
    
    for key, title in sections:
        if key in prd and prd[key]:
            items = prd[key] if isinstance(prd[key], list) else [prd[key]]
            text_lines.append(f"\n*{title}:*")
            
            # Add count in divider
            blocks.append({
                "type": "divider"
            })
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{title}* ({len(items)} items)"
                }
            })
            
            # Add first 3 items
            for item in items[:3]:
                item_text = item if isinstance(item, str) else item.get("description", str(item))
                text_lines.append(f"• {item_text[:100]}")
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"• {item_text[:200]}"
                    }
                })
            
            if len(items) > 3:
                text_lines.append(f"... and {len(items) - 3} more")
    
    text = "\n".join(text_lines)
    return text, blocks


def format_analysis_for_slack(analysis: Dict[str, Any]) -> tuple[str, List[Dict[str, Any]]]:
    """
    Format analysis results for Slack display
    
    Returns: (text, blocks)
    """
    text_lines = ["🔍 **Requirements Analysis**"]
    
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*🔍 Requirements Analysis*"
            }
        }
    ]
    
    # Completeness score
    if "completeness_score" in analysis:
        score = analysis["completeness_score"]
        emoji = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"
        text_lines.append(f"\n{emoji} *Completeness:* {score}%")
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{emoji} *Completeness Score:* {score}%"
            }
        })
    
    # Gaps
    if "gaps_identified" in analysis and analysis["gaps_identified"]:
        gaps = analysis["gaps_identified"]
        text_lines.append(f"\n⚠️ *Gaps Identified:* {len(gaps)} found")
        blocks.append({
            "type": "divider"
        })
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"⚠️ *Gaps Identified:* {len(gaps)} items"
            }
        })
        
        for gap in gaps[:3]:
            gap_text = gap if isinstance(gap, str) else gap.get("description", str(gap))
            text_lines.append(f"• {gap_text[:80]}")
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"• {gap_text[:200]}"
                }
            })
        
        if len(gaps) > 3:
            text_lines.append(f"... and {len(gaps) - 3} more gaps")
    
    # Risks
    if "risks" in analysis and analysis["risks"]:
        risks = analysis["risks"]
        text_lines.append(f"\n🚨 *Risks:* {len(risks)} identified")
        blocks.append({
            "type": "divider"
        })
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"🚨 *Risks:* {len(risks)} items"
            }
        })
        
        for risk in risks[:2]:
            risk_text = risk if isinstance(risk, str) else risk.get("description", str(risk))
            text_lines.append(f"• {risk_text[:80]}")
    
    # Recommendations
    if "recommendations" in analysis and analysis["recommendations"]:
        recs = analysis["recommendations"]
        text_lines.append(f"\n💡 *Recommendations:* {len(recs)} items")
        blocks.append({
            "type": "divider"
        })
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"💡 *Recommendations:* {len(recs)} items"
            }
        })
        
        for rec in recs[:2]:
            rec_text = rec if isinstance(rec, str) else rec.get("description", str(rec))
            text_lines.append(f"• {rec_text[:80]}")
    
    # Effort estimation
    if "effort_estimation" in analysis:
        effort = analysis["effort_estimation"]
        text_lines.append(f"\n📊 *Effort:* {effort} story points")
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"📊 *Effort Estimation:* {effort} story points"
            }
        })
    
    text = "\n".join(text_lines)
    return text, blocks
