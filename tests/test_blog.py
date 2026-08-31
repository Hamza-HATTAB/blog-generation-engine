import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from api import app
from src.schema import BlogRequest, BlogPost
from src.nodes import BlogNodes
from src.graph import BlogGraphBuilder

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_blog_nodes_mock():
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = AIMessage(content="Generated Title")

    nodes = BlogNodes(llm=mock_llm)
    title_res = nodes.generate_title_node({"topic": "AI in Robotics"})
    assert title_res["title"] == "Generated Title"


def test_quality_evaluator_and_graph_compilation():
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = AIMessage(content="## Section Heading\n\nThis is detailed sample blog content with technical depth.")
    
    mock_structured = MagicMock()
    mock_structured.invoke.return_value = BlogPost(
        title="Titre en Français",
        content="## Section\n\nContenu du blog en français.",
        language="french"
    )
    mock_llm.with_structured_output.return_value = mock_structured

    builder = BlogGraphBuilder(llm=mock_llm)
    graph = builder.build_graph()
    assert graph is not None

    initial_state = {
        "topic": "AI Trends",
        "target_language": "french",
        "title": "",
        "content": "",
        "quality_grade": 0,
        "refinement_feedback": "",
        "final_blog": {}
    }

    result = graph.invoke(initial_state)
    assert result["quality_grade"] >= 6
    assert result["final_blog"]["language"] == "french"
