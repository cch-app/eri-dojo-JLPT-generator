---
name: verify-apis-with-context7
description: Verifies library/framework syntaxes and APIs are current (not deprecated) by consulting Context7 docs before implementing changes. Use when touching any external dependency APIs, adding new integrations, or resolving possible deprecation/version mismatches.
---

# Verify APIs with Context7 before implementing

## When to use

Use this skill whenever making changes that touch **external libraries, frameworks, SDKs, CLIs, or cloud services** (including “common” ones).

This applies to both:

- **Planning/design** (plan → build): verify APIs while drafting the approach, before proposing concrete code/config/commands.
- **Implementation** (build): verify APIs before writing or editing code that depends on them.

The goal is to avoid implementing or recommending deprecated or changed APIs.

## Required workflow

1. Identify the concrete thing to verify:
   - function/method name and signature
   - config keys
   - CLI flags/subcommands
   - required setup steps
2. Consult Context7 docs for the specific library/tool and version context available.
3. Confirm:
   - the API/syntax is current
   - any deprecations/migrations needed
   - the recommended modern alternative (if deprecated)
4. Only then implement the change using the verified syntax.

## Output expectations during implementation

- Cite the verified API shape in the explanation (briefly) before coding.
- If docs conflict with existing codebase usage, prefer the docs and update usage consistently, unless constrained by pinned versions.

## Guardrails

- Do not “guess” external APIs when uncertain—verify first.
- If Context7 can’t find relevant docs, fall back to web search or repository docs and clearly note the uncertainty.

