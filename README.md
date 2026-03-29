# VaultMem Demo

Interactive Streamlit demo for [VaultMem](https://github.com/aag1091-alt/vaultmem-sdk) —
an embeddable Python SDK that gives personal AI agents **operator-blind encrypted memory**.

The platform developer integrates the library but **cryptographically cannot read user memories**.
Not a privacy policy — AES-256-GCM with a key that never leaves the user's session.

---

## Try it

**[→ Open live demo](https://vaultmem-demo.streamlit.app)**

Or run locally:
```bash
git clone https://github.com/aag1091-alt/vaultmem-demo
cd vaultmem-demo
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

---

## Demo account

Click **▶ Try Demo** in the sidebar to load a pre-seeded vault with **36 example memories**
covering all 4 memory types. No passphrase needed.

Each retrieved memory shows its **relevancy score**, **memory type**, and **retrieval tier**.

[See all 36 conversations in plain text →](examples/demo_conversations.md)

### Suggested questions to ask

| Question | Memory type |
|----------|-------------|
| What do I know about Sarah Chen? | EPISODIC |
| Tell me about the Tokyo trip | EPISODIC |
| What happened with my first Kubernetes deployment? | EPISODIC |
| Tell me about my cat | EPISODIC |
| How does Flash Attention work? | SEMANTIC |
| What is the CAP theorem? | SEMANTIC |
| How does the TCP handshake work? | SEMANTIC |
| What's the best approach for CPU-bound Python? | SEMANTIC |
| What editor do I use? | PERSONA |
| What coffee do I drink? | PERSONA |
| How do I prefer to communicate? | PERSONA |
| Where do I get my best ideas? | PERSONA |
| What is my morning routine? | PROCEDURAL |
| How do I debug problems? | PROCEDURAL |
| How do I take notes? | PROCEDURAL |
| How do I learn a new programming language? | PROCEDURAL |

---

## What the demo shows

- **Left panel** — chat with an AI agent that remembers what you tell it
- **Right panel** — raw encrypted bytes from `current.vmem` and `current.atoms` —
  what the server operator actually sees (nothing readable)
- **Argon2id spinner** — the ~52ms key derivation that makes brute-force expensive
- **Memory persistence** — lock and reopen your vault; memories survive across sessions

---

## How it works

```
Your passphrase
  → Argon2id (64 MiB, brute-force resistant)
  → KEK (in RAM only)
  → unwrap MEK
  → MEK (in RAM during session only)
  → AES-256-GCM → ciphertext on disk
```

The MEK is zeroed from RAM on session close.
The platform operator only ever holds ciphertext — mathematically unreadable without your passphrase.

---

## Install the SDK

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

[Full SDK documentation →](https://github.com/aag1091-alt/vaultmem-sdk)
[Paper (Zenodo) →](https://doi.org/10.5281/zenodo.19154079)
