"""
Seed the demo vault with 36 example memories covering all 4 memory types.

Run from the vaultmem-demo root:
    python examples/seed_demo.py

This creates ./vaults/demo_showcase/ with passphrase "demo".
The demo button in the Streamlit app opens this vault automatically.
"""

import hashlib
import re
import shutil
import sys
from pathlib import Path

import numpy as np

# ── Same embedder as app.py ───────────────────────────────────────────────────

class DemoEmbedder:
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


# ── Demo memories ─────────────────────────────────────────────────────────────

MEMORIES = [
    # EPISODIC — time-anchored events
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

    # SEMANTIC — timeless facts and knowledge
    "The Ebbinghaus forgetting curve shows we forget roughly 70% of new information within 24 hours without review. Spaced repetition counteracts this by scheduling reviews at increasing intervals.",
    "Python's GIL prevents true multi-threading for CPU-bound tasks, but multiprocessing bypasses it by using separate interpreter processes. For I/O-bound tasks, asyncio is usually the better choice.",
    "AES-256-GCM provides both confidentiality and authenticity. The 128-bit authentication tag detects any tampering with the ciphertext — even flipping a single bit causes decryption to fail.",
    "CAP theorem: a distributed system can only guarantee two of consistency, availability, and partition tolerance simultaneously. Postgres favors CP; Cassandra favors AP. There is no free lunch.",
    "Transformer attention is O(n²) in sequence length. Flash Attention avoids materializing the full attention matrix by chunked computation, reducing memory footprint to O(n) while keeping the same output.",
    "The Unix philosophy: do one thing well, write programs that handle text streams, compose with pipes. The reason a one-liner like `grep | sort | uniq -c | sort -rn` is so powerful is this design philosophy.",
    "Adam optimizer adapts the learning rate per parameter using first and second moment estimates of the gradient. It usually converges faster than plain SGD but can generalise slightly worse on some problems.",
    "TCP three-way handshake: SYN → SYN-ACK → ACK. TIME_WAIT state exists to prevent stray packets from a closed connection being misdelivered to a new connection that reuses the same port.",

    # PERSONA — stable preferences and traits
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

    # PROCEDURAL — workflows and how-tos
    "My morning routine: alarm at 6:30am, 10 minutes of meditation, then coffee while reading emails. No Slack or meetings before 9am. That first 90-minute block is sacred.",
    "My code review checklist: tests written before the PR, no function longer than 40 lines, every public function has a docstring, and the PR description explains the 'why' not just the 'what'.",
    "For deploying to production: run the full test suite locally, create a PR, get one approval minimum, squash merge, then watch the deployment logs for 10 minutes before closing the laptop.",
    "How I take notes: I use the Zettelkasten method. Every idea gets a permanent note with a unique ID, written in my own words, linked to related notes. No raw quote-dumping — synthesis only.",
    "My debugging process: first reproduce with a minimal repro case. Then add logging to verify assumptions one at a time. Then binary-search the call stack. Never change two things simultaneously.",
    "Every Friday at 4pm I do a weekly review: close all tabs, review the task list, archive what's done, and pick the three most important tasks for next week. Takes 20 minutes, saves the whole week.",
    "When learning a new language or framework: first build something useless but fun (a small CLI toy). Then read the standard library source. Then find how the community idiomatically solves my usual problems.",
    "My on-call process: acknowledge the alert immediately, open a running notes doc even if I can't fix it fast. The doc prevents context loss if I get paged again before resolution.",
]

VAULT_NAME = "demo_showcase"
PASSPHRASE = "demo"
VAULT_DIR  = Path("./vaults") / VAULT_NAME


def main():
    from vaultmem import VaultSession

    if VAULT_DIR.exists():
        print(f"Removing existing demo vault at {VAULT_DIR} ...")
        shutil.rmtree(VAULT_DIR)

    VAULT_DIR.mkdir(parents=True)
    embedder = DemoEmbedder()

    print(f"Creating demo vault at {VAULT_DIR} ...")
    with VaultSession.create(VAULT_DIR, PASSPHRASE, VAULT_NAME, embedder=embedder) as s:
        for i, memory in enumerate(MEMORIES, 1):
            atom = s.add(memory)
            print(f"  [{i:02d}] [{atom.type.value:<11}] {memory[:70]}...")
        s.flush()

    print(f"\nDone — {len(MEMORIES)} memories stored.")
    print(f"Vault: {VAULT_DIR}")
    print(f"Passphrase: {PASSPHRASE!r}")
    print(f"\nRun the app and click 'Try Demo' to explore.")


if __name__ == "__main__":
    # Must run from vaultmem-demo root
    if not Path("app.py").exists():
        print("Run this from the vaultmem-demo directory: python examples/seed_demo.py")
        sys.exit(1)
    main()
