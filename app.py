import os
import json
import streamlit as st
from openai import OpenAI

# ============================================================
# AI STUDY PACK GENERATOR
# OpenAI + Streamlit
#
# 5-stage workflow:
# Planning -> Content -> Assessment -> Review -> Refinement
#
# Streamlit Cloud Secret:
# OPENAI_API_KEY = "your-key"
# ============================================================

MODEL = "gpt-5.6-luna"

st.set_page_config(
    page_title="AI Study Pack Generator",
    page_icon="📚",
    layout="wide",
)


def get_api_key():
    """Read the OpenAI key from Streamlit Secrets or environment."""
    try:
        key = st.secrets.get("OPENAI_API_KEY")
        if key:
            return key
    except Exception:
        pass
    return os.getenv("OPENAI_API_KEY")


def get_client():
    key = get_api_key()
    return OpenAI(api_key=key) if key else None


def ask_ai(client, system_prompt, user_prompt, max_output_tokens=4000):
    """One safe OpenAI request used by every workflow stage."""
    try:
        response = client.responses.create(
            model=MODEL,
            instructions=system_prompt,
            input=user_prompt,
            max_output_tokens=max_output_tokens,
        )
        text = response.output_text
        if not text or not text.strip():
            return None, "OpenAI returned an empty response."
        return text.strip(), None
    except Exception as exc:
        return None, str(exc)


def run_stage(client, title, system_prompt, user_prompt, max_tokens):
    with st.status(title, expanded=True) as status:
        result, error = ask_ai(
            client,
            system_prompt,
            user_prompt,
            max_output_tokens=max_tokens,
        )
        if error:
            status.update(label=f"{title} failed", state="error")
            return None, error
        status.update(label=f"{title} completed", state="complete")
        return result, None


def planning_stage(client, profile):
    system = """
You are the Planning Agent for a personalized AI study-pack system.
Create a concise learning plan. Return ONLY valid JSON with:
learning_goal, difficulty_strategy, key_concepts,
study_sequence, estimated_minutes, content_requirements,
assessment_requirements.
Match the student's level, available time and goal.
"""
    user = f"""
Student profile:
{json.dumps(profile, indent=2)}
Create the personalized learning plan.
"""
    raw, error = run_stage(client, "1/5 Planning", system, user, 2500)
    if error:
        return None, error

    try:
        return json.loads(raw), None
    except json.JSONDecodeError:
        return {
            "learning_goal": profile["goal"],
            "difficulty_strategy": profile["level"],
            "key_concepts": [profile["topic"]],
            "study_sequence": [profile["topic"]],
            "estimated_minutes": 60,
            "content_requirements": ["Simple explanations", "Examples", "Revision"],
            "assessment_requirements": ["Practice questions", "MCQs"],
        }, None


def content_stage(client, profile, plan):
    system = """
You are the Content Generation Agent.
Create accurate, simple, exam-friendly Markdown study material.
Use the student profile and planning context.
Include:
# Study Pack
## Learning Goal
## Quick Introduction
## Important Concepts
## Key Definitions
## Detailed Notes
## Examples
## Common Mistakes
## Quick Revision
## Exam Tips
Do not mention internal agents or workflow.
"""
    user = f"""
Student profile:
{json.dumps(profile, indent=2)}

Planning context:
{json.dumps(plan, indent=2)}

Generate the study material.
"""
    return run_stage(client, "2/5 Content Generation", system, user, 5000)


def assessment_stage(client, profile, plan, content):
    system = """
You are the Assessment Agent.
Create an assessment based on the supplied study content.
Return Markdown containing:
## Practice Questions
5 questions from easy to challenging.

## Multiple Choice Quiz
5 MCQs with four options each.

## Answer Key
Correct answers with short explanations.
"""
    user = f"""
Student profile:
{json.dumps(profile, indent=2)}

Plan:
{json.dumps(plan, indent=2)}

Study content:
{content}

Create the assessment.
"""
    return run_stage(client, "3/5 Assessment", system, user, 3500)


def review_stage(client, profile, plan, content, assessment):
    system = """
You are the Review and Quality-Control Agent.
Check the content and assessment for:
accuracy, topic coverage, difficulty, personalization,
missing concepts, weak/duplicate questions, clarity,
grammar and formatting.

Return Markdown:
## Review Score
Score 1-10.

## Strengths
## Problems Found
## Required Changes

Do not rewrite the whole pack.
"""
    user = f"""
Student profile:
{json.dumps(profile, indent=2)}

Plan:
{json.dumps(plan, indent=2)}

Content:
{content}

Assessment:
{assessment}

Perform the quality review.
"""
    return run_stage(client, "4/5 Review", system, user, 3000)


def refinement_stage(client, profile, plan, content, assessment, review):
    system = """
You are the Refinement Agent.
Create the final polished study pack using ALL supplied context.
Apply the reviewer's required changes.
Use simple English and make it useful for exam preparation.

Return Markdown with:
# 📚 Final AI Study Pack
## Learning Goal
## Quick Introduction
## Important Concepts
## Key Definitions
## Detailed Notes
## Examples
## Common Mistakes
## Quick Revision
## Practice Questions
## Multiple Choice Quiz
## Answer Key
## Exam Tips
## Flashcards

Do not mention agents, prompts, API keys or internal workflow.
"""
    user = f"""
Student profile:
{json.dumps(profile, indent=2)}

Plan:
{json.dumps(plan, indent=2)}

Original content:
{content}

Assessment:
{assessment}

Quality review:
{review}

Create the final refined study pack.
"""
    return run_stage(client, "5/5 Refinement", system, user, 6000)


# ------------------------- UI -------------------------

st.title("📚 AI Study Pack Generator")
st.write(
    "A 5-stage AI workflow that plans, generates, assesses, reviews "
    "and refines a personalized study pack."
)

with st.sidebar:
    st.header("🎯 Student Profile")

    subject = st.text_input(
        "Subject",
        placeholder="Example: Data Structures",
    )
    topic = st.text_input(
        "Topic",
        placeholder="Example: Binary Search",
    )
    level = st.selectbox(
        "Student Level",
        ["Beginner", "Intermediate", "Advanced"],
    )
    study_time = st.selectbox(
        "Available Study Time",
        ["15 minutes", "30 minutes", "1 hour", "2 hours", "3+ hours"],
    )
    goal = st.selectbox(
        "Learning Goal",
        [
            "Exam preparation",
            "Understand the topic",
            "Quick revision",
            "Practice and test myself",
        ],
    )
    pack_type = st.selectbox(
        "Study Pack Type",
        [
            "Complete Study Pack",
            "Notes + Quiz",
            "Flashcards + Quiz",
            "Exam Revision Pack",
        ],
    )

    generate = st.button(
        "🚀 Generate Study Pack",
        type="primary",
        use_container_width=True,
    )

st.info(
    "🔄 Workflow: Student Profile → Planning → Content → "
    "Assessment → Review → Refinement → Final Pack"
)

if generate:
    if not subject.strip() or not topic.strip():
        st.error("Please enter both Subject and Topic.")
        st.stop()

    client = get_client()
    if client is None:
        st.error(
            "OPENAI_API_KEY is missing. Add it in "
            "Streamlit → Manage app → Settings → Secrets."
        )
        st.stop()

    profile = {
        "subject": subject.strip(),
        "topic": topic.strip(),
        "level": level,
        "study_time": study_time,
        "goal": goal,
        "pack_type": pack_type,
    }

    plan, error = planning_stage(client, profile)
    if error:
        st.error(f"Planning error: {error}")
        st.stop()

    content, error = content_stage(client, profile, plan)
    if error:
        st.error(f"Content generation error: {error}")
        st.stop()

    assessment, error = assessment_stage(
        client, profile, plan, content
    )
    if error:
        st.error(f"Assessment error: {error}")
        st.stop()

    review, error = review_stage(
        client, profile, plan, content, assessment
    )
    if error:
        st.error(f"Review error: {error}")
        st.stop()

    final_pack, error = refinement_stage(
        client, profile, plan, content, assessment, review
    )
    if error:
        st.error(f"Refinement error: {error}")
        st.stop()

    st.success("🎉 Your personalized study pack is ready!")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["🧠 Planning", "📝 Content", "❓ Assessment", "🔍 Review", "📚 Final Pack"]
    )

    with tab1:
        st.json(plan)

    with tab2:
        st.markdown(content)

    with tab3:
        st.markdown(assessment)

    with tab4:
        st.markdown(review)

    with tab5:
        st.markdown(final_pack)
        st.download_button(
            "⬇️ Download Study Pack",
            data=final_pack,
            file_name="ai_study_pack.md",
            mime="text/markdown",
        )
