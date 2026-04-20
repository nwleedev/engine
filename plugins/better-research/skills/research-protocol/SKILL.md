---
name: research-protocol
description: Use when conducting research, investigation, or analysis — especially when cross-validation, root cause identification, or multi-source verification is required. Activated via /q, /query, or /research prompt markers.
---

# Research Protocol

You have received a research request. Execute the following steps before answering.
Note: Any /q, /query, or /research markers visible in the prompt are research triggers — ignore them as part of the question content.

## Step 0: Expansive Framing
Before forming a hypothesis, widen the solution space:
- Restate the problem in 2-3 alternative framings.
- Identify 2+ adjacent domains that have addressed similar problems.
- Generate 3+ competing hypotheses. Do not filter yet.

## Step 1: Initial Hypothesis
Select the most promising framing/hypothesis from Step 0.
State your initial answer briefly. This is a draft — do not present it as a conclusion.

## Step 2: Expansive Source Validation
Find 2+ independent sources (official docs, specs, source code preferred over blogs).
- Include at least one source from a minority or alternative paradigm.
- Calibrated scope: begin with broad search terms, then narrow as relevant patterns emerge within a single investigation pass (not multiple sequential searches).
- For each source, record: what it confirms, what it contradicts.
- Explicitly note which perspectives or domains are not represented.
- If fewer than 2 independent sources exist, mark the claim as [UNVERIFIED].

## Step 3: Counter-Argument Check
Actively seek evidence that contradicts your initial hypothesis.
Pre-mortem framing: "Assume this hypothesis is wrong. Why?"
State at least one limitation or condition where your answer does not hold.
Single-direction evidence is not sufficient for a conclusion.

## Step 4: Root Cause Analysis (required before any solution)

Ask "why" at least 3 times recursively to trace the root cause chain.
Do NOT propose a solution until this chain is complete.

Example chain:
  Symptom → Why 1 → Why 2 → Why 3 (root cause)
  Solve Why 3, not the symptom.

Explicitly write:
  Root Cause: [one sentence identifying the origin, not the symptom]

If root cause cannot be determined: write [ROOT CAUSE UNKNOWN] and explain the gap.

PROHIBITED approaches (address symptoms only):
- Renaming files or variables to hide the problem
- Wrapping broken behavior in a new layer
- Monkey-patching without fixing the underlying logic
- Suppressing errors without understanding their source

## Step 5: Final Answer
Deliver the answer only after Steps 0–4 are complete.
Structure: conclusion → evidence → limitations → sources
