# Demo Account — Sample Conversations

These are the 36 plain-text conversations stored in the demo vault (passphrase: `demo`).
This is what the user told the agent. The right panel in the app shows what the
**platform operator sees** — encrypted bytes that reveal nothing without the passphrase.

---

## EPISODIC — time-anchored events

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

**Conversation 4**
```
User: Spent a week in Tokyo last spring. Visited teamLab Planets in
      Toyosu — the infinite water room genuinely made me lose my sense
      of up and down. Had ramen at Fuunji in Shinjuku, best I've ever eaten.
```

**Conversation 5**
```
User: My first Kubernetes cluster in production went sideways the first
      night. Forgot to set resource limits — a runaway pod starved the
      whole node. Learned more in that one incident than in two months
      of tutorials.
```

**Conversation 6**
```
User: Attended a zero-knowledge proof workshop at ETH Zurich last autumn.
      Rafael walked us through how you can prove you know a secret without
      revealing it — felt like magic until the math clicked.
```

**Conversation 7**
```
User: My grandfather passed away last October. He taught me how to play
      chess and fix bicycles. I still have his toolkit. Miss him every
      time I open it.
```

**Conversation 8**
```
User: Adopted a grey tabby cat named Miso three months ago. She was
      terrified for the first week, hid behind the radiator. Now she
      sleeps on my keyboard every morning.
```

**Conversation 9**
```
User: Got my first commit merged into ripgrep — a one-line documentation
      fix, but Andrew Gallant replied personally. It felt completely
      disproportionate how good that made me feel.
```

**Conversation 10**
```
User: Ran my first 10K last Sunday. Finished in 58 minutes. Both knees
      ached on Monday but I'm signing up for the next one.
```

---

## SEMANTIC — timeless facts and knowledge

> Things that are generally true, not tied to a specific event.

**Conversation 11**
```
User: The Ebbinghaus forgetting curve shows we forget roughly 70% of
      new information within 24 hours without review. Spaced repetition
      counteracts this by scheduling reviews at increasing intervals.
```

**Conversation 12**
```
User: Python's GIL prevents true multi-threading for CPU-bound tasks,
      but multiprocessing bypasses it by using separate interpreter
      processes. For I/O-bound tasks, asyncio is usually the better choice.
```

**Conversation 13**
```
User: AES-256-GCM provides both confidentiality and authenticity.
      The 128-bit authentication tag detects any tampering with the
      ciphertext — even flipping a single bit causes decryption to fail.
```

**Conversation 14**
```
User: CAP theorem: a distributed system can only guarantee two of
      consistency, availability, and partition tolerance simultaneously.
      Postgres favors CP; Cassandra favors AP. There is no free lunch.
```

**Conversation 15**
```
User: Transformer attention is O(n²) in sequence length. Flash Attention
      avoids materializing the full attention matrix by chunked computation,
      reducing memory footprint to O(n) while keeping the same output.
```

**Conversation 16**
```
User: The Unix philosophy: do one thing well, write programs that handle
      text streams, compose with pipes. The reason a one-liner like
      `grep | sort | uniq -c | sort -rn` is so powerful is this design
      philosophy.
```

**Conversation 17**
```
User: Adam optimizer adapts the learning rate per parameter using first
      and second moment estimates of the gradient. It usually converges
      faster than plain SGD but can generalise slightly worse on some
      problems.
```

**Conversation 18**
```
User: TCP three-way handshake: SYN → SYN-ACK → ACK. TIME_WAIT state
      exists to prevent stray packets from a closed connection being
      misdelivered to a new connection that reuses the same port.
```

---

## PERSONA — stable preferences and traits

> Who you are, what you like, how you operate.

**Conversation 19**
```
User: I prefer dark mode in all my editors and terminals. Light mode
      gives me headaches after more than an hour of coding.
```

**Conversation 20**
```
User: I drink exactly two cups of coffee every morning before I start
      coding. Espresso-based — flat white or cortado. Never instant.
```

**Conversation 21**
```
User: I've been vegetarian for five years. Not vegan — I still eat eggs
      and dairy. Pescatarian once in a while when travelling.
```

**Conversation 22**
```
User: I work best in 90-minute deep work blocks with a 15-minute break
      between them. Cal Newport's Deep Work is basically my operating manual.
```

**Conversation 23**
```
User: I use Neovim with a custom config — took two weeks to feel fluent,
      but modal editing is now so natural I can't go back. VSCode feels
      like wading through water.
```

**Conversation 24**
```
User: I'm mildly introverted. Conferences are energising in small doses
      but I need at least one full day alone afterwards to recover. I value
      the connections, not the crowd.
```

**Conversation 25**
```
User: I listen to lo-fi music or brown noise while coding. Anything with
      lyrics completely breaks my concentration — even a language I don't
      understand.
```

**Conversation 26**
```
User: I prefer written communication over calls. I always ask for an
      agenda before jumping on anything spontaneous. Async first.
```

**Conversation 27**
```
User: My resting heart rate is 52 bpm. I run three times a week and do
      20 minutes of yoga after morning meditation. Sleep drops everything
      when I skip the yoga.
```

**Conversation 28**
```
User: My best ideas come in the shower or on long walks, never at my
      desk. I keep a paper notebook in the bathroom and a small Moleskine
      in my jacket pocket.
```

---

## PROCEDURAL — workflows and how-tos

> Step-by-step processes and rules you follow.

**Conversation 29**
```
User: My morning routine: alarm at 6:30am, 10 minutes of meditation,
      then coffee while reading emails. No Slack or meetings before 9am.
      That first 90-minute block is sacred.
```

**Conversation 30**
```
User: My code review checklist: tests written before the PR, no function
      longer than 40 lines, every public function has a docstring,
      and the PR description explains the "why" not just the "what".
```

**Conversation 31**
```
User: For deploying to production: run the full test suite locally,
      create a PR, get one approval minimum, squash merge, then watch
      the deployment logs for 10 minutes before closing the laptop.
```

**Conversation 32**
```
User: How I take notes: I use the Zettelkasten method. Every idea gets
      a permanent note with a unique ID, written in my own words, linked
      to related notes. No raw quote-dumping — synthesis only.
```

**Conversation 33**
```
User: My debugging process: first reproduce with a minimal repro case.
      Then add logging to verify assumptions one at a time. Then
      binary-search the call stack. Never change two things simultaneously.
```

**Conversation 34**
```
User: Every Friday at 4pm I do a weekly review: close all tabs, review
      the task list, archive what's done, and pick the three most important
      tasks for next week. Takes 20 minutes, saves the whole week.
```

**Conversation 35**
```
User: When learning a new language or framework: first build something
      useless but fun (a small CLI toy). Then read the standard library
      source. Then find how the community idiomatically solves my usual
      problems.
```

**Conversation 36**
```
User: My on-call process: acknowledge the alert immediately, open a
      running notes doc even if I can't fix it fast. The doc prevents
      context loss if I get paged again before resolution.
```

---

## Suggested questions to ask the demo agent

```
What do I know about Sarah Chen?
What were my health checkup results?
What book did I finish recently and what was the key lesson?
Tell me about the Tokyo trip.
What went wrong with my first Kubernetes deployment?
What is a zero-knowledge proof?
Tell me about my cat.
How does Flash Attention work?
What is the CAP theorem?
How does the TCP handshake work?
What's my preference on editors?
What kind of coffee do I drink?
Am I vegetarian?
What music do I listen to while coding?
What's my resting heart rate?
Where do I get my best ideas?
What is my morning routine?
How do I do code reviews?
What's my deployment process?
How do I debug problems?
How do I take notes?
How do I learn a new programming language?
What do I do on-call?
```

---

## What this demonstrates

| Memory type | Example question | Retrieved memory |
|-------------|-----------------|-----------------|
| EPISODIC | "Tell me about my cat" | Miso the tabby, keyboard sleeper |
| EPISODIC | "What happened with Kubernetes?" | Runaway pod incident, resource limits lesson |
| SEMANTIC | "How does Flash Attention work?" | O(n²) → O(n) chunked computation |
| SEMANTIC | "What is the CAP theorem?" | CP vs AP, Postgres vs Cassandra |
| PERSONA | "What editor do I use?" | Neovim, modal editing, custom config |
| PERSONA | "How do I prefer to communicate?" | Written over calls, async first, agenda required |
| PROCEDURAL | "How do I debug?" | Minimal repro → logging → binary search call stack |
| PROCEDURAL | "How do I learn new tech?" | CLI toy → stdlib source → community idioms |

Each result shows its **relevancy score** (cosine similarity %), **memory type**, and **retrieval tier**
(ATOM = direct match, COMPOSITE = aggregated, AFFINITY = recurring pattern with time decay).
