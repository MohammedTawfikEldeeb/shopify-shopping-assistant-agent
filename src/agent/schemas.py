from pydantic import BaseModel, Field


class AgentDecision(BaseModel):
    thought: str = Field(description="Step-by-step reasoning about the user's intent")
    action: str = Field(description="Action to take: retrieve, sql_query, or answer")
    content: str = Field(description="The content: search query, SQL query, or direct answer")
