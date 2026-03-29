# Demo Account — Sample Conversations

These are the plain-text conversations stored in the demo vault (passphrase: `demo`).
This is what the user told the agent. The right panel in the app shows what the
**platform operator sees** — encrypted bytes that reveal nothing without the passphrase.

---

## EPISODIC memories — time-anchored events

> Things that happened at a specific point in time.

**Conversation 1**
```
User: I met Sarah Chen at the NeurIPS conference last December.
      She's a researcher at Stanford working on privacy-preserving ML.
      We exchanged contacts and plan to collaborate on a paper.
```

**Conversation 2**
```
User: Had my annual health checkup yesterday. Doctor said my blood
      pressure is 120/80 — perfectly normal. Cholesterol is slightly
      high at 210, she recommended cutting back on saturated fats.
```

**Conversation 3**
```
User: Just finished reading "The Pragmatic Programmer" last night.
      The tip that hit hardest: "Don't live with broken windows."
      Small bad code decisions accumulate into unmaintainable systems.
```

---

## SEMANTIC memories — timeless facts and knowledge

> Things that are generally true, not tied to a specific event.

**Conversation 4**
```
User: The Ebbinghaus forgetting curve shows we forget roughly 70% of
      new information within 24 hours without review. Spaced repetition
      counteracts this by scheduling reviews at increasing intervals.
```

**Conversation 5**
```
User: Python's GIL prevents true multi-threading for CPU-bound tasks,
      but multiprocessing bypasses it by using separate interpreter
      processes. For I/O-bound tasks, asyncio is usually the better choice.
```

**Conversation 6**
```
User: AES-256-GCM provides both confidentiality and authenticity.
      The 128-bit authentication tag detects any tampering with the
      ciphertext — even flipping a single bit causes decryption to fail.
```

---

## PERSONA memories — stable preferences and traits

> Who you are, what you like, how you operate.

**Conversation 7**
```
User: I prefer dark mode in all my editors and terminals. Light mode
      gives me headaches after more than an hour of coding.
```

**Conversation 8**
```
User: I drink exactly two cups of coffee every morning before I start
      coding. Espresso-based — flat white or cortado. Never instant.
```

**Conversation 9**
```
User: I've been vegetarian for five years. Not vegan — I still eat eggs
      and dairy. Pescatarian once in a while when travelling.
```

**Conversation 10**
```
User: I work best in 90-minute deep work blocks with a 15-minute break
      between them. Cal Newport's Deep Work is basically my operating manual.
```

---

## PROCEDURAL memories — workflows and how-tos

> Step-by-step processes and rules you follow.

**Conversation 11**
```
User: My morning routine: alarm at 6:30am, 10 minutes of meditation,
      then coffee while reading emails. No Slack or meetings before 9am.
      That first 90-minute block is sacred.
```

**Conversation 12**
```
User: My code review checklist: tests written before the PR, no function
      longer than 40 lines, every public function has a docstring,
      and the PR description explains the "why" not just the "what".
```

**Conversation 13**
```
User: For deploying to production: run the full test suite locally,
      create a PR, get one approval minimum, squash merge, then watch
      the deployment logs for 10 minutes before closing the laptop.
```

---

## Suggested questions to ask the demo agent

```
What do I know about Sarah Chen?
What were my health checkup results?
What book did I finish recently and what was the key lesson?
How does the Ebbinghaus forgetting curve work?
What's my preference on editors?
What kind of coffee do I drink?
Am I vegetarian?
What is my morning routine?
How do I do code reviews?
What's my deployment process?
What do I know about AES-256-GCM?
What's the best approach for CPU-bound Python tasks?
```

---

## What this demonstrates

| Memory type | Example question | Retrieved memory |
|-------------|-----------------|-----------------|
| EPISODIC | "What were my health results?" | Blood pressure 120/80, cholesterol 210 |
| SEMANTIC | "How does spaced repetition work?" | Ebbinghaus forgetting curve explanation |
| PERSONA | "What coffee do I drink?" | Flat white or cortado, never instant |
| PROCEDURAL | "How do I deploy to production?" | Full test suite → PR → approval → squash merge → watch logs |
