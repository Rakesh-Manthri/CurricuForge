from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import re
from typing import List, Optional
import os
import io
import httpx
from agents import run_agentic_generation
from database import (
    init_db, save_curriculum, get_curriculum, list_curricula, close_pool,
    create_user, authenticate_user, create_session, get_user_by_token, delete_session
)
from pdf_generator import generate_curriculum_pdf

# Get the absolute path to the directory where app.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = FastAPI(title="CurricuForge API")

# Setup static files and templates
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATE_DIR)


# ── Disable browser cache for static files (dev) ─────────────────────
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class NoCacheStaticMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

app.add_middleware(NoCacheStaticMiddleware)


# ── Lifecycle events ─────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    await init_db()

@app.on_event("shutdown")
async def shutdown():
    await close_pool()


# ── Request model ────────────────────────────────────────────────────
class CurriculumRequest(BaseModel):
    skill: str
    level: str = "undergraduate"
    semesters: int = 4
    hours: int = 15
    goals: Optional[str] = ""
    style: Optional[str] = "balanced"
    industry: Optional[str] = ""
    selectedTopics: List[str] = []
    notes: Optional[str] = ""


# ── Page routes ──────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/generate", response_class=HTMLResponse)
async def generate_page(request: Request):
    return templates.TemplateResponse("generate.html", {"request": request})

@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})


# ── Contact form endpoint ────────────────────────────────────────────
class ContactRequest(BaseModel):
    name: str
    email: str
    subject: Optional[str] = ""
    message: str
    tags: List[str] = []

@app.post("/api/contact")
async def api_contact(data: ContactRequest):
    """Send the contact form message via SMTP to the configured email."""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from dotenv import load_dotenv

    load_dotenv()

    SMTP_EMAIL = os.getenv("SMTP_EMAIL", "").strip()
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
    CONTACT_TO_EMAIL = os.getenv("CONTACT_TO_EMAIL", "manthrirs06@gmail.com").strip()

    print(f"[EMAIL DEBUG] SMTP_EMAIL='{SMTP_EMAIL}', PASSWORD length={len(SMTP_PASSWORD)}, TO='{CONTACT_TO_EMAIL}'")

    if not SMTP_EMAIL or not SMTP_PASSWORD:
        raise HTTPException(status_code=500, detail="Email service is not configured. Please set SMTP_EMAIL and SMTP_PASSWORD in your .env file.")

    # Build email
    msg = MIMEMultipart()
    msg["From"] = SMTP_EMAIL
    msg["To"] = CONTACT_TO_EMAIL
    msg["Subject"] = f"CurricuForge Contact: {data.subject or 'General'}"

    tags_str = ", ".join(data.tags) if data.tags else "None"
    body = f"""New contact message from CurricuForge:

Name: {data.name}
Email: {data.email}
Subject: {data.subject or 'General'}
Tags: {tags_str}

Message:
{data.message}
"""
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)
        return {"status": "success", "message": "Email sent successfully."}
    except Exception as e:
        print(f"[EMAIL] Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")


@app.get("/analysis", response_class=HTMLResponse)
async def analysis_page(request: Request):
    return templates.TemplateResponse("analysis.html", {"request": request})

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.get("/signin", response_class=HTMLResponse)
async def signin_page(request: Request):
    return templates.TemplateResponse("signin.html", {"request": request})


# ── Auth API endpoints ─────────────────────────────────────────────────
class SignUpRequest(BaseModel):
    full_name: str
    email: str
    password: str

class SignInRequest(BaseModel):
    email: str
    password: str

@app.post("/api/auth/signup")
async def api_signup(data: SignUpRequest):
    if not data.full_name.strip() or not data.email.strip() or not data.password.strip():
        raise HTTPException(status_code=400, detail="All fields are required.")
    if len(data.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    user_id = await create_user(data.full_name.strip(), data.email.strip(), data.password)
    if not user_id:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    # Auto sign-in after signup
    token = await create_session(user_id)
    response = JSONResponse({
        "status": "success",
        "user": {"id": user_id, "full_name": data.full_name.strip(), "email": data.email.strip()}
    })
    response.set_cookie(
        key="cf_session", value=token, httponly=True,
        max_age=7*24*3600, samesite="lax"
    )
    return response

@app.post("/api/auth/signin")
async def api_signin(data: SignInRequest):
    user = await authenticate_user(data.email, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = await create_session(user['id'])
    response = JSONResponse({
        "status": "success",
        "user": user
    })
    response.set_cookie(
        key="cf_session", value=token, httponly=True,
        max_age=7*24*3600, samesite="lax"
    )
    return response

@app.post("/api/auth/signout")
async def api_signout(request: Request):
    token = request.cookies.get("cf_session")
    if token:
        await delete_session(token)
    response = JSONResponse({"status": "signed_out"})
    response.delete_cookie("cf_session")
    return response

@app.get("/api/auth/me")
async def api_current_user(request: Request):
    token = request.cookies.get("cf_session")
    if not token:
        return {"user": None}
    user = await get_user_by_token(token)
    return {"user": user}


# ── Chat endpoint for curriculum Q&A ─────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    curriculum_context: str
    chat_history: List[dict] = []
    curriculum_data: Optional[dict] = None  # actual curriculum JSON for modifications

@app.post("/api/chat")
async def chat_with_curriculum(data: ChatRequest):
    """Chat with the AI about the generated curriculum."""
    try:
        from langchain_ollama import ChatOllama
        from langchain_core.messages import HumanMessage, SystemMessage
        import json as json_mod
        import copy

        llm = ChatOllama(model="granite3.3:2b", temperature=0.4)

        # Detect if this is a modification request
        modify_keywords = ['add', 'remove', 'delete', 'replace', 'change', 'modify',
                          'swap', 'update', 'rename', 'move', 'simplify', 'include', 'insert']
        msg_lower = data.message.lower()
        is_modification = any(kw in msg_lower for kw in modify_keywords) and data.curriculum_data

        if is_modification:
            # ── MODIFICATION MODE: Use a focused prompt for the action ──
            action_prompt = f"""You are a curriculum editor. The user wants to modify this curriculum.

Current curriculum semesters:
{data.curriculum_context}

The user says: "{data.message}"

You must respond in EXACTLY this format (nothing else):
EXPLANATION: [1-2 sentence explanation of the change]
ACTION: [one of: add_course, remove_course, modify_course]
SEMESTER: [semester number to modify, e.g. 1, 2, 3]
COURSE_NAME: [name of the new or target course]
CREDITS: [credits, default 3]
DURATION: [weeks, default 15]
DESCRIPTION: [short course description]
TOPICS: [comma-separated list of topics]

Examples:
- If user says "add a machine learning course to semester 3":
EXPLANATION: Adding a Machine Learning course to Semester 3 to cover AI fundamentals.
ACTION: add_course
SEMESTER: 3
COURSE_NAME: Machine Learning Fundamentals
CREDITS: 3
DURATION: 15
DESCRIPTION: Introduction to machine learning algorithms and applications
TOPICS: Supervised Learning, Neural Networks, Model Evaluation, Feature Engineering

- If user says "remove the database course from semester 2":
EXPLANATION: Removing the database course from Semester 2 as requested.
ACTION: remove_course
SEMESTER: 2
COURSE_NAME: Database Systems

Respond now for the user's request. Only output the fields above, nothing else."""

            messages = [SystemMessage(content=action_prompt)]
            messages.append(HumanMessage(content=data.message))

            response = await llm.ainvoke(messages)
            raw_reply = response.content.strip()
            print(f"[CHAT-MODIFY] Raw model response:\n{raw_reply}")

            # Parse the structured response
            curriculum_update = None
            explanation = ""
            try:
                lines = {}
                for line in raw_reply.split('\n'):
                    line = line.strip()
                    if ':' in line:
                        key, _, val = line.partition(':')
                        lines[key.strip().upper().replace(' ', '_')] = val.strip()

                explanation = lines.get('EXPLANATION', 'Changes applied.')
                action = lines.get('ACTION', '').lower().strip().replace(' ', '_')
                
                # Parse semester number robustly
                sem_str = lines.get('SEMESTER', '1')
                # Extract just the number
                import re as re_mod
                sem_match = re_mod.search(r'(\d+)', sem_str)
                sem_num = int(sem_match.group(1)) if sem_match else 1
                
                course_name = lines.get('COURSE_NAME', 'New Course')

                print(f"[CHAT-MODIFY] Parsed: action={action}, semester={sem_num}, course={course_name}")
                print(f"[CHAT-MODIFY] All parsed lines: {lines}")

                if action and data.curriculum_data and 'semesters' in data.curriculum_data:
                    updated = copy.deepcopy(data.curriculum_data)
                    semesters = updated.get('semesters', [])

                    # Find the target semester (check 'number' field OR use index)
                    target_sem = None
                    target_sem_idx = None
                    for i, sem in enumerate(semesters):
                        if sem.get('number') == sem_num:
                            target_sem = sem
                            target_sem_idx = i
                            break

                    if not target_sem:
                        # Fallback: use index
                        idx = min(sem_num - 1, len(semesters) - 1)
                        idx = max(0, idx)
                        if semesters:
                            target_sem = semesters[idx]
                            target_sem_idx = idx

                    if target_sem:
                        if 'courses' not in target_sem:
                            target_sem['courses'] = []

                        # Log all courses for debugging
                        course_names_in_sem = [c.get('name', '') for c in target_sem['courses']]
                        print(f"[CHAT-MODIFY] Courses in semester {sem_num}: {course_names_in_sem}")

                        if action in ('add_course', 'add'):
                            new_course = {
                                "name": course_name,
                                "credits": int(lines.get('CREDITS', '3')),
                                "duration": int(lines.get('DURATION', '15')),
                                "description": lines.get('DESCRIPTION', ''),
                                "topics": [t.strip() for t in lines.get('TOPICS', '').split(',') if t.strip()]
                            }
                            target_sem['courses'].append(new_course)
                            curriculum_update = semesters
                            print(f"[CHAT-MODIFY] Added course '{course_name}' to semester {sem_num}")

                        elif action in ('remove_course', 'remove', 'delete_course', 'delete'):
                            original_count = len(target_sem['courses'])
                            search_name = course_name.lower().strip()
                            
                            # Try multiple matching strategies
                            matched = False
                            
                            # Strategy 1: Substring match (either direction)
                            remaining = [
                                c for c in target_sem['courses']
                                if not (search_name in c.get('name', '').lower() or 
                                       c.get('name', '').lower() in search_name)
                            ]
                            if len(remaining) < original_count:
                                target_sem['courses'] = remaining
                                matched = True
                            
                            # Strategy 2: Word overlap matching (if strategy 1 didn't work)
                            if not matched:
                                search_words = set(search_name.split())
                                best_match_idx = -1
                                best_overlap = 0
                                for ci, c in enumerate(target_sem['courses']):
                                    cname_words = set(c.get('name', '').lower().split())
                                    overlap = len(search_words & cname_words)
                                    if overlap > best_overlap:
                                        best_overlap = overlap
                                        best_match_idx = ci
                                
                                if best_match_idx >= 0 and best_overlap >= 1:
                                    removed_name = target_sem['courses'][best_match_idx].get('name', '')
                                    target_sem['courses'].pop(best_match_idx)
                                    matched = True
                                    print(f"[CHAT-MODIFY] Fuzzy matched and removed '{removed_name}'")
                            
                            # Strategy 3: Search ALL semesters if not found in target
                            if not matched:
                                for si, sem in enumerate(semesters):
                                    for ci, c in enumerate(sem.get('courses', [])):
                                        c_lower = c.get('name', '').lower()
                                        if search_name in c_lower or c_lower in search_name:
                                            removed_name = c.get('name', '')
                                            sem['courses'].pop(ci)
                                            matched = True
                                            print(f"[CHAT-MODIFY] Found and removed '{removed_name}' from semester {si+1}")
                                            break
                                    if matched:
                                        break
                            
                            if matched:
                                curriculum_update = semesters
                                print(f"[CHAT-MODIFY] Remove successful")
                            else:
                                explanation += f" (Note: Could not find a course matching '{course_name}' to remove.)"
                                print(f"[CHAT-MODIFY] Remove FAILED - no match for '{course_name}'")

                        elif action in ('modify_course', 'modify', 'update_course', 'update', 'change'):
                            search_name = course_name.lower().strip()
                            modified = False
                            for c in target_sem['courses']:
                                c_lower = c.get('name', '').lower()
                                if search_name in c_lower or c_lower in search_name:
                                    if lines.get('DESCRIPTION'):
                                        c['description'] = lines['DESCRIPTION']
                                    if lines.get('TOPICS'):
                                        c['topics'] = [t.strip() for t in lines['TOPICS'].split(',') if t.strip()]
                                    if lines.get('CREDITS'):
                                        c['credits'] = int(lines['CREDITS'])
                                    if lines.get('DURATION'):
                                        c['duration'] = int(lines['DURATION'])
                                    curriculum_update = semesters
                                    modified = True
                                    print(f"[CHAT-MODIFY] Modified course '{c.get('name')}'")
                                    break
                            if not modified:
                                explanation += f" (Note: Could not find '{course_name}' to modify.)"

                    print(f"[CHAT-MODIFY] Final result: success={curriculum_update is not None}")

            except Exception as parse_err:
                print(f"[CHAT-MODIFY] Parse error: {parse_err}")
                explanation = raw_reply

            # ── FALLBACK: If structured parsing didn't produce an update, try NLP-based extraction ──
            if curriculum_update is None and data.curriculum_data and 'semesters' in data.curriculum_data:
                print("[CHAT-MODIFY] Structured parse failed, trying fallback NLP extraction...")
                try:
                    import re as re_mod
                    updated = copy.deepcopy(data.curriculum_data)
                    semesters = updated.get('semesters', [])
                    user_msg = data.message.lower()

                    # Determine action from user's original message
                    fallback_action = None
                    if any(w in user_msg for w in ['add', 'include', 'insert', 'create']):
                        fallback_action = 'add'
                    elif any(w in user_msg for w in ['remove', 'delete', 'drop', 'eliminate']):
                        fallback_action = 'remove'
                    elif any(w in user_msg for w in ['change', 'modify', 'update', 'rename', 'replace']):
                        fallback_action = 'modify'

                    # Extract semester number from user message
                    sem_match = re_mod.search(r'semester\s*(\d+)', user_msg)
                    fallback_sem = int(sem_match.group(1)) if sem_match else None
                    if not fallback_sem:
                        sem_match = re_mod.search(r'sem\s*(\d+)', user_msg)
                        fallback_sem = int(sem_match.group(1)) if sem_match else None

                    # Extract course name from user message (text between quotes or after course keywords)
                    name_match = re_mod.search(r'["\']([^"\']+)["\']', data.message)
                    if not name_match:
                        # Try "add X to semester N" or "remove X from semester N"
                        name_match = re_mod.search(r'(?:add|include|insert)\s+(?:a\s+)?(?:course\s+(?:on|about|for|called|named)\s+)?(.+?)(?:\s+to\s+|\s+in\s+)', data.message, re_mod.IGNORECASE)
                    if not name_match:
                        name_match = re_mod.search(r'(?:remove|delete|drop)\s+(?:the\s+)?(?:course\s+)?(.+?)(?:\s+from\s+)', data.message, re_mod.IGNORECASE)
                    if not name_match:
                        # Try to get course name from model response
                        name_match = re_mod.search(r'["\']([^"\']+)["\']', raw_reply)

                    fallback_course = name_match.group(1).strip() if name_match else None

                    print(f"[CHAT-MODIFY FALLBACK] action={fallback_action}, semester={fallback_sem}, course={fallback_course}")

                    if fallback_action and fallback_course:
                        # Find target semester
                        target = None
                        if fallback_sem:
                            for sem in semesters:
                                if sem.get('number') == fallback_sem:
                                    target = sem
                                    break
                            if not target and fallback_sem <= len(semesters):
                                target = semesters[fallback_sem - 1]
                        if not target and semesters:
                            target = semesters[-1]  # default to last semester

                        if target and 'courses' not in target:
                            target['courses'] = []

                        if fallback_action == 'add' and target:
                            # Use model response for course details if available
                            desc = lines.get('DESCRIPTION', f'A course covering {fallback_course}')
                            topics_str = lines.get('TOPICS', fallback_course)
                            new_course = {
                                "name": fallback_course,
                                "credits": int(lines.get('CREDITS', '3')),
                                "duration": int(lines.get('DURATION', '15')),
                                "description": desc,
                                "topics": [t.strip() for t in topics_str.split(',') if t.strip()]
                            }
                            target['courses'].append(new_course)
                            curriculum_update = semesters
                            if not explanation or explanation == raw_reply:
                                explanation = f"Added '{fallback_course}' to Semester {fallback_sem or 'last'}."
                            print(f"[CHAT-MODIFY FALLBACK] Added '{fallback_course}'")

                        elif fallback_action == 'remove' and target:
                            search = fallback_course.lower()
                            orig_len = len(target['courses'])
                            # Try word overlap matching
                            search_words = set(search.split())
                            best_idx = -1
                            best_score = 0
                            for ci, c in enumerate(target.get('courses', [])):
                                cname = c.get('name', '').lower()
                                cword = set(cname.split())
                                score = len(search_words & cword)
                                if search in cname or cname in search:
                                    score = 100
                                if score > best_score:
                                    best_score = score
                                    best_idx = ci
                            
                            if best_idx >= 0 and best_score >= 1:
                                removed = target['courses'].pop(best_idx)
                                curriculum_update = semesters
                                explanation = f"Removed '{removed.get('name')}' from Semester {fallback_sem or '?'}."
                                print(f"[CHAT-MODIFY FALLBACK] Removed '{removed.get('name')}'")
                            else:
                                # Search all semesters
                                for si, sem in enumerate(semesters):
                                    for ci, c in enumerate(sem.get('courses', [])):
                                        cname = c.get('name', '').lower()
                                        if search in cname or cname in search or len(set(search.split()) & set(cname.split())) >= 1:
                                            removed = sem['courses'].pop(ci)
                                            curriculum_update = semesters
                                            explanation = f"Removed '{removed.get('name')}' from Semester {si+1}."
                                            print(f"[CHAT-MODIFY FALLBACK] Removed '{removed.get('name')}' from sem {si+1}")
                                            break
                                    if curriculum_update:
                                        break

                except Exception as fb_err:
                    print(f"[CHAT-MODIFY FALLBACK] Error: {fb_err}")

            result = {"reply": explanation}
            if curriculum_update:
                result["curriculum_update"] = curriculum_update
            else:
                result["reply"] = explanation + "\n\nI wasn't able to apply the change automatically. You can use the ✏️ Customize button to make manual edits."
            return result

        else:
            # ── NORMAL Q&A MODE ──
            system_prompt = f"""You are a helpful academic advisor for the CurricuForge platform.
You have full knowledge of the following curriculum:

{data.curriculum_context}

Answer questions clearly and helpfully. Be encouraging and specific.
Keep responses concise (2-4 paragraphs max).
If the user asks to modify the curriculum, suggest using the ✏️ Customize button or tell them to phrase it as: "Add [course] to Semester [N]" or "Remove [course] from Semester [N]"."""

            messages = [SystemMessage(content=system_prompt)]
            for msg in data.chat_history[-6:]:
                if msg.get('role') == 'user':
                    messages.append(HumanMessage(content=msg['content']))
                else:
                    from langchain_core.messages import AIMessage
                    messages.append(AIMessage(content=msg['content']))

            messages.append(HumanMessage(content=data.message))
            response = await llm.ainvoke(messages)

            return {"reply": response.content}

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

# ══════════════════════════════════════════════════════════════════════
#  PROMPT BUILDER
# ══════════════════════════════════════════════════════════════════════
def build_prompt(skill, level, semesters, hours, industry, goals, style, selected_topics, notes):
    # Start with core instructions
    prompt_parts = [
        f"You are an expert curriculum designer. Create a comprehensive {semesters}-semester curriculum for '{skill}' at a {level} level.",
        f"First, identify ALL individual courses needed to master '{skill}', then distribute them evenly across {semesters} semesters (3-4 courses per semester)."
    ]

    # Add parameters only if they have values
    parameters = []
    parameters.append(f"Weekly Commitment: {hours} hours")
    if industry:
        parameters.append(f"Industry Focus: {industry}")
    if goals:
        parameters.append(f"Learning Goals: {goals}")
    if style:
        parameters.append(f"Instructional Style: {style}")
    if selected_topics:
        parameters.append(f"Key Topics to Include: {', '.join(selected_topics)}")
    else:
        parameters.append("Key Topics to Include: General core topics")
    if notes:
        parameters.append(f"Additional Context: {notes}")

    if parameters:
        prompt_parts.append("\nParameters:")
        for param in parameters:
            prompt_parts.append(f"- {param}")

    # Strict formatting instructions
    prompt_parts.append("\nYour response MUST follow this EXACT structure for automated parsing. DO NOT include any conversational text or extra information outside these tags:")

    prompt_parts.append("\n<<OVERVIEW>>")
    prompt_parts.append("A professional, encouraging summary of the entire curriculum (max 3 sentences).")

    for i in range(1, semesters + 1):
        prompt_parts.append(f"\n<<SEMESTER {i}>>")
        prompt_parts.append(f"TITLE: (Descriptive theme for semester {i})")
        prompt_parts.append("")
        prompt_parts.append("COURSE: (Course name)")
        prompt_parts.append("CREDITS: (Number of credits)")
        prompt_parts.append("DURATION: (Number of weeks)")
        prompt_parts.append("TOPICS: (At least 5 specific topics, comma separated)")
        prompt_parts.append("DESCRIPTION: (2-3 sentences explaining what students learn)")
        prompt_parts.append("")
        prompt_parts.append("COURSE: (Next course name)")
        prompt_parts.append("CREDITS: (Number of credits)")
        prompt_parts.append("DURATION: (Number of weeks)")
        prompt_parts.append("TOPICS: (At least 5 specific topics, comma separated)")
        prompt_parts.append("DESCRIPTION: (2-3 sentences explaining what students learn)")
        prompt_parts.append("")
        prompt_parts.append("COURSE: (Third course name)")
        prompt_parts.append("CREDITS: (Number of credits)")
        prompt_parts.append("DURATION: (Number of weeks)")
        prompt_parts.append("TOPICS: (At least 5 specific topics, comma separated)")
        prompt_parts.append("DESCRIPTION: (2-3 sentences explaining what students learn)")

    prompt_parts.append("\nRules:")
    prompt_parts.append("- Each semester MUST have 3-4 courses")
    prompt_parts.append("- Each course MUST have at least 5 specific topics")
    prompt_parts.append("- Include credits and duration for every course")
    prompt_parts.append("- Maintain logical progression from foundational to advanced")
    prompt_parts.append("- Keep the tone educational, professional, and industry-aligned.")

    return "\n".join(prompt_parts)


# ══════════════════════════════════════════════════════════════════════
#  PARSER — Robust parser that handles multiple AI output formats
# ══════════════════════════════════════════════════════════════════════
def parse_curriculum_output(ai_output: str) -> dict:
    """
    Robust parser that handles various AI output formats:
    - <<OVERVIEW>> / <<SEMESTER N>> with COURSE: blocks
    - <<SEMESTER_N>> with COURSE: blocks
    - Fallback TOPICS/DETAILS format
    """
    parsed = {
        "summary": "Curriculum successfully generated.",
        "semesters": []
    }

    # Clean markdown artifacts
    cleaned = re.sub(r'\*\*', '', ai_output)
    cleaned = re.sub(r'#{1,3}\s*', '', cleaned)  # Remove markdown headers

    print(f"[PARSER] Raw output length: {len(ai_output)} chars")

    # ── Try to find OVERVIEW ─────────────────────────────────────
    # Try multiple overview formats
    for pattern in [
        r'<<\s*OVERVIEW\s*>>(.*?)(?=<<|$)',
        r'<<\s*PROGRAM_OVERVIEW\s*>>(.*?)(?=<<|$)',
        r'Overview[:\s]*(.*?)(?=<<|Semester|\n\n)',
    ]:
        overview_m = re.search(pattern, cleaned, re.DOTALL | re.IGNORECASE)
        if overview_m and overview_m.group(1).strip():
            parsed["summary"] = overview_m.group(1).strip()
            break

    # ── Try to find SEMESTERS ────────────────────────────────────
    # Pattern 1: <<SEMESTER N>> (with space)
    # Pattern 2: <<SEMESTER_N>> (with underscore)
    semester_pattern = r'<<\s*SEMESTER[\s_]+(\d+)\s*>>'
    semester_blocks = re.split(r'(?=' + semester_pattern + r')', cleaned, flags=re.IGNORECASE)

    semester_data = {}

    for block in semester_blocks:
        sem_match = re.search(semester_pattern, block, re.IGNORECASE)
        if not sem_match:
            continue

        num = int(sem_match.group(1))
        # Remove the semester tag
        content = re.sub(semester_pattern, '', block, count=1, flags=re.IGNORECASE).strip()
        # Remove closing tags
        content = re.sub(r'<<\s*/?\s*SEMESTER[\s_]*\d*\s*>>', '', content, flags=re.IGNORECASE).strip()

        # Extract title - try multiple patterns
        title = f"Semester {num}"
        for title_pat in [
            r'(?:SEMESTER_)?TITLE\s*:\s*(.*?)(?=\n)',
            r'^([A-Z][^\n]{5,60})(?=\n)',  # First line if it looks like a title
        ]:
            title_m = re.search(title_pat, content, re.IGNORECASE | re.MULTILINE)
            if title_m and title_m.group(1).strip():
                title = title_m.group(1).strip()
                break

        # ── Extract COURSE blocks ────────────────────────────────
        courses = []

        # Try Pattern 1: COURSE: blocks (our preferred format)
        course_splits = re.split(r'(?=(?:^|\n)\s*COURSE\s*:)', content, flags=re.IGNORECASE)

        for cb in course_splits:
            course_name_m = re.search(r'COURSE\s*:\s*(.*?)(?=\n|$)', cb, re.IGNORECASE)
            if not course_name_m:
                continue

            course_name = course_name_m.group(1).strip()
            if not course_name or len(course_name) < 3:
                continue

            # Credits
            credits_m = re.search(r'CREDITS?\s*:\s*(\d+)', cb, re.IGNORECASE)
            credits = int(credits_m.group(1)) if credits_m else 3

            # Duration
            duration_m = re.search(r'DURATION\s*:\s*(\d+)', cb, re.IGNORECASE)
            duration = int(duration_m.group(1)) if duration_m else 15

            # Topics
            topics = []
            topics_m = re.search(r'TOPICS?\s*:\s*(.*?)(?=\n\s*(?:DESCRIPTION|COURSE|OUTCOME|ASSESS|<<)|$)', cb, re.DOTALL | re.IGNORECASE)
            if topics_m:
                topics_raw = topics_m.group(1).strip()
                for t in re.split(r'[,;\n]', topics_raw):
                    cleaned_t = re.sub(r'^\s*[\d.\-•*]+\s*', '', t).strip()
                    if cleaned_t and len(cleaned_t) > 2 and len(cleaned_t) < 150:
                        topics.append(cleaned_t)

            # Description
            desc = ""
            desc_m = re.search(r'DESCRIPTION\s*:\s*(.*?)(?=\n\s*(?:COURSE|<<)|$)', cb, re.DOTALL | re.IGNORECASE)
            if desc_m:
                desc = desc_m.group(1).strip()

            courses.append({
                "name": course_name,
                "credits": credits,
                "duration": duration,
                "topics": topics,
                "description": desc
            })

        # Try Pattern 2: <<COURSE_N>> blocks
        if not courses:
            course_tag_splits = re.split(r'(?=<<\s*COURSE_\d+\s*>>)', content, flags=re.IGNORECASE)
            for cb in course_tag_splits:
                tag_m = re.search(r'<<\s*COURSE_\d+\s*>>', cb, re.IGNORECASE)
                if not tag_m:
                    continue
                cb_clean = re.sub(r'<<\s*/?COURSE_\d+\s*>>', '', cb, flags=re.IGNORECASE).strip()

                c_title_m = re.search(r'TITLE\s*:\s*(.*?)(?=\n)', cb_clean, re.IGNORECASE)
                c_credits_m = re.search(r'CREDITS?\s*:\s*(\d+)', cb_clean, re.IGNORECASE)
                c_duration_m = re.search(r'DURATION\s*:\s*(\d+)', cb_clean, re.IGNORECASE)

                topics = []
                topics_section = re.search(r'TOPICS?\s*:\s*(.*?)(?=\n\s*(?:OUTCOME|ASSESS|DESCRIPTION|<<)|$)', cb_clean, re.DOTALL | re.IGNORECASE)
                if topics_section:
                    for line in re.split(r'[,;\n]', topics_section.group(1)):
                        cleaned_t = re.sub(r'^\s*[\d.\-•*]+\s*', '', line).strip()
                        if cleaned_t and len(cleaned_t) > 2:
                            topics.append(cleaned_t)

                desc_m = re.search(r'(?:DESCRIPTION|OUTCOMES?)\s*:\s*(.*?)(?=\n\s*(?:ASSESS|<<|COURSE)|$)', cb_clean, re.DOTALL | re.IGNORECASE)

                courses.append({
                    "name": c_title_m.group(1).strip() if c_title_m else "Untitled Course",
                    "credits": int(c_credits_m.group(1)) if c_credits_m else 3,
                    "duration": int(c_duration_m.group(1)) if c_duration_m else 15,
                    "topics": topics,
                    "description": desc_m.group(1).strip() if desc_m else ""
                })

        # Fallback Pattern 3: Old TOPICS/DETAILS format (no courses)
        if not courses:
            topics_m = re.search(r'TOPICS?\s*:\s*(.*?)(?=\nDETAILS|\nDESCRIPTION|\n<<|$)', content, re.DOTALL | re.IGNORECASE)
            details_m = re.search(r'(?:DETAILS|DESCRIPTION)\s*:\s*([\s\S]*?)(?=\n<<|$)', content, re.IGNORECASE)
            topics_str = topics_m.group(1).strip() if topics_m else ""
            details = details_m.group(1).strip() if details_m else ""
            topics = [t.strip() for t in re.split(r'[,\n;]', topics_str) if t.strip() and len(t.strip()) > 2]
            courses.append({
                "name": title,
                "credits": 3,
                "duration": 15,
                "topics": topics,
                "description": details
            })

        semester_data[num] = {
            "number": num,
            "title": title,
            "courses": courses
        }

    # Sort and add semesters
    for i in sorted(semester_data.keys()):
        parsed["semesters"].append(semester_data[i])

    print(f"[PARSER] Found {len(parsed['semesters'])} semesters, summary length: {len(parsed['summary'])}")
    for sem in parsed["semesters"]:
        print(f"[PARSER]   Semester {sem['number']}: {sem['title']} — {len(sem['courses'])} courses")

    return parsed


# ── Generation endpoint ──────────────────────────────────────────────
@app.post("/generate")
async def generate_curriculum(data: CurriculumRequest, request: Request):
    """
    Agentic Curriculum generation endpoint.
    Uses a multi-agent LangGraph workflow (Planner -> Detailer -> Reviewer).
    Saves to SQLite.
    """
    try:
        input_payload = data.dict()

        # Build the prompt
        full_prompt = build_prompt(
            data.skill, data.level, data.semesters, data.hours,
            data.industry, data.goals, data.style, data.selectedTopics, data.notes
        )

        # Pass the prompt along with the input data
        input_payload['full_prompt'] = full_prompt

        # Execute the multi-agent graph
        result = await run_agentic_generation(input_payload)

        # Extract outputs
        ai_output = result['details']['raw_text']
        plan = result.get('plan', '')
        review_result = result.get('review_result', 'No review available')

        print(f"--- AGENT PLAN ---\n{plan}")
        print(f"--- AGENT REVIEW ---\n{review_result}")
        print(f"--- DETAILED OUTPUT (first 2000 chars) ---\n{ai_output[:2000]}")

        # Parse the structured text
        structured_curriculum = parse_curriculum_output(ai_output)

        # Save to SQLite (with user_id if logged in)
        db_id = None
        user_id = None
        token = request.cookies.get("cf_session")
        if token:
            user = await get_user_by_token(token)
            if user:
                user_id = user['id']
        try:
            db_id = await save_curriculum(input_payload, structured_curriculum, plan, review_result, ai_output, user_id=user_id)
        except Exception as db_err:
            print(f"[DB] Save failed (non-critical): {db_err}")

        return {
            "status": "success",
            "skill": data.skill,
            "level": data.level,
            "semesters": data.semesters,
            "curriculum": structured_curriculum,
            "agent_review": review_result,
            "db_id": db_id
        }
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Agent Workflow Error: {str(e)}")


# ── History page & endpoints ────────────────────────────────────────
@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request):
    return templates.TemplateResponse("history.html", {"request": request})

@app.get("/api/curricula")
async def api_list_curricula(request: Request):
    """Get recent generated curricula for the logged-in user."""
    user_id = None
    token = request.cookies.get("cf_session")
    if token:
        user = await get_user_by_token(token)
        if user:
            user_id = user['id']
    items = await list_curricula(limit=50, user_id=user_id)
    return {"curricula": items}

@app.get("/api/curricula/{curriculum_id}")
async def api_get_curriculum(curriculum_id: int):
    """Get a specific stored curriculum."""
    result = await get_curriculum(curriculum_id)
    if not result:
        raise HTTPException(status_code=404, detail="Curriculum not found")
    return result


# ── PDF Export endpoint ──────────────────────────────────────────────
class PDFExportRequest(BaseModel):
    curriculum: dict
    params: dict

@app.post("/export-pdf")
async def export_pdf(data: PDFExportRequest):
    """Generate and return a PDF of the curriculum."""
    try:
        pdf_bytes = generate_curriculum_pdf(data.curriculum, data.params)
        skill_name = data.params.get('skill', 'curriculum').replace(' ', '_')
        filename = f"CurricuForge_{skill_name}.pdf"

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"PDF generation error: {str(e)}")
