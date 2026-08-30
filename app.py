import os
import streamlit as st
from langchain_groq import ChatGroq

from src.graph import BlogGraphBuilder

st.set_page_config(
    page_title="Multi-Agent Blog Engine",
    layout="wide"
)

st.title("Multi-Agent Blog Generation Engine")
st.caption("Automated Content Creation & Dynamic Multilingual Translation with Corrective Quality Graders")

# Sidebar
with st.sidebar:
    st.header("Configuration")
    groq_key = st.text_input("Groq API Key", type="password", value=os.getenv("GROQ_API_KEY", ""))
    if groq_key:
        os.environ["GROQ_API_KEY"] = groq_key

    target_language = st.selectbox(
        "Target Output Language",
        ["English", "French", "Spanish", "German", "Hindi", "Arabic", "Japanese"],
        index=0
    )
    
    model_name = st.selectbox(
        "Select Model",
        ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"],
        index=0
    )

# Main UI Form
with st.form("blog_form"):
    topic_input = st.text_input("Enter Blog Topic / Key Concept", placeholder="e.g. The Future of Quantum Computing in Cryptography")
    submit_button = st.form_submit_button("Generate Blog Post", use_container_width=True)

if submit_button:
    if not topic_input.strip():
        st.error("Please enter a valid topic.")
        st.stop()
        
    if not os.getenv("GROQ_API_KEY"):
        st.error("Please provide a Groq API Key in the sidebar.")
        st.stop()

    try:
        with st.spinner("Multi-agent team generating outline, content, evaluating quality, and translating..."):
            llm = ChatGroq(
                groq_api_key=os.getenv("GROQ_API_KEY"),
                model_name=model_name,
                temperature=0.7
            )
            
            builder = BlogGraphBuilder(llm=llm)
            graph = builder.build_graph()

            initial_state = {
                "topic": topic_input,
                "target_language": target_language.lower(),
                "title": "",
                "content": "",
                "quality_grade": 0,
                "refinement_feedback": "",
                "revision_count": 0,
                "final_blog": {}
            }

            result = graph.invoke(initial_state)
            final_blog = result.get("final_blog", {})

            title = final_blog.get("title", result.get("title", "Generated Blog"))
            content = final_blog.get("content", result.get("content", ""))
            lang = final_blog.get("language", target_language)

            st.metric(label="Evaluator Readability & Quality Grade", value=f"{result.get('quality_grade', 9)}/10")

            st.success(f"Blog post successfully generated in `{lang.capitalize()}`")
            
            st.subheader(title)
            st.markdown(content)

            st.download_button(
                label="Download Blog Post (Markdown)",
                data=f"# {title}\n\n{content}",
                file_name=f"blog_{topic_input.lower().replace(' ', '_')[:30]}.md",
                mime="text/markdown"
            )

    except Exception as e:
        st.error(f"Error generating blog: {e}")
