---
name: design-vibe-architecture
description: Turn vague app, web, SaaS, internal-tool, or AI product ideas—and existing vibe-coded repositories—into buildable architecture plans with explicit trade-offs, frontend/backend boundaries, APIs, database models, identity and authorization, LLM safety boundaries, production evolution plans, ADRs, and Mermaid diagrams. Use when Codex is asked to propose, explain, review, or revise a software architecture; select a proportionate stack; design data or auth; plan an AI feature; prepare an implementation blueprint; assess whether generated code fits the system; or produce architecture, ER, sequence, deployment, or data-flow diagrams for a small or medium product.
---

# Design Vibe Architecture

Turn a product idea into a decision-ready plan that another coding agent can implement and a human can audit. Optimize for understandable systems, reversible decisions, and observable production behavior.

## Operating stance

- Treat architecture as a set of trade-offs and evidence, not a list of fashionable technologies.
- Default to the smallest architecture that meets the stated risk and quality needs. Add services, queues, caches, vector stores, agents, or real-time infrastructure only when a concrete requirement justifies them.
- Separate known facts, user decisions, and working assumptions. Never invent user counts, compliance duties, budgets, or latency targets.
- Recommend one primary design. Mention alternatives only when a genuine unresolved decision changes the architecture.
- Describe responsibilities and trust boundaries before naming frameworks or vendors.
- Do not implement the product unless the user also asks for implementation.

## Required references

- Read [references/architecture-method.md](references/architecture-method.md) for every new architecture or architecture review.
- Read [references/output-contract.md](references/output-contract.md) before producing the final plan or diagrams.

## Workflow

### 1. Establish the evidence base

- If a repository exists, inspect its entry points, dependency manifests, schema and migrations, authentication, API routes, deployment configuration, tests, and observability before recommending changes.
- If only an idea exists, extract the target users, jobs, critical journey, data handled, external actors, irreversible mistakes, expected scale evidence, delivery constraints, and explicit non-goals.
- Ask at most five short questions only when their answers would materially change data sensitivity, tenancy, money movement, authorization, availability, or deployment. Otherwise proceed with clearly labeled assumptions.

### 2. Draw the product boundary

- Define who uses the system and the one to three journeys the first version must complete.
- State what remains outside the system and what is explicitly deferred.
- Turn vague qualities into measurable scenarios: stimulus, environment, expected response, and evidence.
- Identify trust boundaries, privileged actions, sensitive data, and deletion/retention expectations.

### 3. Choose a proportionate architecture

- Start with a modular monolith, one primary relational database, object storage for blobs, and managed infrastructure for most small and medium products.
- Separate the UI, application/API layer, domain modules, persistence, background work, and external integrations by responsibility even when they deploy together.
- Add asynchronous jobs when work is slow, retryable, scheduled, or should not block the user. Define idempotency, retry limits, status, compensation, and dead-letter handling.
- Add distributed services only for independently scaling bottlenecks, hard isolation, separate ownership, or deployment constraints supported by evidence.
- Record each consequential choice as an ADR: decision, context, considered options, consequences, evidence, and trigger for revisiting it.

### 4. Design the end-to-end system

Cover all applicable areas:

- Frontend state, validation, accessibility, error states, and the boundary between presentation and trusted business rules.
- Backend modules, API contracts, input validation, authorization checks, transactions, rate limits, and error semantics.
- Relational data model, keys, constraints, indexes, ownership, deletion behavior, migrations, backup, and restore testing.
- Authentication, session lifecycle, account recovery, role or attribute rules, object-level authorization, audit events, and administrative paths.
- External integrations, webhooks, timeouts, signatures, replay protection, retry strategy, and degraded operation.
- Build, environments, secrets, feature flags, migration order, canary or gradual rollout, observability, incident response, rollback, and cleanup.

### 5. Bound LLM and agent behavior

- Keep deterministic code responsible for identity, authorization, money, destructive changes, persistence rules, and final validation.
- Give models typed inputs and structured outputs. Validate outputs before use.
- Treat retrieved content, tool results, and user content as untrusted input.
- Use least-privilege tools, explicit approval for high-impact actions, full traces, versioned prompts/models, an offline evaluation set, online quality signals, and a non-AI fallback.
- Evaluate task outcome and execution trajectory. Include adversarial cases such as prompt injection, data exfiltration, excessive agency, and tool misuse.

### 6. Produce the architecture package

Follow the exact order and minimum content in `references/output-contract.md`. Always include:

1. A concise product and scope brief.
2. Assumptions, open questions, and measurable quality targets.
3. One recommended architecture with a responsibility table.
4. At least one Mermaid system architecture diagram.
5. A Mermaid ER diagram when the system stores relational data; otherwise explain why it is omitted.
6. A Mermaid sequence diagram for the riskiest or most important journey.
7. Data, API, identity, security, LLM, production, testing, migration, and maintenance decisions as applicable.
8. A phased implementation plan with acceptance evidence and rollback points.
9. ADRs, risks, revisit triggers, and a copy-ready task brief for the next coding agent.

Default to compact mode for a new small or two-person project: target roughly 1,200–2,500 words plus diagrams, use tables to remove repetition, and keep each section decision-oriented. Use an extended plan only when the user requests it or when existing-system, regulatory, financial, medical, multi-region, or high-availability risk genuinely requires the detail.

Keep Mermaid portable: use stable ASCII node IDs, quote labels containing spaces or punctuation, avoid custom themes, and do not invent infrastructure that is absent from the written design.

### 7. Validate before delivery

- Check every component in the diagrams appears in the written responsibility table.
- Check every persistent entity has ownership, a key, lifecycle, and deletion behavior.
- Check every privileged action has authentication, object-level authorization, auditability, and an explicit failure path.
- Check every rollout step has evidence, monitoring, and a reversal or mitigation path.
- If the plan is saved as Markdown, run:

```bash
python3 scripts/validate_architecture_plan.py path/to/architecture-plan.md
```

Resolve errors before delivery. Treat warnings as prompts for explicit explanation, not automatic blockers.

## Review mode

When reviewing an existing plan or repository, preserve its real constraints. Return findings in priority order, cite the relevant files or sections, distinguish correctness risks from optional improvements, and finish with the smallest safe next architecture change. Do not rewrite the whole system merely to match the default baseline.
