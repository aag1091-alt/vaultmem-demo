"""
VaultMem Demo — Operator-Blind Encrypted Memory for Personal AI Agents

Run locally:
    pip install -r requirements.txt
    streamlit run app.py

Deploy free:
    https://streamlit.io/cloud  (connect this repo, set main file = app.py)
"""

import hashlib
import re
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

# ── LLM response ──────────────────────────────────────────────────────────────

def is_question(text: str) -> bool:
    t = text.strip()
    return t.endswith("?") or t.lower().startswith(("what", "who", "where", "when", "why", "how", "do ", "did ", "is ", "are ", "can ", "does "))


def respond(query: str, memories: list[str], groq_key: str) -> str:
    if not memories:
        if is_question(query):
            return "I don't have anything in memory about that yet. Tell me first and I'll remember it."
        return "Got it, I'll remember that."

    if groq_key:
        try:
            from groq import Groq
            mem_block = "\n".join(f"- {m}" for m in memories)
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
            return f"*(Groq error: {exc})*\n\nFrom memories: {memories[0]}"

    # Template fallback — no API key needed
    if is_question(query):
        return f"Based on what you've told me: **{memories[0]}**"
    bullets = "\n".join(f"• {m}" for m in memories[:3])
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

for key, default in [("unlocked", False), ("vault_name", None),
                     ("passphrase", None), ("messages", [])]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Demo vault seed + open ────────────────────────────────────────────────────

DEMO_NAME       = "demo_showcase"
DEMO_PASSPHRASE = "demo"
DEMO_MEMORIES   = [
    "I met Sarah Chen at the NeurIPS conference last December. She's a researcher at Stanford working on privacy-preserving ML. We exchanged contacts and plan to collaborate on a paper.",
    "Had my annual health checkup yesterday. Doctor said my blood pressure is 120/80 — perfectly normal. Cholesterol is slightly high at 210, she recommended cutting back on saturated fats.",
    "Just finished reading 'The Pragmatic Programmer' last night. The tip that hit hardest: 'Don't live with broken windows.' Small bad code decisions accumulate into unmaintainable systems.",
    "The Ebbinghaus forgetting curve shows we forget roughly 70% of new information within 24 hours without review. Spaced repetition counteracts this by scheduling reviews at increasing intervals.",
    "Python's GIL prevents true multi-threading for CPU-bound tasks, but multiprocessing bypasses it by using separate interpreter processes. For I/O-bound tasks, asyncio is usually the better choice.",
    "AES-256-GCM provides both confidentiality and authenticity. The 128-bit authentication tag detects any tampering with the ciphertext — even flipping a single bit causes decryption to fail.",
    "I prefer dark mode in all my editors and terminals. Light mode gives me headaches after more than an hour of coding.",
    "I drink exactly two cups of coffee every morning before I start coding. Espresso-based — flat white or cortado. Never instant.",
    "I've been vegetarian for five years. Not vegan — I still eat eggs and dairy. Pescatarian once in a while when travelling.",
    "I work best in 90-minute deep work blocks with a 15-minute break between them. Cal Newport's Deep Work is basically my operating manual.",
    "My morning routine: alarm at 6:30am, 10 minutes of meditation, then coffee while reading emails. No Slack or meetings before 9am. That first 90-minute block is sacred.",
    "My code review checklist: tests written before the PR, no function longer than 40 lines, every public function has a docstring, and the PR description explains the 'why' not just the 'what'.",
    "For deploying to production: run the full test suite locally, create a PR, get one approval minimum, squash merge, then watch the deployment logs for 10 minutes before closing the laptop.",
]


def ensure_demo_vault():
    """Seed demo vault if it doesn't exist yet."""
    from vaultmem import VaultSession
    vd = vault_dir(DEMO_NAME)
    if not vault_exists(DEMO_NAME):
        vd.mkdir(parents=True, exist_ok=True)
        with VaultSession.create(vd, DEMO_PASSPHRASE, DEMO_NAME, embedder=_EMBEDDER) as s:
            for memory in DEMO_MEMORIES:
                s.add(memory)
            s.flush()


if demo_btn:
    with st.spinner("Loading demo vault…"):
        ensure_demo_vault()
    st.session_state.unlocked = True
    st.session_state.vault_name = DEMO_NAME
    st.session_state.passphrase = DEMO_PASSPHRASE
    st.session_state.messages = [{
        "role": "assistant",
        "content": (
            "👋 Welcome to the demo vault! I have **13 memories** loaded across all 4 types:\n\n"
            "- 🕐 **EPISODIC** — Sarah Chen, health checkup, Pragmatic Programmer\n"
            "- 📚 **SEMANTIC** — Ebbinghaus curve, Python GIL, AES-256-GCM\n"
            "- 🧠 **PERSONA** — dark mode, coffee habits, vegetarian, deep work\n"
            "- ⚙️ **PROCEDURAL** — morning routine, code review, deployment process\n\n"
            "Try asking: *What do I know about Sarah Chen?* or *What's my coffee order?*\n\n"
            "[See all example conversations on GitHub →](https://github.com/aag1091-alt/vaultmem-demo/blob/main/examples/demo_conversations.md)"
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
                            st.caption(f"• {m}")

        if user_input := st.chat_input("Tell me something, or ask a question…"):
            st.session_state.messages.append({"role": "user", "content": user_input})

            memories = []
            try:
                from vaultmem import VaultSession
                vd = vault_dir(name)
                with VaultSession.open(vd, phr, embedder=_EMBEDDER) as s:
                    # Only store statements, not questions
                    if not is_question(user_input):
                        s.add(user_input)
                    results = s.search(user_input, top_k=4)
                    memories = [
                        r.atom.content for r in results
                        if r.atom.content != user_input
                    ][:3]
            except Exception as exc:
                st.warning(f"Vault error: {exc}")

            reply = respond(user_input, memories, api_key or "")
            st.session_state.messages.append(
                {"role": "assistant", "content": reply, "memories": memories}
            )
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
