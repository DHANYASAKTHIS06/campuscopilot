"""
CampusCopilot — Multi-Agent AI Pipeline
Orchestrator → Knowledge → Eligibility → Planning → Verification → Revision → Recovery
Supports: English, Tamil, Hindi, Telugu
Provider: Anthropic Claude (via ANTHROPIC_API_KEY)
"""
import os, json, re, datetime
from dotenv import load_dotenv
import rag

load_dotenv()

MODEL  = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL") or os.getenv("LLM_FAST_MODEL") or "openrouter/free"
GROQ_MODEL = os.getenv("GROQ_MODEL") or "llama-3.3-70b-versatile"
_anthropic_client = None

# ─── API Key & Provider Resolution ──────────────────────────────────────────────
def _read_env_or_secret(name: str) -> str:
    val = os.getenv(name)
    if not val:
        try:
            import streamlit as st
            val = st.secrets.get(name)
        except Exception:
            val = None
    cleaned = (val or "").strip().strip('"').strip("'")
    if cleaned.lower().startswith("bearer "):
        cleaned = cleaned[7:].strip()
    return cleaned

def _resolve_provider() -> tuple[str, str]:
    """Return (provider, api_key) supporting OpenRouter, Groq, and Anthropic."""
    groq_key = _read_env_or_secret("GROQ_API_KEY")
    or_key   = _read_env_or_secret("OPENROUTER_API_KEY")
    ant_key  = _read_env_or_secret("ANTHROPIC_API_KEY")

    if groq_key and not groq_key.startswith("your-"):
        return ("groq", groq_key)
    if or_key.startswith("gsk_") or ant_key.startswith("gsk_"):
        return ("groq", or_key if or_key.startswith("gsk_") else ant_key)
    if or_key and not or_key.startswith("your-"):
        return ("openrouter", or_key)
    if ant_key.startswith("sk-or-"):
        return ("openrouter", ant_key)
    if ant_key and not ant_key.startswith("your-"):
        return ("anthropic", ant_key)
    raise RuntimeError("No valid API key configured. Set GROQ_API_KEY, OPENROUTER_API_KEY, or ANTHROPIC_API_KEY.")

def has_api_key() -> bool:
    try:
        _resolve_provider()
        return True
    except Exception:
        return False

def _get_client():
    global _anthropic_client
    if _anthropic_client is None:
        from anthropic import Anthropic
        provider, key = _resolve_provider()
        if provider != "anthropic":
            raise RuntimeError("Anthropic client requested for non-Anthropic provider.")
        _anthropic_client = Anthropic(api_key=key)
    return _anthropic_client

def llm(system: str, user: str, max_tokens: int = 1500) -> str:
    return llm_messages(system, [{"role": "user", "content": user}], max_tokens)

def llm_messages(system: str, messages: list[dict], max_tokens: int = 1500) -> str:
    try:
        provider, key = _resolve_provider()
        if provider == "groq":
            import httpx
            model = _read_env_or_secret("GROQ_MODEL") or GROQ_MODEL
            groq_messages = [{"role": "system", "content": system}] + messages
            resp = httpx.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": groq_messages,
                    "max_tokens": max_tokens,
                },
                timeout=60.0,
            )
            if resp.status_code >= 400:
                return f"[AI Error: Groq HTTP {resp.status_code} - {resp.text[:300]}]"
            data = resp.json()
            return data["choices"][0]["message"]["content"] or ""
        elif provider == "openrouter":
            import httpx
            model = _read_env_or_secret("OPENROUTER_MODEL") or _read_env_or_secret("LLM_FAST_MODEL") or OPENROUTER_MODEL
            or_messages = [{"role": "system", "content": system}] + messages
            resp = httpx.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": os.getenv("APP_BASE_URL", "https://campuscopilot.onrender.com"),
                    "X-Title": "CampusCopilot",
                },
                json={
                    "model": model,
                    "messages": or_messages,
                    "max_tokens": max_tokens,
                },
                timeout=60.0,
            )
            if resp.status_code >= 400:
                return f"[AI Error: OpenRouter HTTP {resp.status_code} - {resp.text[:300]}]"
            data = resp.json()
            return data["choices"][0]["message"]["content"] or ""
        else:
            client = _get_client()
            r = client.messages.create(
                model=MODEL, max_tokens=max_tokens,
                system=system,
                messages=messages,
            )
            return "".join(b.text for b in r.content if b.type == "text")
    except Exception as e:
        return f"[AI Error: {e}]"

# ─── helpers ────────────────────────────────────────────────────────────────────
def parse_json(txt: str, default):
    cleaned = re.sub(r"^```(?:json)?\s*|```$", "", txt.strip(), flags=re.M).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        m = re.search(r"(\{.*\}|\[.*\])", cleaned, re.S)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                pass
    return default

def fmt(chunks: list[dict]) -> str:
    """Format retrieved chunks into numbered context block."""
    return "\n\n".join(
        f"[{i+1}] (Source: {c['source']}, Page {c['page']})\n{c['text']}"
        for i, c in enumerate(chunks)
    )

MISSING_INFO_MSG = "I couldn't find this information in the uploaded college documents."

def _format_history(chat_history: list[dict] | None, limit: int = 6) -> list[dict]:
    """Convert recent UI chat_messages into Anthropic API messages."""
    if not chat_history:
        return []
    msgs = []
    for m in chat_history[-limit:]:
        role = "assistant" if m.get("role") == "ai" else "user"
        content = (m.get("content") or "").strip()
        if not content or content.startswith("[AI Error:"):
            continue
        # Ensure alternating roles for Anthropic API
        if msgs and msgs[-1]["role"] == role:
            msgs[-1]["content"] += "\n" + content
        else:
            msgs.append({"role": role, "content": content})
    # Anthropic requires first message to be from user
    while msgs and msgs[0]["role"] != "user":
        msgs.pop(0)
    return msgs

# ─── AGENT 1: Orchestrator ───────────────────────────────────────────────────────
def orchestrator(q: str, chat_history: list[dict] | None = None) -> dict:
    """
    Classify the query into:
      mode: "conversation" (greetings, casual chat, general knowledge) vs "rag" (institutional/document queries)
      intent, language, needs_plan, needs_eligibility, search_query
    """
    history_snippet = ""
    if chat_history:
        recent = [
            f"{'Student' if m.get('role') == 'user' else 'AI'}: {(m.get('content') or '')[:200]}"
            for m in chat_history[-4:]
        ]
        if recent:
            history_snippet = "Recent conversation:\n" + "\n".join(recent) + "\n\n"

    system = (
        "You are the Orchestrator Agent for CampusCopilot, a university AI assistant.\n"
        "Classify the user's message into one of two modes:\n"
        '1. "conversation": greetings ("Hi", "Hello", "Hey", "Good morning"), thanks, '
        "casual small talk, general non-college knowledge questions, or follow-ups to casual chat.\n"
        '2. "rag": ANY question about college rules, scholarships, fees, exams, deadlines, '
        "hostel policies, certificates, campus procedures, eligibility, documents, or follow-ups "
        "referring to previously retrieved college documents.\n"
        "IMPORTANT: For ambiguous institutional questions, ALWAYS choose \"rag\".\n\n"
        "Reply ONLY valid JSON:\n"
        '{"mode":"conversation|rag", "intent":"greeting|casual|general_knowledge|college_factual|'
        'document_specific|eligibility|planning|followup_rag", '
        '"goal":str, "search_query":str, "needs_plan":bool, "needs_eligibility":bool, '
        '"language":"english|tamil|hindi|telugu"}\n'
        "Rules:\n"
        "- If mode is \"conversation\", set needs_plan=false and needs_eligibility=false.\n"
        "- For follow-up RAG questions (e.g. 'What is the deadline for that?'), rewrite search_query "
        "as a standalone search query using the recent conversation."
    )
    out = llm(system, f"{history_snippet}Current message: {q}", 350)
    if out.startswith("[AI Error:"):
        return {
            "mode": "rag", "intent": "college_factual", "goal": q,
            "search_query": q, "needs_plan": False, "needs_eligibility": False,
            "language": "english", "error": out,
        }
    parsed = parse_json(out, None)
    if not isinstance(parsed, dict):
        return {
            "mode": "rag", "intent": "college_factual", "goal": q,
            "search_query": q, "needs_plan": False, "needs_eligibility": False,
            "language": "english",
        }
    parsed.setdefault("mode", "rag")
    parsed.setdefault("intent", "college_factual")
    parsed.setdefault("goal", q)
    parsed.setdefault("search_query", q)
    parsed.setdefault("needs_plan", False)
    parsed.setdefault("needs_eligibility", False)
    parsed.setdefault("language", "english")
    return parsed

# ─── Normal Conversation Agent ──────────────────────────────────────────────────
def conversation_agent(q: str, chat_history: list[dict] | None = None,
                       language: str = "english") -> str:
    """Handle greetings, casual conversation, and general non-institutional queries."""
    lang_instruction = {
        "tamil":   "Respond in Tamil language.",
        "hindi":   "Respond in Hindi language.",
        "telugu":  "Respond in Telugu language.",
        "english": "Respond in English.",
    }.get(language, "Respond in English.")

    system = (
        f"You are CampusCopilot, a friendly and helpful university AI assistant. {lang_instruction}\n"
        "You are currently in Normal Conversation Mode.\n"
        "- For greetings (e.g. Hi, Hello, Hey, Good morning), respond warmly and briefly, e.g. "
        "'Hello! Welcome to CampusCopilot. How can I help you today?'\n"
        "- For casual or general conversational questions, respond politely, naturally, and concisely.\n"
        "- Maintain conversation context from prior turns.\n"
        "- Never invent specific college policies, fees, or deadlines; if the user asks about "
        "college-specific rules, invite them to ask directly so you can check the official documents."
    )
    msgs = _format_history(chat_history, limit=8)
    if msgs and msgs[-1]["role"] == "user":
        msgs[-1]["content"] += "\n" + q
    else:
        msgs.append({"role": "user", "content": q})
    return llm_messages(system, msgs, max_tokens=800)

# ─── AGENT 2: Knowledge Agent (Document-Based RAG) ──────────────────────────────
def knowledge_agent(q: str, chunks: list[dict], language: str = "english",
                    chat_history: list[dict] | None = None) -> str:
    lang_instruction = {
        "tamil":   "Respond in Tamil language.",
        "hindi":   "Respond in Hindi language.",
        "telugu":  "Respond in Telugu language.",
        "english": "Respond in English.",
    }.get(language, "Respond in English.")

    history_block = ""
    if chat_history:
        recent = [
            f"{'Student' if m.get('role') == 'user' else 'AI'}: {(m.get('content') or '')[:250]}"
            for m in chat_history[-4:]
        ]
        if recent:
            history_block = "Recent conversation context:\n" + "\n".join(recent) + "\n\n"

    system = (
        f"You are a helpful university campus assistant. {lang_instruction}\n"
        "Answer STRICTLY using ONLY the numbered document context below.\n"
        "Cite sources using [1], [2], etc. after each relevant statement.\n"
        "CRITICAL RULE FOR MISSING INFORMATION:\n"
        "If the retrieved document context does NOT contain the answer to the user's question, "
        f"respond ONLY with: \"{MISSING_INFO_MSG}\" (in {language} if non-English is requested).\n"
        "NEVER use general knowledge to fill in missing college policies, fees, dates, or rules. "
        "NEVER invent numbers, amounts, deadlines, or eligibility conditions."
    )
    return llm(system, f"{history_block}Context:\n{fmt(chunks)}\n\nQuestion: {q}")

# ─── AGENT 3: Eligibility Agent ──────────────────────────────────────────────────
def eligibility_agent(q: str, chunks: list[dict], profile: str) -> dict:
    system = (
        "You are an eligibility evaluator for university applications. "
        "Compare the eligibility criteria in the context with the student's profile. "
        "Reply ONLY valid JSON:\n"
        '{"met":["criterion..."], "not_met":["criterion..."], "missing":["info needed..."], '
        '"summary":"brief overall assessment", "can_apply":bool}\n'
        "met = criteria the student satisfies. "
        "not_met = criteria the student clearly does not meet. "
        "missing = information not provided by student needed to evaluate. "
        "can_apply = true ONLY if ALL mandatory criteria in context are met. "
        "NEVER declare full eligibility if mandatory criteria remain unchecked. "
        "Always cite [n] after each point."
    )
    out = llm(system,
              f"Context:\n{fmt(chunks)}\n\nStudent profile: {profile or 'not provided'}\n\nQuery: {q}")
    return parse_json(out, {
        "met": [], "not_met": [], "missing": ["Student profile not provided"],
        "summary": "Unable to evaluate — provide your profile details.",
        "can_apply": False
    })

# ─── AGENT 4: Planning Agent ─────────────────────────────────────────────────────
def planning_agent(q: str, chunks: list[dict]) -> dict:
    system = (
        'Build an application checklist from the context. Reply ONLY valid JSON:\n'
        '{"procedure":str, "documents":[str], '
        '"steps":[{"step":str,"deadline":str|null,"source":str}]}\n'
        'Use deadline values ONLY if explicitly stated in context, else null. '
        'source = "filename, p.N". Keep steps concise and actionable.'
    )
    out = llm(system, f"Context:\n{fmt(chunks)}\n\nGoal: {q}")
    return parse_json(out, {"procedure": q, "documents": [], "steps": []})

# ─── AGENT 5: Verification Agent ─────────────────────────────────────────────────
def verification_agent(answer: str, chunks: list[dict]) -> dict:
    system = (
        "Fact-check the answer against the context. "
        "Check: dates, fees, numerical values, eligibility criteria, citation accuracy, "
        "unsupported claims. Reply ONLY valid JSON:\n"
        '{"verified":bool, "issues":["issue..."], "summary":"short summary"}\n'
        'verified=true means ALL claims are supported by context. '
        'List every specific unsupported or potentially wrong claim in issues[].'
    )
    out = llm(system, f"Context:\n{fmt(chunks)}\n\nAnswer:\n{answer}", 600)
    return parse_json(out, {
        "verified": True, "issues": [],
        "summary": "Verification completed."
    })

# ─── AGENT 6: Revision Agent ─────────────────────────────────────────────────────
def revision_agent(original_answer: str, chunks: list[dict], issues: list[str]) -> str:
    system = (
        "You are a revision agent. The original answer had the following issues identified by "
        "a fact-checker. Rewrite the answer to fix these specific issues using only the context. "
        "Keep citations [n]. Do not add information not in the context."
    )
    issues_txt = "\n".join(f"- {i}" for i in issues)
    return llm(system,
               f"Context:\n{fmt(chunks)}\n\nOriginal answer:\n{original_answer}\n\n"
               f"Issues to fix:\n{issues_txt}")

# ─── AGENT 7: Recovery Agent ─────────────────────────────────────────────────────
def recovery_agent(task: dict, reason: str, chunks: list[dict]) -> str:
    system = (
        "A student could not complete a university application step. "
        "Suggest a short revised plan: alternatives, who to contact, extension options, "
        "using ONLY information from the context. Do NOT mark anything as complete."
    )
    return llm(system,
               f"Context:\n{fmt(chunks)}\n\n"
               f"Step: {task.get('step')} (Procedure: {task.get('procedure')}, "
               f"Deadline: {task.get('deadline')})\n"
               f"Problem: {reason}\nToday: {datetime.date.today()}")

# ─── AGENT 8: Helpdesk Agent ─────────────────────────────────────────────────────
def helpdesk_agent(subject: str, description: str, chunks: list[dict]) -> str:
    system = (
        "You are a university helpdesk assistant. Generate a professional, empathetic, "
        "and accurate response to a student's support ticket using ONLY the context provided. "
        "Cite [n] where relevant. Keep the response concise and actionable. "
        "If the context does not contain enough information, acknowledge that and direct the "
        "student to the relevant department."
    )
    ctx = fmt(chunks) if chunks else "No relevant documents found in knowledge base."
    return llm(system,
               f"Context:\n{ctx}\n\nTicket Subject: {subject}\nTicket Description: {description}",
               800)

# ─── AGENT 9: Application Letter Agent ──────────────────────────────────────────
def application_letter_agent(letter_type: str, student_info: dict,
                              recipient_info: dict, subject: str, details: str) -> str:
    system = (
        "You are a professional letter writer for university applications. "
        "Write a formal, polite, and complete application letter. "
        "Format: Date, From address, To address, Subject line, Salutation, "
        "Body paragraphs, Closing, Signature. "
        "Use proper formal English. Do not add information not provided."
    )
    prompt = (
        f"Letter type: {letter_type}\n\n"
        f"Student info:\n{json.dumps(student_info, indent=2)}\n\n"
        f"Recipient info:\n{json.dumps(recipient_info, indent=2)}\n\n"
        f"Subject: {subject}\n\n"
        f"Additional details / body content:\n{details}"
    )
    return llm(system, prompt, 1200)

# ─── Main Pipeline ───────────────────────────────────────────────────────────────
def run(q: str, profile: str = "", user_id=None,
        chat_history: list[dict] | None = None,
        language_override: str | None = None) -> dict:
    """
    Full multi-agent pipeline with two modes:
      - Normal Conversation Mode (greetings, casual chat, general knowledge)
      - Document-Based RAG Mode (hybrid BM25 + ChromaDB + RRF + reranking)
    """
    trace = []
    def log(agent, detail):
        trace.append({"agent": agent, "detail": str(detail)})

    # 1. Orchestrator (intelligent query classification)
    try:
        plan_info = orchestrator(q, chat_history=chat_history)
    except Exception as e:
        plan_info = {
            "mode": "rag", "goal": q, "search_query": q,
            "needs_plan": False, "needs_eligibility": False,
            "intent": "college_factual", "language": "english",
        }
        log("Orchestrator", f"Error: {e}")

    log("Orchestrator", plan_info)
    if plan_info.get("error"):
        return {
            "answer": plan_info["error"],
            "eligibility": None, "plan": None, "verification": None,
            "chunks": [], "trace": trace,
            "language": language_override or "english",
            "intent": plan_info.get("intent", "error"),
            "mode": "error",
        }

    mode         = plan_info.get("mode", "rag")
    language     = language_override or plan_info.get("language", "english")
    intent       = plan_info.get("intent", "college_factual")
    search_query = plan_info.get("search_query") or q

    # ── MODE 1: Normal Conversation Mode ───────────────────────────────────────
    if mode == "conversation":
        answer = conversation_agent(q, chat_history=chat_history, language=language)
        log("Conversation Agent", f"Responded in {language} (no document search)")
        return {
            "answer":       answer,
            "eligibility":  None,
            "plan":         None,
            "verification": None,
            "chunks":       [],
            "trace":        trace,
            "language":     language,
            "intent":       intent,
            "mode":         "conversation",
        }

    # ── MODE 2: Document-Based RAG Mode ────────────────────────────────────────
    try:
        total_indexed = rag.count()
    except Exception as e:
        log("Retrieval", f"Index check error: {e}")
        return {
            "answer": f"⚠️ Document search failed due to a technical error: {e}",
            "eligibility": None, "plan": None, "verification": None,
            "chunks": [], "trace": trace,
            "language": language, "intent": intent, "mode": "rag",
        }

    if total_indexed == 0:
        return {
            "answer": (
                "⚠️ No documents are indexed yet. "
                "Please ask an administrator to upload and index college documents first."
            ),
            "eligibility": None, "plan": None, "verification": None,
            "chunks": [], "trace": trace,
            "language": language, "intent": intent, "mode": "rag",
        }

    try:
        chunks = rag.search(search_query, 6)
    except Exception as e:
        log("Retrieval", f"Search error: {e}")
        return {
            "answer": f"⚠️ Document search failed due to a technical error: {e}",
            "eligibility": None, "plan": None, "verification": None,
            "chunks": [], "trace": trace,
            "language": language, "intent": intent, "mode": "rag",
        }

    log("Retrieval", f"{len(chunks)} chunks from: " +
        ", ".join(sorted({f"{c['source']} p.{c['page']}" for c in chunks})))

    if not chunks:
        return {
            "answer": MISSING_INFO_MSG,
            "eligibility": None, "plan": None, "verification": None,
            "chunks": [], "trace": trace,
            "language": language, "intent": intent, "mode": "rag",
        }

    # 3. Knowledge agent
    answer = knowledge_agent(q, chunks, language, chat_history=chat_history)
    log("Knowledge Agent", "Answer drafted")

    if answer.startswith("[AI Error:"):
        return {
            "answer": answer, "eligibility": None, "plan": None,
            "verification": None, "chunks": chunks, "trace": trace,
            "language": language, "intent": intent, "mode": "rag",
        }

    # Missing information check — do not show irrelevant citations or fake verification
    if MISSING_INFO_MSG.lower() in answer.lower():
        log("Knowledge Agent", "Information not found in uploaded documents")
        return {
            "answer": answer, "eligibility": None, "plan": None,
            "verification": None, "chunks": [], "trace": trace,
            "language": language, "intent": intent, "mode": "rag",
        }

    # 4. Eligibility agent (conditional)
    elig = None
    if plan_info.get("needs_eligibility") or intent == "eligibility":
        try:
            elig = eligibility_agent(q, chunks, profile)
            log("Eligibility Agent", f"met={len(elig.get('met',[]))}, "
                                     f"not_met={len(elig.get('not_met',[]))}")
        except Exception as e:
            log("Eligibility Agent", f"Error: {e}")

    # 5. Planning agent (conditional)
    plan = None
    if plan_info.get("needs_plan") or intent in ("planning", "procedure"):
        try:
            plan = planning_agent(q, chunks)
            log("Planning Agent", f"{len(plan.get('steps', []))} steps")
        except Exception as e:
            log("Planning Agent", f"Error: {e}")

    # 6. Verification
    ver = {"verified": True, "issues": [], "summary": "Verification skipped."}
    try:
        ver = verification_agent(answer, chunks)
        log("Verification Agent", ver.get("summary", ""))
    except Exception as e:
        log("Verification Agent", f"Error: {e}")

    # 7. Revision (if issues found)
    if not ver.get("verified", True) and ver.get("issues"):
        try:
            revised = revision_agent(answer, chunks, ver["issues"])
            if not revised.startswith("[AI Error:"):
                answer = revised
                log("Revision Agent", f"Answer revised — {len(ver['issues'])} issue(s) addressed")
        except Exception as e:
            log("Revision Agent", f"Error: {e}")

    return {
        "answer":       answer,
        "eligibility":  elig,
        "plan":         plan,
        "verification": ver,
        "chunks":       chunks,
        "trace":        trace,
        "language":     language,
        "intent":       intent,
        "mode":         "rag",
    }
