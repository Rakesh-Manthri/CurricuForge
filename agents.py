import os
import re
from typing import List, TypedDict, Optional, Annotated, Any
from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

# Single model — use the smaller, faster one
MODEL = "granite3.3:2b"


# ── State ────────────────────────────────────────────────────────────
class CurriculumState(TypedDict):
    input_data: dict
    plan: Optional[str]
    details: Optional[dict]
    review_result: Optional[str]
    status: str


# ── Agent A: Planner ─────────────────────────────────────────────────
async def planner_agent(state: CurriculumState):
    llm = ChatOllama(model=MODEL, temperature=0.3)
    data = state['input_data']

    topics_hint = ""
    if data.get('selectedTopics'):
        topics_hint = f"\nMust include these topics: {', '.join(data['selectedTopics'])}"

    prompt = f"""Plan a {data['semesters']}-semester curriculum for "{data['skill']}" at the {data['level']} level.
Weekly hours: {data['hours']}
Industry: {data.get('industry') or 'General'}
Goals: {data.get('goals') or 'Core competency'}{topics_hint}

List 3-4 courses per semester with a clear title for each semester.
Format:

SEMESTER 1: [Title]
- [Course Name]
- [Course Name]
- [Course Name]

SEMESTER 2: [Title]
- [Course Name]
...

Continue for all {data['semesters']} semesters. Keep courses specific and progressive."""

    response = await llm.ainvoke([
        SystemMessage(content="You are a curriculum planner. Output only the requested format."),
        HumanMessage(content=prompt)
    ])
    return {"plan": response.content, "status": "planning_complete"}


# ── Agent B: Detailer ────────────────────────────────────────────────
async def detailer_agent(state: CurriculumState):
    llm = ChatOllama(model=MODEL, temperature=0.5)
    data = state['input_data']
    plan = state['plan']

    # Use the full prompt from app.py if available
    full_prompt = data.get('full_prompt', '')

    if full_prompt:
        prompt = f"""Here is a course plan to follow:

{plan}

Now generate the full curriculum using this plan. Follow the EXACT output format below:

{full_prompt}"""
    else:
        prompt = f"""Generate a detailed curriculum based on this plan:
{plan}

Use <<OVERVIEW>> and <<SEMESTER N>> tags with COURSE:, CREDITS:, DURATION:, TOPICS:, DESCRIPTION: fields."""

    response = await llm.ainvoke([
        SystemMessage(content="You are a precise curriculum writer. Follow the output format EXACTLY. No extra text outside the tags."),
        HumanMessage(content=prompt)
    ])
    return {"details": {"raw_text": response.content}, "status": "detailing_complete"}


# ── Agent C: Reviewer ────────────────────────────────────────────────
async def reviewer_agent(state: CurriculumState):
    llm = ChatOllama(model=MODEL, temperature=0.1)
    raw_details = state['details']['raw_text']
    data = state['input_data']

    prompt = f"""Review this curriculum for "{data['skill']}":

{raw_details}

Check:
1. Does each semester have 3-4 courses?
2. Does each course have at least 5 topics?
3. Is the progression logical?

If it looks good, say "APPROVED". Otherwise list issues briefly."""

    response = await llm.ainvoke([
        SystemMessage(content="Curriculum reviewer. Be brief."),
        HumanMessage(content=prompt)
    ])
    return {"review_result": response.content, "status": "review_complete"}


# ── Graph Definition ─────────────────────────────────────────────────
def create_curriculum_graph():
    workflow = StateGraph(CurriculumState)

    workflow.add_node("planner", planner_agent)
    workflow.add_node("detailer", detailer_agent)
    workflow.add_node("reviewer", reviewer_agent)

    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "detailer")
    workflow.add_edge("detailer", "reviewer")
    workflow.add_edge("reviewer", END)

    return workflow.compile()


# ── External interface ───────────────────────────────────────────────
async def run_agentic_generation(data: dict):
    graph = create_curriculum_graph()
    initial_state = {
        "input_data": data,
        "plan": None,
        "details": None,
        "review_result": None,
        "status": "starting"
    }
    final_output = await graph.ainvoke(initial_state)
    return final_output
