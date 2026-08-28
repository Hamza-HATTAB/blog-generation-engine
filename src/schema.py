from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class BlogPost(BaseModel):
    """
    Pydantic schema representing structured blog post output.
    """
    title: str = Field(description="SEO-optimized blog title")
    content: str = Field(description="Comprehensive blog post content in Markdown format")
    language: str = Field(default="english", description="Target language of the post")


class BlogRequest(BaseModel):
    """
    FastAPI request payload schema.
    """
    topic: str = Field(..., description="Blog topic or concept query")
    target_language: Optional[str] = Field(default="english", description="Target output language (e.g., english, french, spanish, german, hindi)")


class BlogResponse(BaseModel):
    """
    FastAPI response payload schema.
    """
    status: str = Field(default="success")
    blog: BlogPost
    topic: str
    target_language: str
    quality_grade: Optional[int] = Field(default=9, description="Quality & readability grade out of 10")


class BlogState(TypedDict):
    """
    State dictionary used across LangGraph multi-agent nodes, supporting Corrective Quality Evaluation (Ch. 13 & 15).
    """
    topic: str
    target_language: str
    title: str
    content: str
    quality_grade: int
    refinement_feedback: str
    revision_count: int
    final_blog: Dict[str, Any]
