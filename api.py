import os
import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from langchain_groq import ChatGroq

from src.schema import BlogRequest, BlogResponse, BlogPost
from src.graph import BlogGraphBuilder
from src.config import settings

app = FastAPI(
    title="Multi-Agent Blog Generation Engine API",
    description="Production REST API for automated blog writing, structuring, quality evaluation, and dynamic translation powered by LangGraph & Groq LLMs.",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "blog-generation-engine"}


@app.post("/api/v1/blogs", response_model=BlogResponse, tags=["Blog Generation"])
async def generate_blog(request: BlogRequest):
    """
    Generate an SEO-optimized blog post with dynamic translation and quality evaluation.
    """
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GROQ_API_KEY is not configured on the server."
        )

    try:
        llm = ChatGroq(
            groq_api_key=groq_key,
            model_name=settings.default_model,
            temperature=0.7
        )
        
        builder = BlogGraphBuilder(llm=llm)
        graph = builder.build_graph()

        initial_state = {
            "topic": request.topic,
            "target_language": request.target_language or "english",
            "title": "",
            "content": "",
            "quality_grade": 0,
            "refinement_feedback": "",
            "final_blog": {}
        }

        result = graph.invoke(initial_state)
        final_blog_data = result.get("final_blog", {})

        blog_post = BlogPost(
            title=final_blog_data.get("title", result.get("title", "Untitled Blog")),
            content=final_blog_data.get("content", result.get("content", "")),
            language=final_blog_data.get("language", request.target_language or "english")
        )

        return BlogResponse(
            status="success",
            blog=blog_post,
            topic=request.topic,
            target_language=blog_post.language,
            quality_grade=result.get("quality_grade", 9)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Blog generation graph execution failed: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run("api:app", host=settings.host, port=settings.port, reload=True)
