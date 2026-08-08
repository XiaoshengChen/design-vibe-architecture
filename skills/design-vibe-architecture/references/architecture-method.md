# Architecture method

Use this reference to reason from product risk to a proportionate system. It combines quality-attribute thinking, domain boundaries, data-intensive design, evolutionary architecture, production reliability, and current LLM engineering practices.

## Contents

1. Evidence hierarchy
2. Scope and quality attributes
3. Baseline architecture
4. Data design
5. Identity and authorization
6. API and asynchronous work
7. LLM and agent systems
8. Production evolution
9. Review checks
10. Decision triggers

## 1. Evidence hierarchy

Prefer evidence in this order:

1. Existing production behavior, incidents, measurements, and contractual obligations.
2. Explicit user decisions and product acceptance criteria.
3. Repository facts: code, schema, deployment configuration, tests, and logs.
4. Reasonable assumptions labeled with confidence and validation method.
5. Generic industry defaults.

Never let a generic default override known system evidence.

## 2. Scope and quality attributes

Capture:

- Primary users and actors.
- One to three critical journeys.
- System boundary and external dependencies.
- Explicit non-goals for the current release.
- Sensitive data and destructive or financial actions.
- Delivery, team, budget, region, and vendor constraints.

Rewrite vague qualities as scenarios:

| Vague claim | Useful scenario |
| --- | --- |
| Fast | At the expected peak, 95% of search requests return within 500 ms, measured at the API boundary. |
| Reliable | If the email provider is unavailable for 30 minutes, account creation succeeds and queued emails resume without duplicates. |
| Secure | A signed-in member cannot read or modify another workspace's objects; object-level authorization tests cover every route. |
| Scalable | The system supports the evidenced peak load with 50% headroom before a documented scaling trigger is reached. |
| Maintainable | A new optional field can be introduced and rolled back without downtime or an incompatible client release. |

Use numbers only when the user, system, or a clearly labeled assumption supplies them.

## 3. Baseline architecture

For most small and medium products, begin with:

- A web or native client responsible for presentation, local interaction state, accessibility, and untrusted input collection.
- One application/API deployment organized as a modular monolith with explicit domain modules.
- One relational database as the source of truth.
- Object storage for large binary assets.
- Managed identity, email, payments, search, or other commodity capabilities when their operational burden outweighs differentiation.
- A background worker or managed task queue only when work is slow, scheduled, retryable, or should survive request failure.
- Centralized logs, metrics, traces, error reporting, backups, and tested restore procedures.

Keep these boundaries even if they share a repository or deployment:

| Boundary | Responsibility | Must not own |
| --- | --- | --- |
| Client | UI, accessibility, optimistic state, input collection | Authorization truth, secrets, durable business invariants |
| API/application | Authentication integration, authorization, use cases, transactions | Browser-only display state |
| Domain modules | Business rules and owned entities | Cross-module table mutation without a contract |
| Database | Durable facts, constraints, transaction integrity | Presentation logic |
| Worker | Retryable or deferred side effects | Silent changes without idempotency and status |
| External provider | Commodity capability behind an adapter | Unbounded authority over core data |

Do not introduce microservices because of hypothetical scale or to imitate a large company. Introduce a service only when at least one is real:

- An independently measured scaling bottleneck.
- A hard isolation or regulatory boundary.
- A separate team with independent release ownership.
- A failure domain that must not share deployment or data access.
- A technology constraint that cannot be contained inside the existing deployment.

## 4. Data design

Start from durable facts and ownership, not pages or JSON responses.

For every entity define:

- Primary key and stable external identifier.
- Owning domain and tenant or user boundary.
- Required fields and database constraints.
- Relationships, cardinality, and deletion behavior.
- State transitions and audit requirements.
- Query paths and indexes justified by those paths.
- Retention, export, deletion, backup, and restore behavior.

Use a relational database by default when the product has accounts, permissions, transactions, reporting, or connected business facts. SQLite is a valid default for local-first, embedded, single-node, or low-write deployments when its operational model matches the product. Use a document, graph, time-series, search, or vector system as a secondary specialized index only when its access pattern requires it; identify the source of truth and rebuild path.

For production schema changes use expand-and-contract:

1. Add compatible structures.
2. Deploy code that tolerates old and new shapes.
3. Write new data in the new shape; dual-write only with a reconciliation plan.
4. Backfill in bounded, observable batches.
5. Verify counts, invariants, and sampled records.
6. Add stricter constraints only after verification.
7. Remove compatibility paths in a later release.

Avoid one-step destructive migrations, full-table locks without evidence, and irreversible transformations without a backup and tested recovery path.

## 5. Identity and authorization

Keep these separate:

- Authentication: who is the caller?
- Session: how does that identity persist and expire?
- Authorization: may this identity perform this action?
- Object authorization: may this identity act on this exact record?
- Audit: can the system explain who did what and when?

For every privileged route trace:

1. Credential or session validation.
2. Actor lookup and account state.
3. Target object lookup scoped to the tenant or owner.
4. Policy decision.
5. Transaction and side effects.
6. Safe response and audit event.

Design account recovery, invitation, email change, MFA reset, administrator impersonation, and service credentials as privileged workflows. Never rely on hiding UI controls as authorization.

## 6. API and asynchronous work

An API contract should define:

- Method and route or message name.
- Authenticated actor and authorization rule.
- Typed input, validation, and size limits.
- Success response and stable error semantics.
- Idempotency behavior.
- Transaction boundary.
- Rate limits and abuse controls.
- Observability fields and correlation identifiers.

For asynchronous work define:

- Producer and consumer.
- Durable job identity and idempotency key.
- At-least-once delivery behavior.
- Timeout, retry count, backoff, and terminal state.
- User-visible status.
- Compensation or reconciliation.
- Dead-letter inspection and replay procedure.

## 7. LLM and agent systems

Use a deterministic shell around the probabilistic capability:

- Deterministic code authenticates users, checks authorization, validates schemas, enforces limits, persists state, and approves destructive or financial changes.
- The model interprets ambiguous language, drafts content, ranks options, extracts structured data, or proposes actions.
- Tools expose narrow, typed capabilities with least privilege.
- High-impact actions pause for explicit human approval with a clear preview.

Version and record:

- Model and provider.
- System and task prompts.
- Tool schemas and policies.
- Retrieval configuration and corpus version.
- Structured-output schema.
- Evaluation dataset and grading logic.

Evaluate both result and trajectory:

- Did the task succeed?
- Were facts grounded and citations valid?
- Did the model choose appropriate tools?
- Did it stay within authorization and cost limits?
- Did it recover from tool and provider failure?
- Did injected content alter trusted instructions or leak data?

Provide timeouts, budgets, circuit breakers, a fallback or manual path, and graceful degradation when the model is unavailable.

## 8. Production evolution

The minimum delivery path is:

1. Reproducible build with pinned dependencies and generated artifacts.
2. Unit, contract, integration, migration, and critical-journey tests.
3. Preview or staging environment with production-like configuration.
4. Backward-compatible schema and API changes.
5. Feature flag or gradual rollout for risky behavior.
6. Dashboards and alerts tied to user-visible outcomes.
7. Rollback or roll-forward procedure verified before full release.
8. Post-release cleanup of flags, dual writes, compatibility code, and temporary resources.

For each change produce an impact map covering clients, APIs, modules, data, permissions, jobs, integrations, metrics, support, and recovery. Prefer small reversible increments over coordinated rewrites.

## 9. Review checks

Review generated code along these paths:

- Requirement to acceptance evidence.
- Input to validation to durable write.
- Identity to object-level authorization to audit.
- Error to user response, retry, alert, and recovery.
- Dependency to lockfile, maintenance status, license, and vulnerability posture.
- Migration to compatibility, backfill, verification, constraint, and rollback.
- LLM input to prompt boundary, tool authority, validation, trace, and evaluation.

Treat passing tests as evidence only when the tests cover the relevant invariant and can fail for the defect being considered.

## 10. Decision triggers

Record explicit triggers rather than speculative complexity:

| Current choice | Revisit when |
| --- | --- |
| Modular monolith | A measured bottleneck, isolation need, or independent team boundary cannot be handled inside it. |
| Single database | Workload isolation, region, compliance, or availability requirements exceed the current design. |
| No cache | A measured hot read remains too slow after query and index work. |
| Synchronous request | Work exceeds the response budget or must survive transient dependency failure. |
| Managed provider | Cost, lock-in, missing control, or reliability crosses an agreed threshold. |
| One LLM call | A measured task requires tools or iterative planning and the added trajectory risk is controlled. |

Every trigger must name the evidence to collect, the threshold or condition, and the migration direction.
