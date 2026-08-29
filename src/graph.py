import logging
from typing import Literal
from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.graph import StateGraph, START, END

from src.schema import BlogState
from src.nodes import BlogNodes

logger = logging.getLogger(__name__)


class BlogGraphBuilder:
    """
    Advanced Multi-Agent LangGraph workflow featuring Corrective Quality Evaluation (Ch. 13 & 15).
    Flow: START -> generate_title -> generate_content -> evaluate_quality -> (pass) -> translate_content -> END
                                                               |
                                                          (grade < 7) -> generate_content
    """
    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        self.nodes = BlogNodes(llm=llm)

    def route_quality_check(self, state: BlogState) -> Literal["translate_content", "generate_content"]:
        """Conditional router based on evaluator quality grade."""
        grade = state.get("quality_grade", 9)
        if grade >= 7:
            return "translate_content"
        else:
            logger.info("Quality grade below threshold. Triggering content refinement loop...")
            return "generate_content"

    def build_graph(self):
        """Construct state machine graph."""
        builder = StateGraph(BlogState)

        builder.add_node("generate_title", self.nodes.generate_title_node)
        builder.add_node("generate_content", self.nodes.generate_content_node)
        builder.add_node("evaluate_quality", self.nodes.evaluate_quality_node)
        builder.add_node("translate_content", self.nodes.translate_content_node)

        builder.add_edge(START, "generate_title")
        builder.add_edge("generate_title", "generate_content")
        builder.add_edge("generate_content", "evaluate_quality")

        builder.add_conditional_edges(
            "evaluate_quality",
            self.route_quality_check,
            {
                "translate_content": "translate_content",
                "generate_content": "generate_content"
            }
        )

        builder.add_edge("translate_content", END)

        return builder.compile()
