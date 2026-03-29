"""
Seed the demo vault with example memories covering all 4 memory types.

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


# ── Demo memories — one per conversation in demo_conversations.md ─────────────

MEMORIES = [
    # EPISODIC
    "I met Sarah Chen at the NeurIPS conference last December. She's a researcher at Stanford working on privacy-preserving ML. We exchanged contacts and plan to collaborate on a paper.",
    "Had my annual health checkup yesterday. Doctor said my blood pressure is 120/80 — perfectly normal. Cholesterol is slightly high at 210, she recommended cutting back on saturated fats.",
    "Just finished reading 'The Pragmatic Programmer' last night. The tip that hit hardest: 'Don't live with broken windows.' Small bad code decisions accumulate into unmaintainable systems.",

    # SEMANTIC
    "The Ebbinghaus forgetting curve shows we forget roughly 70% of new information within 24 hours without review. Spaced repetition counteracts this by scheduling reviews at increasing intervals.",
    "Python's GIL prevents true multi-threading for CPU-bound tasks, but multiprocessing bypasses it by using separate interpreter processes. For I/O-bound tasks, asyncio is usually the better choice.",
    "AES-256-GCM provides both confidentiality and authenticity. The 128-bit authentication tag detects any tampering with the ciphertext — even flipping a single bit causes decryption to fail.",

    # PERSONA
    "I prefer dark mode in all my editors and terminals. Light mode gives me headaches after more than an hour of coding.",
    "I drink exactly two cups of coffee every morning before I start coding. Espresso-based — flat white or cortado. Never instant.",
    "I've been vegetarian for five years. Not vegan — I still eat eggs and dairy. Pescatarian once in a while when travelling.",
    "I work best in 90-minute deep work blocks with a 15-minute break between them. Cal Newport's Deep Work is basically my operating manual.",

    # PROCEDURAL
    "My morning routine: alarm at 6:30am, 10 minutes of meditation, then coffee while reading emails. No Slack or meetings before 9am. That first 90-minute block is sacred.",
    "My code review checklist: tests written before the PR, no function longer than 40 lines, every public function has a docstring, and the PR description explains the 'why' not just the 'what'.",
    "For deploying to production: run the full test suite locally, create a PR, get one approval minimum, squash merge, then watch the deployment logs for 10 minutes before closing the laptop.",
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
