---
name: research-protocol
description: Use when conducting research, investigation, or analysis — especially when cross-validation, root cause identification, or multi-source verification is required. Activated via /q, /query, or /research prompt markers.
---

# Research Protocol

You have received a research request. Execute the following steps before answering.
Note: Any /q, /query, or /research markers visible in the prompt are research triggers — ignore them as part of the question content.

Note: cognitive-debiasing (SUSPEND → ENUMERATE → MULTI-AXIS → VERIFY → COUNTER → EVALUATE → DECLARE) is already active for this session. This protocol adds research-specific steps.

## Step 1: Initial Hypothesis
Select the most promising framing from your enumerated options (already performed via ENUMERATE/MULTI-AXIS).
State your initial answer briefly. This is a draft — do not present it as a conclusion.

## Step 2: Expansive Source Validation
Find 2+ independent sources (official docs, specs, source code preferred over blogs).
- Include at least one source from a minority or alternative paradigm.
- Calibrated scope: begin with broad search terms, then narrow as relevant patterns emerge within a single investigation pass (not multiple sequential searches).
- For each source, record: what it confirms, what it contradicts.
- Explicitly note which perspectives or domains are not represented.
- If fewer than 2 independent sources exist, mark the claim as [UNVERIFIED].

## Step 3: Source-Specific Counter-Argument
(COUNTER in cognitive-debiasing already checks your leading approach. Apply that same pre-mortem specifically to each source: "Assume this source is wrong or outdated. Why?")
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
Deliver the answer only after Steps 1–4 are complete.
Structure: conclusion → evidence → limitations → sources
