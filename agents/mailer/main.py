"""A2A-compliant Mailer agent that sends email notifications via Gmail MCP server."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Optional

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from typing_extensions import Annotated, TypedDict
import structlog

from agents.base import BaseA2AAgent
from config import get_settings, setup_logging


logger = structlog.get_logger(__name__)


class EmailNotification(BaseModel):
    """Email notification data structure."""
    to: List[str] = Field(description="List of recipient email addresses")
    subject: str = Field(description="Email subject line")
    body: str = Field(description="Email body content")
    html_body: Optional[str] = Field(default=None, description="HTML email body")
    cc: Optional[List[str]] = Field(default=None, description="CC recipients")
    bcc: Optional[List[str]] = Field(default=None, description="BCC recipients")


class MailerState(TypedDict):
    """State for the Mailer agent LangGraph workflow."""
    messages: Annotated[list, add_messages]
    trade_plan: Optional[Dict[str, Any]]
    email_notification: Optional[EmailNotification]
    email_sent: bool
    error: Optional[str]


class MailerAgent(BaseA2AAgent):
    """A2A-compliant Mailer agent for sending email notifications."""

    def __init__(self):
        settings = get_settings()
        
        # MCP servers for email services (stdio configuration)
        mcp_servers = {
            "gmail": {
                "command": "npx",
                "args": ["@modelcontextprotocol/server-gmail"],
                "env": {
                    "GMAIL_CREDENTIALS_PATH": settings.gmail_credentials_path,
                    "GMAIL_TOKEN_PATH": settings.gmail_token_path
                }
            }
        }
        
        capabilities = {
            "email_notifications": True,
            "trade_alerts": True,
            "notification_templates": True,
            "google_a2a_compatible": True
        }
        
        super().__init__(
            name="Mailer",
            description="Email notification agent for trading alerts and reports",
            url=settings.mailer_url,
            version="1.0.0",
            mcp_servers=mcp_servers,
            capabilities=capabilities
        )
        
        self.settings = settings
        self.llm = self._setup_llm()
        self.workflow = None

    def _setup_llm(self) -> Any:
        """Setup the LLM (OpenAI or Anthropic)"""
        if self.settings.openai_api_key:
            return ChatOpenAI(
                model="gpt-4",
                temperature=0.3,
                api_key=self.settings.openai_api_key
            )
        elif self.settings.anthropic_api_key:
            return ChatAnthropic(
                model="claude-3-opus-20240229",
                temperature=0.3,
                api_key=self.settings.anthropic_api_key
            )
        else:
            raise ValueError("No LLM API key configured")
    
    def get_agent_card(self) -> Dict[str, Any]:
        """Return detailed agent card for discovery"""
        return {
            "name": self.agent_card.name,
            "description": self.agent_card.description,
            "version": self.agent_card.version,
            "url": self.agent_card.url,
            "capabilities": self.agent_card.capabilities,
            "endpoints": {
                "health": f"{self.agent_card.url}/health",
                "discovery": f"{self.agent_card.url}/.well-known/agent.json",
                "send_email": f"{self.agent_card.url}/send_email"
            },
            "mcp_servers": list(self.mcp_servers_config.keys()),
            "status": "active"
        }

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for email processing."""
        
        async def process_trade_plan(state: MailerState) -> MailerState:
            """Process incoming trade plan and prepare email notification."""
            try:
                trade_plan = state.get("trade_plan")
                if not trade_plan:
                    return {**state, "error": "No trade plan provided"}
                
                logger.info("Processing trade plan for email notification", 
                           extra={"trade_plan_id": trade_plan.get("id")})
                
                # Use LLM to compose professional email
                email_prompt = f"""
                Compose a professional email notification for the following trading plan:
                
                {json.dumps(trade_plan, indent=2)}
                
                Include:
                - Clear subject line with trade symbol and action
                - Professional greeting
                - Summary of the trade plan
                - Key details (symbol, action, reasoning)
                - Risk disclaimer
                - Professional closing
                
                Format as a professional financial notification.
                """
                
                response = await self.llm.ainvoke([{"role": "user", "content": email_prompt}])
                
                # Extract email components from LLM response
                email_content = response.content
                
                # Simple parsing - in production, use more robust method
                lines = email_content.split('\n')
                subject = "Trade Plan Notification"
                body = email_content
                  # Look for subject line in response
                for line in lines:
                    if line.strip().lower().startswith("subject:"):
                        subject = line.split(":", 1)[1].strip()
                        break
                
                email_notification = EmailNotification(
                    to=[self.settings.default_email_recipient],
                    subject=subject,
                    body=body,
                    cc=self.settings.email_cc_recipients if self.settings.email_cc_recipients else None
                )
                
                return {
                    **state,
                    "email_notification": email_notification,
                    "messages": state["messages"] + [
                        {"role": "assistant", "content": f"Composed email notification: {subject}"}
                    ]
                }
                
            except Exception as e:
                logger.error("Error processing trade plan", extra={"error": str(e)})
                return {**state, "error": f"Failed to process trade plan: {str(e)}"}

        async def send_email(state: MailerState) -> MailerState:
            """Send email notification via Gmail MCP server."""
            try:
                email_notification = state.get("email_notification")
                if not email_notification:
                    return {**state, "error": "No email notification prepared"}
                
                # Use MCP Gmail tool to send email
                gmail_tools = await self.get_mcp_tools("gmail")
                send_email_tool = None
                
                for tool in gmail_tools:
                    if tool.name == "send_email":
                        send_email_tool = tool
                        break
                
                if not send_email_tool:
                    return {**state, "error": "Gmail send_email tool not available"}
                
                # Prepare email data for Gmail MCP
                email_data = {
                    "to": email_notification.to,
                    "subject": email_notification.subject,
                    "body": email_notification.body,
                    "mimeType": "text/html" if email_notification.html_body else "text/plain"
                }
                
                if email_notification.html_body:
                    email_data["htmlBody"] = email_notification.html_body
                    email_data["mimeType"] = "multipart/alternative"
                
                if email_notification.cc:
                    email_data["cc"] = email_notification.cc
                
                if email_notification.bcc:
                    email_data["bcc"] = email_notification.bcc
                
                # Send email via MCP
                result = await send_email_tool.ainvoke(email_data)
                
                logger.info("Email sent successfully", 
                           extra={"recipients": email_notification.to, "subject": email_notification.subject})
                
                return {
                    **state,
                    "email_sent": True,
                    "messages": state["messages"] + [
                        {"role": "assistant", "content": f"Email sent successfully to {', '.join(email_notification.to)}"}
                    ]
                }
                
            except Exception as e:
                logger.error("Error sending email", extra={"error": str(e)})
                return {**state, "error": f"Failed to send email: {str(e)}"}

        # Build workflow graph
        workflow = StateGraph(MailerState)
        
        # Add nodes
        workflow.add_node("process_trade_plan", process_trade_plan)
        workflow.add_node("send_email", send_email)
        
        # Add edges
        workflow.add_edge(START, "process_trade_plan")
        workflow.add_edge("process_trade_plan", "send_email")
        workflow.add_edge("send_email", END)
        
        return workflow.compile()

    async def handle_trade_plan_notification(self, trade_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming trade plan notification."""
        logger.info("Received trade plan notification", 
                   extra={"trade_plan_id": trade_plan.get("id", "unknown")})
        
        # Execute workflow
        initial_state: MailerState = {
            "messages": [],
            "trade_plan": trade_plan,
            "email_notification": None,
            "email_sent": False,
            "error": None
        }
        
        final_state = await self.workflow.ainvoke(initial_state)
        
        if final_state.get("error"):
            return {
                "success": False,
                "error": final_state["error"],
                "agent": self.agent_name
            }
        
        return {
            "success": True,
            "email_sent": final_state.get("email_sent", False),
            "recipients": final_state["email_notification"].to if final_state.get("email_notification") else [],
            "agent": self.agent_name
        }

    def get_agent_card(self) -> Dict[str, Any]:
        """Return agent card for A2A discovery."""
        return {
            "name": self.agent_name,
            "description": self.agent_description,
            "version": "1.0.0",
            "capabilities": [
                "send_email_notifications",
                "compose_trade_alerts",
                "gmail_integration"
            ],
            "endpoints": [
                {
                    "path": "/trade-notification",
                    "method": "POST",
                    "description": "Send email notification for trade plan",
                    "parameters": {
                        "trade_plan": {
                            "type": "object",
                            "description": "Trading plan to notify about"
                        }
                    }
                }
            ],
            "mcp_servers": ["gmail"],
            "contact": "mailer@stockripper.com"
        }

    async def setup_routes(self):
        """Setup FastAPI routes for the Mailer agent."""
        
        @self.app.post("/trade-notification")
        async def trade_notification_endpoint(request_data: dict):
            """Endpoint to handle trade plan notifications."""
            trade_plan = request_data.get("trade_plan")
            if not trade_plan:
                return {"error": "trade_plan is required", "success": False}
            
            result = await self.handle_trade_plan_notification(trade_plan)
            return result


async def main():
    """Main entry point for the Mailer agent."""
    agent = MailerAgent()
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())

# Contains AI-generated edits.
