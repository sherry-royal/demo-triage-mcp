"""
Enterprise Triage Assistant - Full MCP Demo
Deployed via FastMCP

Showcases all MCP capabilities:
- Tools (Actions)
- Resources (Data Reading)
- Prompts (Templates)
"""
import json
import logging
import random
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional

from fastmcp import FastMCP, Context
from pydantic import BaseModel, Field, field_validator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize the Server
mcp = FastMCP("Enterprise-Triage-Assistant")

# ============================================================================
# STATE MANAGEMENT: In-Memory Database
# ============================================================================

class TicketPriority(str, Enum):
    """Ticket priority levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TicketStatus(str, Enum):
    """Ticket status values."""
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class Ticket(BaseModel):
    """Ticket data model with Pydantic validation."""
    id: int
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    priority: TicketPriority
    status: TicketStatus = TicketStatus.OPEN
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    assigned_to: Optional[str] = None

    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title cannot be empty or whitespace only")
        return v.strip()


# In-memory ticket database
_tickets_db: List[Ticket] = []
_next_ticket_id: int = 1

# Activity logs for system://logs resource
_activity_logs: List[str] = []


def _log_activity(message: str) -> None:
    """Add a log entry and keep only last 50 entries."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    _activity_logs.append(log_entry)
    logger.info(message)
    # Keep only last 50 logs
    if len(_activity_logs) > 50:
        _activity_logs.pop(0)


def _initialize_database() -> None:
    """Pre-populate the database with dummy tickets."""
    global _next_ticket_id
    
    # Create first ticket (HIGH priority)
    ticket1 = Ticket(
        id=_next_ticket_id,
        title="System Outage - Payment Processing Down",
        description="Users cannot complete payments. Error 500 on checkout endpoint.",
        priority=TicketPriority.HIGH,
        status=TicketStatus.OPEN,
        assigned_to="SRE Team"
    )
    _tickets_db.append(ticket1)
    _next_ticket_id += 1
    
    # Create second ticket (LOW priority)
    ticket2 = Ticket(
        id=_next_ticket_id,
        title="Feature Request: Dark Mode",
        description="Users have requested a dark mode theme for the application.",
        priority=TicketPriority.LOW,
        status=TicketStatus.OPEN,
        assigned_to=None
    )
    _tickets_db.append(ticket2)
    _next_ticket_id += 1
    
    # Create third ticket (MEDIUM priority)
    ticket3 = Ticket(
        id=_next_ticket_id,
        title="Login Page Loading Slowly",
        description="Users report 5-10 second load times on the login page.",
        priority=TicketPriority.MEDIUM,
        status=TicketStatus.IN_PROGRESS,
        assigned_to="App Support"
    )
    _tickets_db.append(ticket3)
    _next_ticket_id += 1
    
    _log_activity("Database initialized with 3 pre-populated tickets")


# Initialize on module load
_initialize_database()


# ============================================================================
# RESOURCES: Dynamic Data Reading
# ============================================================================

@mcp.resource("system://health")
def get_system_health() -> str:
    """
    Returns the current operational health of the Triage Assistant.
    Used by dashboards to verify the agent is alive.
    """
    status = "OPERATIONAL"
    load = random.randint(12, 45)
    open_tickets = len([t for t in _tickets_db if t.status != TicketStatus.CLOSED])
    
    return json.dumps({
        "status": status,
        "cpu_load_percent": load,
        "memory": "OK",
        "open_tickets": open_tickets,
        "total_tickets": len(_tickets_db)
    }, indent=2)


@mcp.resource("system://ticket_queue")
def get_ticket_queue() -> str:
    """
    Returns a JSON list of all open tickets (not closed).
    This resource is referenced in the triage_expert prompt.
    """
    open_tickets = [
        ticket.model_dump()
        for ticket in _tickets_db
        if ticket.status != TicketStatus.CLOSED
    ]
    
    return json.dumps({
        "tickets": open_tickets,
        "count": len(open_tickets),
        "retrieved_at": datetime.now().isoformat()
    }, indent=2)


@mcp.resource("system://logs")
def get_system_logs() -> str:
    """
    Returns the last 5 server activity logs.
    Simulates a log monitoring system.
    """
    recent_logs = _activity_logs[-5:] if len(_activity_logs) >= 5 else _activity_logs
    
    return json.dumps({
        "logs": recent_logs,
        "total_logs": len(_activity_logs),
        "showing_last": len(recent_logs)
    }, indent=2)


# ============================================================================
# TOOLS: Actions (Complex Operations)
# ============================================================================

@mcp.tool()
def create_ticket(
    title: str,
    priority: TicketPriority,
    description: str = "",
    ctx: Optional[Context] = None
) -> str:
    """
    Creates a new support ticket and adds it to the database.
    
    Args:
        title: The ticket title (1-200 characters, required).
        priority: The priority level (LOW, MEDIUM, HIGH, CRITICAL).
        description: Optional detailed description of the issue.
        ctx: MCP context for logging (automatically injected).
    
    Returns:
        JSON string with the created ticket details.
    """
    global _next_ticket_id
    
    try:
        # Pydantic validation happens automatically
        new_ticket = Ticket(
            id=_next_ticket_id,
            title=title,
            description=description,
            priority=priority,
            status=TicketStatus.OPEN
        )
        
        _tickets_db.append(new_ticket)
        _next_ticket_id += 1
        
        _log_activity(f"Created ticket #{new_ticket.id}: {title} ({priority.value})")
        
        if ctx:
            ctx.info(f"Ticket #{new_ticket.id} created successfully")
        
        return json.dumps({
            "success": True,
            "message": f"Ticket #{new_ticket.id} created successfully",
            "ticket": new_ticket.model_dump()
        }, indent=2)
        
    except Exception as e:
        error_msg = f"Failed to create ticket: {str(e)}"
        _log_activity(f"ERROR: {error_msg}")
        if ctx:
            ctx.error(error_msg)
        
        return json.dumps({
            "success": False,
            "error": error_msg
        }, indent=2)


@mcp.tool()
def update_ticket_status(
    ticket_id: int,
    status: TicketStatus,
    ctx: Optional[Context] = None
) -> str:
    """
    Updates the status of an existing ticket.
    
    Args:
        ticket_id: The ID of the ticket to update.
        status: The new status (OPEN, IN_PROGRESS, RESOLVED, CLOSED).
        ctx: MCP context for logging (automatically injected).
    
    Returns:
        JSON string with the update result.
    """
    try:
        # Find the ticket
        ticket = next((t for t in _tickets_db if t.id == ticket_id), None)
        
        if not ticket:
            error_msg = f"Ticket #{ticket_id} not found"
            _log_activity(f"ERROR: {error_msg}")
            if ctx:
                ctx.error(error_msg)
            
            return json.dumps({
                "success": False,
                "error": error_msg,
                "available_ticket_ids": [t.id for t in _tickets_db]
            }, indent=2)
        
        # Update status
        old_status = ticket.status
        ticket.status = status
        ticket.updated_at = datetime.now().isoformat()
        
        _log_activity(f"Updated ticket #{ticket_id}: {old_status} -> {status}")
        
        if ctx:
            ctx.info(f"Ticket #{ticket_id} status updated to {status.value}")
        
        return json.dumps({
            "success": True,
            "message": f"Ticket #{ticket_id} status updated to {status.value}",
            "ticket": ticket.model_dump()
        }, indent=2)
        
    except Exception as e:
        error_msg = f"Failed to update ticket #{ticket_id}: {str(e)}"
        _log_activity(f"ERROR: {error_msg}")
        if ctx:
            ctx.error(error_msg)
        
        return json.dumps({
            "success": False,
            "error": error_msg
        }, indent=2)


@mcp.tool()
def search_knowledge_base(query: str, ctx: Optional[Context] = None) -> str:
    """
    Searches the knowledge base for relevant articles based on keywords.
    This is a mock implementation that simulates a real knowledge base search.
    
    Args:
        query: The search query string.
        ctx: MCP context for logging (automatically injected).
    
    Returns:
        JSON string with relevant articles matching the query.
    """
    # Mock knowledge base articles
    knowledge_base: Dict[str, List[Dict[str, str]]] = {
        "payment": [
            {
                "id": "KB-001",
                "title": "Payment Processing Troubleshooting",
                "content": "Common issues: Check gateway connectivity, verify API keys, review transaction logs.",
                "category": "Payments"
            },
            {
                "id": "KB-002",
                "title": "Payment Gateway Integration Guide",
                "content": "Step-by-step guide for integrating payment gateways. Requires API credentials.",
                "category": "Payments"
            }
        ],
        "login": [
            {
                "id": "KB-003",
                "title": "Login Issues Resolution",
                "content": "Reset password, clear cache, check session timeout settings (default: 30 min).",
                "category": "Authentication"
            },
            {
                "id": "KB-004",
                "title": "SSO Configuration",
                "content": "Single Sign-On setup requires SAML 2.0 configuration and certificate management.",
                "category": "Authentication"
            }
        ],
        "performance": [
            {
                "id": "KB-005",
                "title": "Performance Optimization Checklist",
                "content": "1. Check database query performance 2. Review CDN cache settings 3. Monitor API response times.",
                "category": "Performance"
            }
        ],
        "api": [
            {
                "id": "KB-006",
                "title": "API Rate Limiting",
                "content": "Default rate limit: 1000 requests/hour per API key. Contact support for increases.",
                "category": "API"
            }
        ]
    }
    
    query_lower = query.lower()
    relevant_articles: List[Dict[str, str]] = []
    
    # Simple keyword matching
    for keyword, articles in knowledge_base.items():
        if keyword in query_lower:
            relevant_articles.extend(articles)
    
    # If no matches, return a general article
    if not relevant_articles:
        relevant_articles = [{
            "id": "KB-GENERAL",
            "title": "General Support Guidelines",
            "content": "For assistance, please provide detailed error messages and steps to reproduce the issue.",
            "category": "General"
        }]
    
    _log_activity(f"Knowledge base search: '{query}' -> {len(relevant_articles)} results")
    
    if ctx:
        ctx.info(f"Found {len(relevant_articles)} relevant articles")
    
    return json.dumps({
        "query": query,
        "results_count": len(relevant_articles),
        "articles": relevant_articles
    }, indent=2)


# ============================================================================
# PROMPTS: Reusable Templates
# ============================================================================

@mcp.prompt()
def triage_expert() -> str:
    """
    Returns a system message template for a Senior Support Engineer.
    This prompt references the system://ticket_queue resource to provide context.
    
    The AI should review the ticket queue and suggest next steps.
    """
    return """You are a Senior Support Engineer with 10+ years of experience in enterprise support systems.

Your role is to:
1. Review the current ticket queue (available at system://ticket_queue)
2. Analyze ticket priorities, statuses, and assignments
3. Suggest the next steps for triage and resolution
4. Identify any tickets that need immediate attention or escalation

Please review the ticket queue and provide:
- A summary of the current ticket status
- Recommendations for prioritization
- Suggested assignments or escalations
- Any patterns or trends you notice

Remember to consider:
- High priority tickets should be addressed first
- Unassigned tickets may need routing
- Tickets in progress should be monitored
- Closed tickets indicate successful resolution

Use the available tools (create_ticket, update_ticket_status, search_knowledge_base) to take action as needed."""


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    _log_activity("Enterprise Triage Assistant MCP Server starting...")
    logger.info("Server initialized with:")
    logger.info(f"  - {len(_tickets_db)} tickets in database")
    logger.info(f"  - {len([t for t in _tickets_db if t.status != TicketStatus.CLOSED])} open tickets")
    logger.info("  - Resources: system://health, system://ticket_queue, system://logs")
    logger.info("  - Tools: create_ticket, update_ticket_status, search_knowledge_base")
    logger.info("  - Prompts: triage_expert")
    mcp.run()
