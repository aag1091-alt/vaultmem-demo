"""
VaultMem Demo — Operator-Blind Encrypted Memory for Personal AI Agents

Run locally:
    pip install -r requirements.txt
    streamlit run app.py

Deploy free:
    https://streamlit.io/cloud  (connect this repo, set main file = app.py)
"""

import hashlib
import json
import re
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

import numpy as np
import streamlit as st

# ── Demo embedder (no ML deps) ────────────────────────────────────────────────

class DemoEmbedder:
    """
    Hash-projection embedder — works without PyTorch or sentence-transformers.
    Keyword overlap drives similarity, which is enough for short, distinct memories.
    Swap in LocalEmbedder() from vaultmem[local] for full semantic search.
    """
    DIM = 384

    def embed(self, text: str) -> list[float]:
        tokens = re.findall(r"\b\w+\b", text.lower())
        vec = np.zeros(self.DIM)
        for token in tokens:
            for seed in range(4):
                digest = hashlib.sha256(f"{seed}:{token}".encode()).digest()
                idx = int.from_bytes(digest[:4], "big") % self.DIM
                sign = 1.0 if digest[4] & 1 else -1.0
                vec[idx] += sign
        norm = np.linalg.norm(vec)
        return (vec / norm).tolist() if norm > 0 else vec.tolist()


_EMBEDDER = DemoEmbedder()

# ── Sanitizer (loaded once — downloads dslim/bert-base-NER on first use) ──────

@st.cache_resource(show_spinner=False)
def get_sanitizer():
    """
    Returns a Sanitizer if presidio + transformers are installed, else None.
    The demo runs fine without it — sanitizer sections are hidden when unavailable.
    Install locally with: pip install 'vaultmem[presidio]'
    """
    try:
        import presidio_analyzer  # noqa: F401
        from vaultmem import Sanitizer
        return Sanitizer(backend="spacy")
    except Exception:
        return None

# ── Vault helpers ─────────────────────────────────────────────────────────────

VAULTS_DIR = Path("./vaults")
VAULTS_DIR.mkdir(exist_ok=True)


def vault_dir(name: str) -> Path:
    safe = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
    return VAULTS_DIR / safe


def vault_exists(name: str) -> bool:
    return (vault_dir(name) / "current.vmem").exists()


def encrypted_preview(name: str) -> str:
    d = vault_dir(name)
    lines = []
    for fname in ("current.vmem", "current.atoms"):
        f = d / fname
        if f.exists():
            raw = f.read_bytes()[:48]
            hex_str = " ".join(f"{b:02x}" for b in raw)
            lines.append(f"# {fname}  ({f.stat().st_size:,} bytes)\n{hex_str} ...")
    return "\n\n".join(lines) if lines else "No vault files yet."


def vault_file_sizes(name: str) -> list[tuple[str, int]]:
    d = vault_dir(name)
    return [(f.name, f.stat().st_size) for f in sorted(d.glob("*")) if f.is_file()]


# ── LLM call log (SQLite) ─────────────────────────────────────────────────────

def _log_db(vault_name: str) -> Path:
    return vault_dir(vault_name) / "llm_log.db"


def _init_log(vault_name: str) -> None:
    with sqlite3.connect(_log_db(vault_name)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS llm_calls (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at       REAL,
                query            TEXT,
                sanitized_context TEXT,
                restoration_map  TEXT,
                raw_reply        TEXT,
                final_reply      TEXT
            )
        """)


def save_llm_call(vault_name: str, query: str, sanitized_context: str | None,
                  restoration_map: dict, raw_reply: str, final_reply: str) -> None:
    _init_log(vault_name)
    with sqlite3.connect(_log_db(vault_name)) as conn:
        conn.execute(
            "INSERT INTO llm_calls "
            "(created_at, query, sanitized_context, restoration_map, raw_reply, final_reply) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                datetime.utcnow().timestamp(),
                query,
                sanitized_context,
                json.dumps(restoration_map),
                raw_reply,
                final_reply,
            ),
        )


def load_llm_calls(vault_name: str) -> list[dict]:
    db = _log_db(vault_name)
    if not db.exists():
        return []
    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM llm_calls ORDER BY created_at DESC LIMIT 3"
        ).fetchall()
    return [dict(r) for r in rows]


# ── LLM response ──────────────────────────────────────────────────────────────

def is_question(text: str) -> bool:
    t = text.strip()
    return t.endswith("?") or t.lower().startswith(("what", "who", "where", "when", "why", "how", "do ", "did ", "is ", "are ", "can ", "does "))


class GroqQueryNormalizer:
    """
    Uses the server-side Groq key to extract key search terms from the query
    before embedding — better than regex for complex or unusual phrasing.
    Falls back to the raw query on any error.
    """
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def normalize(self, text: str) -> str:
        try:
            from groq import Groq
            resp = Groq(api_key=self._api_key).chat.completions.create(
                model="llama-3.3-70b-versatile",
                max_tokens=20,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Extract the key search terms from this query. "
                            "Return only the keywords — no punctuation, no explanation."
                        ),
                    },
                    {"role": "user", "content": text},
                ],
            )
            result = resp.choices[0].message.content.strip()
            return result if result else text
        except Exception:
            return text




def respond(query: str, memories: list[dict], groq_key: str,
            sanitized_context: str | None = None) -> str:
    if not memories:
        if is_question(query):
            return "I don't have anything in memory about that yet. Tell me first and I'll remember it."
        return "Got it, I'll remember that."

    contents = [m["content"] for m in memories]

    if groq_key:
        try:
            from groq import Groq
            # Use sanitized context if available, otherwise raw memories
            mem_block = sanitized_context or "\n".join(f"- {c}" for c in contents)
            msg = Groq(api_key=groq_key).chat.completions.create(
                model="llama-3.3-70b-versatile",
                max_tokens=400,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful personal AI assistant. "
                            "Use only the retrieved memories below to answer directly and concisely. "
                            "Do not mention 'memories' or 'based on' — just answer naturally.\n\n"
                            f"Retrieved memories:\n{mem_block}"
                        ),
                    },
                    {"role": "user", "content": query},
                ],
            )
            return msg.choices[0].message.content
        except Exception as exc:
            return f"*(Groq error: {exc})*\n\nFrom memories: {contents[0]}"

    # Template fallback — no API key needed
    if is_question(query):
        return f"Based on what you've told me: **{contents[0]}**"
    bullets = "\n".join(f"• {c}" for c in contents[:3])
    return f"Noted! Related things I already know:\n\n{bullets}"

# ── Page setup ────────────────────────────────────────────────────────────────

st.set_page_config(page_title="VaultMem Demo", page_icon="🔐", layout="wide")

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("🔐 VaultMem")
    st.caption("Operator-blind encrypted memory · [GitHub](https://github.com/aag1091-alt/vaultmem-sdk)")

    st.divider()

    # ── Demo shortcut ─────────────────────────────────────────────────────────
    demo_btn = st.button("▶ Try Demo", type="primary", width="stretch",
                         help="Load a pre-seeded vault with 13 example memories across all 4 types")
    st.caption("[See demo conversations on GitHub](https://github.com/aag1091-alt/vaultmem-demo/blob/main/examples/demo_conversations.md)")

    st.divider()
    st.subheader("Or open your own vault")

    vault_name = st.text_input("Vault name", placeholder="e.g. my_vault")
    passphrase = st.text_input("Passphrase", type="password", placeholder="Secret passphrase")

    col_open, col_lock = st.columns(2)
    open_btn = col_open.button("Open", width="stretch")
    lock_btn = col_lock.button("Lock", width="stretch")

    st.divider()
    # Groq key — loaded from Streamlit secrets (server-side, never exposed to user)
    # For local dev, create .streamlit/secrets.toml with: GROQ_API_KEY = "gsk_..."
    api_key = st.secrets.get("GROQ_API_KEY", "")

    st.divider()
    st.markdown("""
**How it works**

1. Click **Try Demo** or open your own vault
2. Chat — statements are encrypted and stored
3. Ask questions — VaultMem retrieves relevant memories
4. The right panel shows what the **server sees**: pure ciphertext

`pip install vaultmem`
    """)

# ── Session state ─────────────────────────────────────────────────────────────

# sid is a short unique ID per browser tab — scopes the demo vault so every
# visitor gets their own isolated copy and cannot see or pollute others' data.
if "sid" not in st.session_state:
    st.session_state.sid = uuid.uuid4().hex[:8]

for key, default in [("unlocked", False), ("vault_name", None),
                     ("passphrase", None), ("messages", [])]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Demo vault seed + open ────────────────────────────────────────────────────

DEMO_PASSPHRASE = "demo"
DEMO_MEMORIES   = [
    # ── EPISODIC — time-anchored events ──────────────────────────────────────
    "I met Sarah Chen at the NeurIPS conference last December. She's a researcher at Stanford working on privacy-preserving ML. We exchanged contacts and plan to collaborate on a paper.",
    "Had my annual health checkup yesterday. Doctor said my blood pressure is 120/80 — perfectly normal. Cholesterol is slightly high at 210, she recommended cutting back on saturated fats.",
    "Just finished reading 'The Pragmatic Programmer' last night. The tip that hit hardest: 'Don't live with broken windows.' Small bad code decisions accumulate into unmaintainable systems.",
    "Spent a week in Tokyo last spring. Visited teamLab Planets in Toyosu — the infinite water room genuinely made me lose my sense of up and down. Had ramen at Fuunji in Shinjuku, best I've ever eaten.",
    "My first Kubernetes cluster in production went sideways the first night. Forgot to set resource limits — a runaway pod starved the whole node. Learned more in that one incident than in two months of tutorials.",
    "Attended a zero-knowledge proof workshop at ETH Zurich last autumn. Rafael walked us through how you can prove you know a secret without revealing it — felt like magic until the math clicked.",
    "My grandfather passed away last October. He taught me how to play chess and fix bicycles. I still have his toolkit. Miss him every time I open it.",
    "Adopted a grey tabby cat named Miso three months ago. She was terrified for the first week, hid behind the radiator. Now she sleeps on my keyboard every morning.",
    "Got my first commit merged into ripgrep — a one-line documentation fix, but Andrew Gallant replied personally. It felt completely disproportionate how good that made me feel.",
    "Ran my first 10K last Sunday. Finished in 58 minutes. Both knees ached on Monday but I'm signing up for the next one.",
    # ── SEMANTIC — timeless facts and knowledge ───────────────────────────────
    "The Ebbinghaus forgetting curve shows we forget roughly 70% of new information within 24 hours without review. Spaced repetition counteracts this by scheduling reviews at increasing intervals.",
    "Python's GIL prevents true multi-threading for CPU-bound tasks, but multiprocessing bypasses it by using separate interpreter processes. For I/O-bound tasks, asyncio is usually the better choice.",
    "AES-256-GCM provides both confidentiality and authenticity. The 128-bit authentication tag detects any tampering with the ciphertext — even flipping a single bit causes decryption to fail.",
    "CAP theorem: a distributed system can only guarantee two of consistency, availability, and partition tolerance simultaneously. Postgres favors CP; Cassandra favors AP. There is no free lunch.",
    "Transformer attention is O(n²) in sequence length. Flash Attention avoids materializing the full attention matrix by chunked computation, reducing memory footprint to O(n) while keeping the same output.",
    "The Unix philosophy: do one thing well, write programs that handle text streams, compose with pipes. The reason a one-liner like `grep | sort | uniq -c | sort -rn` is so powerful is this design philosophy.",
    "Adam optimizer adapts the learning rate per parameter using first and second moment estimates of the gradient. It usually converges faster than plain SGD but can generalise slightly worse on some problems.",
    "TCP three-way handshake: SYN → SYN-ACK → ACK. TIME_WAIT state exists to prevent stray packets from a closed connection being misdelivered to a new connection that reuses the same port.",
    # ── PERSONA — stable preferences and traits ───────────────────────────────
    "I prefer dark mode in all my editors and terminals. Light mode gives me headaches after more than an hour of coding.",
    "I drink exactly two cups of coffee every morning before I start coding. Espresso-based — flat white or cortado. Never instant.",
    "I've been vegetarian for five years. Not vegan — I still eat eggs and dairy. Pescatarian once in a while when travelling.",
    "I work best in 90-minute deep work blocks with a 15-minute break between them. Cal Newport's Deep Work is basically my operating manual.",
    "I use Neovim with a custom config — took two weeks to feel fluent, but modal editing is now so natural I can't go back. VSCode feels like wading through water.",
    "I'm mildly introverted. Conferences are energising in small doses but I need at least one full day alone afterwards to recover. I value the connections, not the crowd.",
    "I listen to lo-fi music or brown noise while coding. Anything with lyrics completely breaks my concentration — even a language I don't understand.",
    "I prefer written communication over calls. I always ask for an agenda before jumping on anything spontaneous. Async first.",
    "My resting heart rate is 52 bpm. I run three times a week and do 20 minutes of yoga after morning meditation. Sleep drops everything when I skip the yoga.",
    "My best ideas come in the shower or on long walks, never at my desk. I keep a paper notebook in the bathroom and a small Moleskine in my jacket pocket.",
    # ── PROCEDURAL — workflows and how-tos ───────────────────────────────────
    "My morning routine: alarm at 6:30am, 10 minutes of meditation, then coffee while reading emails. No Slack or meetings before 9am. That first 90-minute block is sacred.",
    "My code review checklist: tests written before the PR, no function longer than 40 lines, every public function has a docstring, and the PR description explains the 'why' not just the 'what'.",
    "For deploying to production: run the full test suite locally, create a PR, get one approval minimum, squash merge, then watch the deployment logs for 10 minutes before closing the laptop.",
    "How I take notes: I use the Zettelkasten method. Every idea gets a permanent note with a unique ID, written in my own words, linked to related notes. No raw quote-dumping — synthesis only.",
    "My debugging process: first reproduce with a minimal repro case. Then add logging to verify assumptions one at a time. Then binary-search the call stack. Never change two things simultaneously.",
    "Every Friday at 4pm I do a weekly review: close all tabs, review the task list, archive what's done, and pick the three most important tasks for next week. Takes 20 minutes, saves the whole week.",
    "When learning a new language or framework: first build something useless but fun (a small CLI toy). Then read the standard library source. Then find how the community idiomatically solves my usual problems.",
    "My on-call process: acknowledge the alert immediately, open a running notes doc even if I can't fix it fast. The doc prevents context loss if I get paged again before resolution.",
]


def ensure_demo_vault(demo_name: str) -> None:
    """Seed a fresh per-session demo vault."""
    import shutil
    from vaultmem import VaultSession
    vd = vault_dir(demo_name)
    if vd.exists():
        shutil.rmtree(vd)
    vd.mkdir(parents=True, exist_ok=True)
    with VaultSession.create(vd, DEMO_PASSPHRASE, demo_name, embedder=_EMBEDDER) as s:
        for memory in DEMO_MEMORIES:
            s.add(memory)
        s.flush()


if demo_btn:
    demo_name = f"demo_{st.session_state.sid}"
    with st.spinner("Loading demo vault…"):
        ensure_demo_vault(demo_name)
    st.session_state.unlocked = True
    st.session_state.vault_name = demo_name
    st.session_state.passphrase = DEMO_PASSPHRASE
    st.session_state.messages = [{
        "role": "assistant",
        "content": (
            "👋 Welcome to the demo vault! I have **36 memories** loaded across all 4 types:\n\n"
            "- 🕐 **EPISODIC** (10) — NeurIPS meeting, health checkup, Tokyo trip, first 10K run, cat Miso...\n"
            "- 📚 **SEMANTIC** (8) — Ebbinghaus curve, Python GIL, CAP theorem, Flash Attention, TCP...\n"
            "- 🧠 **PERSONA** (10) — dark mode, coffee, vegetarian, Neovim, introversion, ideas in the shower...\n"
            "- ⚙️ **PROCEDURAL** (8) — morning routine, code reviews, Zettelkasten notes, debugging, on-call...\n\n"
            "Each retrieved memory shows its **relevancy score** and **retrieval tier** (ATOM / COMPOSITE / AFFINITY).\n\n"
            "Try: *What do I know about Sarah Chen?* · *What's my coffee order?* · *How does Flash Attention work?*\n\n"
            "[See all 36 conversations on GitHub →](https://github.com/aag1091-alt/vaultmem-demo/blob/main/examples/demo_conversations.md)"
        ),
        "memories": [],
    }]

# ── Open / lock ───────────────────────────────────────────────────────────────

if open_btn:
    if not vault_name or not passphrase:
        st.sidebar.error("Enter a vault name and passphrase.")
    else:
        try:
            from vaultmem import VaultSession, WrongPassphraseError

            vd = vault_dir(vault_name)
            vd.mkdir(parents=True, exist_ok=True)

            with st.spinner("Deriving key with Argon2id (~52 ms — brute-force resistant)…"):
                if vault_exists(vault_name):
                    with VaultSession.open(vd, passphrase, embedder=_EMBEDDER):
                        pass
                    action = "opened"
                else:
                    with VaultSession.create(vd, passphrase, vault_name, embedder=_EMBEDDER):
                        pass
                    action = "created"

            st.session_state.unlocked = True
            st.session_state.vault_name = vault_name
            st.session_state.passphrase = passphrase
            st.session_state.messages = []
            st.sidebar.success(f"✅ Vault {action}")

        except Exception as exc:
            st.sidebar.error(f"❌ {exc}")

if lock_btn:
    st.session_state.update(unlocked=False, vault_name=None, passphrase=None, messages=[])
    st.sidebar.info("Vault locked.")

# ── Landing page ──────────────────────────────────────────────────────────────

if not st.session_state.unlocked:
    st.markdown("## Welcome to the VaultMem Demo")
    st.markdown("""
VaultMem is a Python SDK that gives personal AI agents **operator-blind encrypted memory**.
The platform developer integrates the library but **cryptographically cannot read user memories** —
not because of a privacy policy, but because of AES-256-GCM.

👈 **Enter a vault name and passphrase to get started.**

---

### How it compares
    """)

    st.dataframe({
        "": ["mem0 / Zep / Letta", "Self-hosted mem0", "VaultMem"],
        "Storage": ["Plaintext / platform key", "Plaintext in your DB", "AES-256-GCM, user key"],
        "Operator can read": ["✅ Yes", "✅ Yes (you = operator)", "❌ No"],
        "User holds key": ["❌ No", "❌ No", "✅ Yes"],
        "Embeddable library": ["✅ Yes", "✅ Yes", "✅ Yes"],
        "Portable format": ["❌ No", "❌ No", "✅ .vmem standard"],
    }, hide_index=True, width="stretch")

    st.markdown("""
---
**Try it:**
```bash
pip install vaultmem
```
```python
from vaultmem import VaultSession, NullEmbedder

with VaultSession.create("./vault", "my-passphrase", "alice", embedder=NullEmbedder()) as s:
    s.add("I prefer dark mode in all my editors.")
    s.add("I drink two coffees every morning before coding.")
    results = s.search("coffee habits", top_k=3)
    for r in results:
        print(r.atom.content)
```
    """)

# ── Main demo ─────────────────────────────────────────────────────────────────

else:
    name = st.session_state.vault_name
    phr  = st.session_state.passphrase

    col_chat, col_vault = st.columns([3, 2])

    # ── Chat ──────────────────────────────────────────────────────────────────
    with col_chat:
        st.subheader("💬 Chat")
        st.caption(f"Vault: **{name}** · every message is encrypted before being stored")

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("memories"):
                    with st.expander(
                        f"🔍 {len(msg['memories'])} memor{'y' if len(msg['memories']) == 1 else 'ies'} retrieved"
                    ):
                        for m in msg["memories"]:
                            score_pct = max(0, int(m["score"] * 100))
                            stored_on = datetime.fromtimestamp(m["created_at"]).strftime("%b %d, %Y") if m.get("created_at") else "?"
                            st.caption(
                                f"`{m.get('type', '')}` `{m['tier']}` **{score_pct}%** · stored {stored_on}"
                            )
                            st.caption(f"  {m['content']}")

                if msg.get("sanitized_context"):
                    rmap = msg.get("restoration_map", {})
                    with st.expander(f"🔏 Sent to Grok — {len(rmap)} entit{'y' if len(rmap) == 1 else 'ies'} redacted"):
                        st.caption("PII-stripped context — real values stayed on your device.")
                        st.code(msg["sanitized_context"], language=None)
                        if rmap:
                            st.caption("Replaced:")
                            cols = st.columns(2)
                            for i, (pseudo, real) in enumerate(rmap.items()):
                                cols[i % 2].caption(f"`{real}` → `{pseudo}`")

                if msg.get("raw_reply"):
                    with st.expander("🤖 Grok's raw response (before restoration)"):
                        st.caption("This is exactly what Grok returned — using pseudonyms, not your real data.")
                        st.markdown(msg["raw_reply"])

        if user_input := st.chat_input("Tell me something, or ask a question…"):
            st.session_state.messages.append({"role": "user", "content": user_input})

            memories = []
            try:
                from vaultmem import VaultSession, RegexQueryNormalizer
                vd = vault_dir(name)
                normalizer = GroqQueryNormalizer(api_key) if api_key else RegexQueryNormalizer()
                with VaultSession.open(vd, phr, embedder=_EMBEDDER,
                                       query_normalizer=normalizer) as s:
                    # Only store statements, not questions
                    if not is_question(user_input):
                        s.add(user_input)
                    results = s.search(user_input, top_k=4, normalize_query=True)
                    memories = [
                        {
                            "content": r.atom.content,
                            "score": r.score,
                            "tier": r.tier,
                            "type": r.atom.type.value,
                            "created_at": r.atom.created_at,
                        }
                        for r in results
                        if r.atom.content != user_input
                    ][:3]
            except Exception as exc:
                st.warning(f"Vault error: {exc}")

            # ── Sanitize context + query before sending to Grok ──────────
            sanitized_context = None
            sanitized_query = user_input
            restoration_map: dict[str, str] = {}
            if api_key and memories:
                sanitizer = get_sanitizer()
                if sanitizer:
                    # Sanitize context first — establishes the entity→pseudonym map
                    raw_context = "\n".join(f"- {m['content']}" for m in memories)
                    sanitized_context, restoration_map = sanitizer.sanitize(raw_context)
                    # Sanitize query using the same sanitizer instance so the same
                    # names map to the same pseudonyms ("Sarah Chen" → "Casey" in both)
                    sanitized_query, restoration_map = sanitizer.sanitize(user_input)

            raw_reply = respond(sanitized_query, memories, api_key or "",
                                sanitized_context=sanitized_context)

            # Restore real names/values in the response
            reply = raw_reply
            if restoration_map:
                sanitizer = get_sanitizer()
                if sanitizer:
                    reply = sanitizer.restore(raw_reply, restoration_map)

            # Persist to LLM call log
            if api_key and memories:
                try:
                    save_llm_call(
                        name, user_input,
                        sanitized_context, restoration_map,
                        raw_reply, reply,
                    )
                except Exception:
                    pass

            st.session_state.messages.append({
                "role": "assistant",
                "content": reply,
                "memories": memories,
                "sanitized_context": sanitized_context,
                "raw_reply": raw_reply if restoration_map else None,
                "restoration_map": restoration_map,
            })
            st.rerun()

    # ── Platform view ─────────────────────────────────────────────────────────
    with col_vault:
        st.subheader("🔒 Platform's view")
        st.caption("This is everything the server operator can see — ciphertext only.")

        st.code(encrypted_preview(name), language=None)

        sizes = vault_file_sizes(name)
        if sizes:
            for fname, size in sizes:
                st.caption(f"`{fname}` — {size:,} bytes, all encrypted")

        st.divider()
        st.markdown("**Without your passphrase:**")
        st.code(
            'VaultSession.open(vault, "wrong-passphrase")\n'
            "→ WrongPassphraseError",
            language="python",
        )

        st.divider()
        st.markdown("**Key architecture:**")
        st.code(
            "passphrase\n"
            "  → Argon2id (64 MiB, brute-force resistant)\n"
            "  → KEK  (in RAM only)\n"
            "  → unwrap MEK\n"
            "  → MEK  (in RAM during session only)\n"
            "  → AES-256-GCM → ciphertext on disk",
            language=None,
        )
        st.caption("MEK is zeroed from RAM on session close. The platform never sees it.")

        # ── LLM call log ──────────────────────────────────────────────────────
        st.divider()
        st.subheader("📋 LLM Context Log")
        st.caption("Every context block sent to the LLM — query, what was sanitized, and the raw response.")

        llm_calls = load_llm_calls(name)
        if not llm_calls:
            st.caption("No LLM calls yet. Ask a question to see the log.")
        else:
            for call in llm_calls:
                ts = datetime.fromtimestamp(call["created_at"]).strftime("%H:%M:%S")
                rmap = json.loads(call["restoration_map"] or "{}")
                redacted_note = f" · {len(rmap)} redacted" if rmap else ""
                with st.expander(f"[{ts}] {call['query'][:45]}…{redacted_note}"):
                    if call["sanitized_context"]:
                        st.caption("**Sent to LLM:**")
                        st.code(call["sanitized_context"], language=None)

                    if rmap:
                        st.caption("**Entities redacted:**")
                        for real, pseudo in rmap.items():
                            st.caption(f"  `{real}` → `{pseudo}`")

                    if call["raw_reply"] and call["raw_reply"] != call["final_reply"]:
                        st.caption("**Raw LLM response (with pseudonyms):**")
                        st.markdown(call["raw_reply"])

                    st.caption("**Final response (restored):**")
                    st.markdown(call["final_reply"])
