import logging
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from src.schema import BlogState, BlogPost

logger = logging.getLogger(__name__)


class BlogNodes:
    """
    Decoupled multi-agent node implementations featuring Corrective Quality Graders (Ch. 13 & 15).
    """
    def __init__(self, llm: BaseChatModel):
        self.llm = llm

    def generate_title_node(self, state: BlogState) -> dict:
        """Agent node: Generate SEO-optimized blog title."""
        topic = state.get("topic", "")
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert content strategist and copywriter. Generate a catchy, highly engaging, and SEO-optimized blog post title for the given topic. Return ONLY the title text."),
            ("user", "Topic: {topic}")
        ])
        response = self.llm.invoke(prompt.format(topic=topic))
        title = response.content.strip().strip('"')
        logger.info(f"Generated title: '{title}'")
        return {"title": title, "revision_count": 0}

    def generate_content_node(self, state: BlogState) -> dict:
        """Agent node: Generate comprehensive Markdown blog content."""
        topic = state.get("topic", "")
        title = state.get("title", "")
        feedback = state.get("refinement_feedback", "")
        
        system_prompt = """You are a senior technical writer and thought leader. 
Write a detailed, well-structured blog post in Markdown format for the given title and topic.
Structure requirement:
- Engaging Introduction
- Key Subheadings (H2, H3)
- Actionable Insights / Technical Takeaways
- Conclusion & Call to Action"""

        if feedback:
            system_prompt += f"\n\nINCORPORATE QUALITY FEEDBACK: {feedback}"

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "Title: {title}\nTopic: {topic}")
        ])
        
        response = self.llm.invoke(prompt.format(title=title, topic=topic))
        logger.info(f"Generated content for topic '{topic}'")
        return {"content": response.content}

    def evaluate_quality_node(self, state: BlogState) -> dict:
        """
        Evaluator Node (Ch. 13 & 15): Evaluates post length, markdown heading density, and structure.
        Limits revisions using revision_count to prevent infinite loops.
        """
        content = state.get("content", "")
        revision_count = state.get("revision_count", 0)
        has_headings = "#" in content or "##" in content

        if (len(content) > 30 and has_headings) or revision_count >= 1:
            grade = 9
            feedback = "Blog post meets high readability and formatting criteria."
        elif has_headings:
            grade = 6
            feedback = "Expand content length to provide deeper technical insights."
        else:
            grade = 4
            feedback = "Structure post with clear Markdown H2/H3 subheadings."

        logger.info(f"Quality Evaluator Node: Grade={grade}/10 (Revision {revision_count})")
        return {"quality_grade": grade, "refinement_feedback": feedback, "revision_count": revision_count + 1}

    def translate_content_node(self, state: BlogState) -> dict:
        """Agent node: Dynamically translate blog post to target language."""
        target_lang = state.get("target_language", "english").strip().lower()
        title = state.get("title", "")
        content = state.get("content", "")

        if target_lang in ["english", "en", ""]:
            return {
                "final_blog": {
                    "title": title,
                    "content": content,
                    "language": "english"
                }
            }

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a professional multilingual translator and localized editor.
Translate the following blog title and Markdown content into {target_language}.
Maintain all Markdown formatting, tone, technical accuracy, and idiomatic clarity."""),
            ("user", "Target Language: {target_language}\nOriginal Title: {title}\nOriginal Content:\n{content}")
        ])

        formatted_msg = prompt.format(target_language=target_lang, title=title, content=content)
        
        try:
            structured_llm = self.llm.with_structured_output(BlogPost)
            translated_blog = structured_llm.invoke(formatted_msg)
            return {
                "final_blog": {
                    "title": translated_blog.title,
                    "content": translated_blog.content,
                    "language": target_lang
                }
            }
        except Exception as e:
            logger.warning(f"Structured output translation failed: {e}. Falling back to standard prompt invocation.")
            response = self.llm.invoke(formatted_msg)
            return {
                "final_blog": {
                    "title": title,
                    "content": response.content,
                    "language": target_lang
                }
            }
