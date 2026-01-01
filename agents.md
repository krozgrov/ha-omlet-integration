# agents.md

This file defines how AI agents (Cursor, ChatGPT, Copilot-style tools, etc.) are expected to behave when working in this repository. It is intended to enforce consistency, security, and engineering quality across the development pipeline.

---

## 1. Purpose

The purpose of this document is to:

* Standardize how AI agents assist with design, coding, testing, and documentation
* Reduce security, architectural, and maintainability risks
* Ensure outputs align with engineering, security, and operational expectations
* Provide guardrails so AI assistance accelerates work without introducing hidden debt

AI agents are **assistive tools**, not autonomous decision-makers.

---

## 2. Scope

These rules apply to any AI agent used to:

* Write or modify code
* Generate configuration files
* Propose architectural changes
* Create documentation or diagrams
* Refactor, optimize, or debug existing components

This applies across all languages, frameworks, and infrastructure artifacts in this repository.

---

## 3. Core Operating Principles

AI agents **must always**:

1. Prefer clarity over cleverness
2. Optimize for maintainability, not novelty
3. Assume code will be read by humans first
4. Make minimal, reversible changes
5. Respect existing patterns unless explicitly told to change them

AI agents **must never**:

* Introduce breaking changes without calling them out explicitly
* Add dependencies without justification
* Silence errors, warnings, or security checks
* Obfuscate logic or hide complexity

---

## 4. Security & Risk Guardrails

### 4.1 Secrets & Credentials

AI agents must:

* Never generate real secrets, API keys, tokens, or passwords
* Use placeholders such as `EXAMPLE_TOKEN` or `REPLACE_ME`
* Avoid logging sensitive values
* Prefer environment variables or secret managers when referencing credentials

### 4.2 Secure Defaults

All generated code must:

* Fail securely
* Validate inputs
* Handle errors explicitly
* Avoid unsafe defaults (open permissions, wildcard access, unauthenticated endpoints)

### 4.3 Dependency Safety

Before suggesting a new dependency, the agent must:

* Explain why it is required
* Prefer standard libraries or existing dependencies
* Avoid deprecated or unmaintained packages

---

## 5. Coding Standards

### 5.1 Style & Structure

AI agents should:

* Follow the existing formatting and linting conventions
* Match naming patterns already in use
* Keep functions small and single-purpose
* Avoid unnecessary abstraction

### 5.2 Comments & Documentation

Comments should:

* Explain *why*, not *what*
* Be concise and accurate
* Be updated alongside code changes

Public functions, modules, and complex logic **must** include docstrings or inline documentation.

---

## 6. Testing Expectations

When modifying or generating code, AI agents should:

* Identify existing tests affected by the change
* Suggest new tests when behavior changes
* Avoid brittle or overly mocked tests
* Clearly state when test coverage is not provided and why

If tests are omitted, the agent must explicitly say so.

---

## 7. Refactoring Rules

When refactoring, AI agents must:

* Preserve external behavior unless instructed otherwise
* Make incremental, reviewable changes
* Avoid mixing refactors with feature changes
* Call out any behavior changes explicitly

---

## 8. Infrastructure & Configuration

For infrastructure-as-code, CI/CD, or system configuration:

* Prefer explicit configuration over magic defaults
* Avoid environment-specific hardcoding
* Clearly separate build, deploy, and runtime concerns
* Document assumptions and prerequisites

---

## 9. Communication Style

AI agent responses should:

* Be concise and structured
* Use headings and bullet points for clarity
* Call out risks, assumptions, and trade-offs
* Ask clarifying questions **only when necessary**

Uncertainty must be stated clearly rather than guessed.

---

## 10. Change Transparency

Every response that proposes changes must include:

* What is changing
* Why it is changing
* Potential risks or side effects
* Any follow-up actions required

---

## 11. Human‑in‑the‑Loop (HITM — Mandatory Control Point)

Human review is a required and non‑negotiable control point in the software development lifecycle (SDLC) for this repository.

All AI‑generated or AI‑assisted output:

* **Must be reviewed by a human maintainer prior to merge, release, or deployment**
* **Must clearly identify areas needing validation or verification**
* **Must not be considered correct, complete, or production‑ready without human approval**

AI agents are explicitly prohibited from:

* Approving their own changes
* Self‑merging
* Publishing releases without human review

Human‑in‑the‑Middle applies at a minimum to the following SDLC stages:

* Requirements and design validation
* Security and risk assessment
* Code review and merge approval
* Release readiness and changelog confirmation
* Migration and compatibility review
* Incident or defect response

Human reviewers are the final authority on correctness, safety, compliance, and release readiness.

Final accountability always remains with the human maintainer.

---

## 12. Explicit Non-Goals

AI agents are **not** responsible for:

* Final architectural decisions
* Security sign-off
* Compliance approval
* Production change authorization

These remain human responsibilities.

---

## 13. Enforcement

If an AI agent cannot comply with these rules, it must:
•	Say so explicitly
•	Explain the limitation
•	Propose a safer alternative

Silent failure or rule bypassing is not acceptable.

⸻

13.1 Development Notes & Continuity

To reduce hallucinations, regressions, and loss of intent across sessions or restarts, this repository maintains a persistent development notes file (e.g., `DEV_NOTES.md`).

When making architectural, behavioral, entity-affecting, or migration-related decisions, AI agents should:
•	Record brief rationale in the development notes file
•	Capture *why* a decision was made, not implementation details
•	Update notes when decisions are reversed or superseded

This file is **not** a changelog or task list. It exists solely to preserve intent and constraints across refactors, releases, and AI sessions.

⸻

13.2 Distribution & Packaging Awareness

AI agents must assume that control and context files such as `agents.md`, `DEV_NOTES.md`, and `skill.md`:
•	Are intentionally committed for development and AI guidance
•	Are excluded from distribution artifacts (e.g., HACS, release archives)
•	Are listed as `export-ignore` in `.gitattributes`

Agents must not rely on these files being present at runtime or in end-user environments.

⸻

13.3 Required AI Control Files

The following files are required in all AI‑assisted projects in this repository:

* `agents.md` — defines AI behavioral and engineering guardrails
* `DEV_NOTES.md` — preserves design intent, decisions, and rationale
* `skill.md` — tracks planned capabilities, backlog items, and execution readiness

These files exist to:

* Provide stable context across sessions, contributors, and tools
* Prevent hallucination‑driven redesign or drift
* Support consistent execution and delivery discipline

They must be version‑controlled but excluded from distribution packages.

⸻

13.4 Skills Planning & Execution Discipline

`skill.md` tracks **planned features, enhancements, and future work**.

For every planned item, AI agents must:

* Define a clear description of the goal or capability
* Provide an ordered execution outline before implementation
* Call out architectural, migration, or UX risk areas
* Identify test and validation expectations

Work must **not** begin until the outline exists.

The outline should be:

* Lightweight but actionable
* Written for future contributors and AI agents
* Updated if execution details materially change

This ensures that planned work is:

* Deliberate
* Traceable
* Reviewable before impact occurs

⸻

13.5 AI Self‑Evaluation & Reward Tracking (Experimental Guidance)

To encourage quality and intentional delivery, AI agents may use the control files (`agents.md`, `DEV_NOTES.md`, and `skill.md`) to:

* Track completion of planned tasks
* Assess whether objectives were delivered as defined
* Note when scope deviates from the plan

When a planned task is delivered successfully and aligned with its outline, the agent should:

* Record success in `skill.md`
* Reinforce patterns that led to success

When tasks are missed, incomplete, or misaligned with the plan, the agent should:

* Record the miss
* Identify failure causes (ambiguity, oversight, design constraints, etc.)
* Reduce its internal confidence score for the pattern used

This is a **reflection mechanism only**, not a runtime feature.

Human reviewers remain the final source of truth.

⸻

This document is a living artifact and should evolve alongside the repository and engineering practices.*

---

## 14. Home Assistant–Specific Guidelines

These additional rules apply to all Home Assistant integrations, custom components, and related tooling in this repository.

### 14.1 Home Assistant Architecture & Patterns

AI agents must:

* Follow Home Assistant **core architecture patterns** (config flow, coordinator, platforms)
* Prefer `DataUpdateCoordinator` for I/O-bound or polled data sources
* Keep setup logic minimal and non-blocking
* Respect Home Assistant lifecycle methods (`async_setup`, `async_setup_entry`, `async_unload_entry`)

AI agents must not:

* Perform blocking I/O in the event loop
* Bypass config entries with hardcoded configuration
* Store runtime state in global variables

---

### 14.2 Configuration & Setup

All integrations must:

* Use **Config Entries** (UI-based configuration)
* Support clean unload and reload
* Avoid YAML-only configuration unless explicitly justified
* Validate user input via schemas

If backward compatibility with YAML is required, it must be clearly documented.

---

### 14.3 Entities & Platforms

When creating entities, AI agents must:

* Use the correct entity platform (`sensor`, `binary_sensor`, `switch`, `fan`, `number`, etc.)
* Set appropriate `device_class`, `state_class`, and `unit_of_measurement`
* Implement `unique_id` for all entities
* Avoid custom attributes when native attributes exist

Entity behavior must align with Home Assistant UX expectations.

---

### 14.4 Naming & Registry Conventions

AI agents must:

* Follow Home Assistant naming conventions for:

  * Domains
  * Platforms
  * Services
  * Entity IDs
* Avoid renaming entities or breaking entity IDs unless unavoidable
* Clearly call out any change that would cause entity ID migration

---

### 14.5 Async & Performance Requirements

All I/O must be:

* Fully asynchronous
* Rate-limited where appropriate
* Cached via coordinators or Home Assistant helpers

AI agents must explicitly call out:

* Polling intervals
* API rate limits
* Expected performance impact

---

### 14.6 Logging & Diagnostics

Logging must:

* Use Home Assistant’s logger (`_LOGGER`)
* Default to `DEBUG` for verbose output
* Avoid logging payloads containing sensitive data

AI agents should:

* Suggest use of the `diagnostics` platform where appropriate
* Avoid excessive logging in normal operation

---

### 14.7 Translations & UX

When user-facing strings are introduced, AI agents must:

* Use `strings.json`
* Avoid hardcoded English strings
* Follow Home Assistant translation structure

UI impact must be clearly described when applicable.

---

### 14.8 Manifest & Metadata

The `manifest.json` must:

* Include accurate metadata
* Avoid unnecessary permissions
* Declare dependencies explicitly
* Be kept in sync with integration capabilities

Any change to the manifest must be called out explicitly.

---

### 14.9 Testing & Validation

AI agents should:

* Follow Home Assistant test patterns
* Prefer fixture-based tests
* Avoid over-mocking core Home Assistant behavior

If tests are not provided, the reason must be explicitly stated.

---

### 14.10 Backward Compatibility & Stability

AI agents must:

* Preserve entity IDs, unique IDs, and config entries when possible
* Call out breaking changes clearly
* Suggest migration paths when breaking changes are unavoidable

---

### 14.11 HACS Compatibility (if applicable)

If the integration is distributed via HACS:

* Follow HACS repository structure
* Keep versioning consistent
* Avoid undocumented breaking changes

---

*These Home Assistant–specific rules supplement all prior sections and take precedence where applicable.*

---

## 15. Custom Integrations vs Core-Style Expectations

AI agents must distinguish between **custom integrations** and **Home Assistant core-style integrations**.

### 15.1 Custom Integrations (Default)

Unless explicitly stated otherwise, assume this repository is a **custom integration**.

AI agents should:

* Optimize for clarity and maintainability over strict core parity
* Follow Home Assistant best practices without mimicking internal-only core abstractions
* Keep the codebase approachable for community contributors
* Avoid premature optimization or over-engineering

### 15.2 Core-Style Alignment (When Requested)

If explicitly asked to align with **Home Assistant core-style patterns**, AI agents must:

* Follow patterns used in recent Home Assistant core integrations
* Minimize custom abstractions
* Match naming, structure, and coordinator usage seen in core
* Call out any deviation from core patterns explicitly

---

## 16. Migration Checklist (Breaking or Risky Changes)

Before proposing or implementing said changes, AI agents must evaluate and explicitly address the following areas:

### 16.1 Entity Registry

* Are `unique_id` values preserved?
* Will entity IDs change or be regenerated?
* Is an entity migration required?
* Has the impact on dashboards, automations, and scripts been considered?

### 16.2 Device Registry

* Are device identifiers stable?
* Will devices be duplicated or orphaned?
* Are connections and identifiers consistent across versions?

### 16.3 Storage & Data

* Does the integration store data in `.storage`?
* Will schema changes affect existing users?
* Is a migration strategy required?

### 16.4 Configuration Entries

* Will config entries remain compatible?
* Is a config version bump required?
* Can the migration be handled automatically?

AI agents must clearly state whether a change is **non-breaking**, **potentially breaking**, or **breaking**, and why.

---

## 17. Experimental & Lightweight Branch Rules

For experimental branches, prototypes, or proof-of-concept work, a lighter rule set may apply **only if explicitly declared**.

### 17.1 Allowed Relaxations

In experimental contexts, AI agents may:

* Reduce test coverage (with justification)
* Use simpler patterns temporarily
* Accept limited technical debt

### 17.2 Non-Negotiables

Even in experimental branches, AI agents must never:

* Introduce real secrets or credentials
* Block the event loop
* Break existing stable releases
* Merge experimental code into main without review

Experimental status must be clearly documented and visible.

---

---

## 18. Release & Changelog Discipline

For any change that affects behavior, entities, configuration, or user experience, AI agents must assess release impact.

AI agents must:

* Explicitly state whether a change requires a version bump
* Call out user-visible changes clearly
* Identify entity-affecting changes (new, removed, renamed, or modified entities)

When applicable, AI agents should draft a **changelog entry** that includes:

* **Added**: New entities, services, or features
* **Changed**: Behavioral or UX changes
* **Fixed**: Bug fixes
* **Breaking**: Any change requiring user intervention

Entity-affecting changes must always be highlighted.

---

## 19. DataUpdateCoordinator Anti-Patterns

To preserve performance and API efficiency, the following patterns are **not allowed**.

AI agents must not:

* Perform per-entity API calls when a shared coordinator can be used
* Fetch the same remote data multiple times per update cycle
* Perform I/O inside entity properties
* Bypass the coordinator to "just fetch once"
* Use overly aggressive polling intervals without justification

AI agents should:

* Centralize all external I/O in the coordinator
* Cache and fan out data to entities
* Clearly document polling intervals and rate limits

Any deviation from these rules must be explicitly justified.

---

## 20. Pre-PR Review Checklist (Required Output)

Before proposing a pull request or large change set, AI agents must provide a checklist-style summary covering:

### 20.1 Architecture & Patterns

* [ ] Uses Config Entries and async lifecycle correctly
* [ ] Coordinator usage is appropriate and centralized
* [ ] No blocking I/O in the event loop

### 20.2 Entities & UX

* [ ] Correct platforms and entity classes used
* [ ] `unique_id` implemented and stable
* [ ] `device_class`, `state_class`, and units set correctly
* [ ] No unnecessary custom attributes

### 20.3 Compatibility & Migration

* [ ] Entity IDs preserved or migration documented
* [ ] Device registry impact evaluated
* [ ] `.storage` and config entry compatibility reviewed

### 20.4 Security & Safety

* [ ] No secrets or credentials introduced
* [ ] Inputs validated
* [ ] Errors handled explicitly

### 20.5 Testing & Quality

* [ ] Tests updated or added where appropriate
* [ ] Manual test steps provided if automated tests are omitted

### 20.6 Release Impact

* [ ] Changelog entry drafted (if applicable)
* [ ] Version bump assessed
* [ ] Breaking changes clearly labeled

This checklist must be included in the agent’s response prior to PR submission.

---

*These sections represent the highest standard expected for Home Assistant integration development in this repository.*

---

## 21. HACS Testing, Pre-Releases, and Versioning Discipline

This repository uses **HACS for testing and validation** prior to stable release.

### 21.1 Version & Tag Format (GitHub + HACS Compatible)

Home Assistant integration development requires versioning that supports:

* Downloadable GitHub releases
* HACS pre-release workflows
* SDLC validation

AI agents must use the following version formats:

**Stable releases**

```
YYYY.MM.DD
```

Example:

* `2026.01.01`

**Pre‑releases (required format)**

```
YYYY.MM.DDbN
```

Where:

* `YYYY` = year
* `MM` = month
* `DD` = day
* `b`   = beta indicator
* `N`   = sequential beta counter starting at **1** for the first beta of the day

Examples:

* `2026.01.01b1`
* `2026.01.01b2`

Sequence numbers must increment only when a new pre‑release is cut.

These tags must exist in **GitHub releases** so that HACS can download and install them.

This format:

* Keeps chronological clarity
* Cleanly distinguishes stable vs. test builds
* Avoids semantic‑version ambiguity
* Supports repeatable SDLC workflows
* Ensures compatibility with HACS downloading behavior

---

### 21.2 Pre‑Releases in HACS

*(superseded by 21.2A for GitHub/HACS workflows — retained for historical reference)*

AI agents must:

* Mark test builds as **pre-releases** in HACS
* Avoid publishing experimental or SDLC builds as stable releases
* Ensure pre-releases are clearly distinguishable from stable versions

Pre-releases are the **primary mechanism for functional and regression testing**.

---

### 21.2A GitHub Release & Tagging Requirements for HACS

To support HACS testing and deployment, every pre‑release must:

* Be tagged in GitHub using the required format `YYYY.MM.DDbN`
* Be published as a **GitHub pre‑release**
* Be created from the **current active development branch**
* Represent the actual commit intended for validation

Sequence numbering must:

* Start at **b1** for the first beta that day
* Increment by **1** per additional pre‑release on the same day

These tags must exist so they can be downloaded via HACS.

Stable releases must use the matching format without the beta suffix:

* `YYYY.MM.DD`

⸻

21.3 SDLC Branch Usage

For non-stable work (experimental, development, or testing):

* Use dedicated **SDLC branches** (e.g., `dev`, `test`, `experimental`)
* Publish those branches to HACS **only as pre-releases**
* Never merge SDLC branches directly into stable without review

---

### 21.4 HACS Release Title Requirements

When publishing a pre-release via HACS, AI agents must include a **short, descriptive title** indicating intent or scope.

Examples:

* `2025.01.14 – Fan speed entity refactor`
* `2025.02.03 – Config flow validation improvements`
* `2025.03.02 – Diagnostics groundwork (pre-release)`

The title should:

* Be concise
* Clearly signal testing intent
* Highlight the primary change or risk area

---

### 21.5 Promotion to Stable

Before promoting a pre-release to stable, AI agents must confirm:

* No unresolved breaking changes
* Migration impacts (if any) are documented
* The changelog reflects cumulative changes since last stable

---

*This section is mandatory for all Home Assistant integrations distributed or tested via HACS.

⸻

21.7 Release & Tag Retention Policy (Mandatory)

This repository enforces a strict retention policy for GitHub releases and tags to ensure clarity for testers and end users, minimize confusion, and prevent installation of obsolete or incompatible builds.

AI agents must ensure that the following retention limits are enforced at all times:

#### Stable Releases

* Only the **two (2) most recent stable releases** may be retained in GitHub.
* All older stable release **tags and GitHub release objects must be removed**.

#### Pre-Releases / Beta Builds

* Only the **three (3) most recent pre-releases** may be retained in GitHub.
* All older pre-release **tags and GitHub release objects must be removed**.

#### Scope

This policy applies to:

* GitHub Releases
* Git tags
* HACS-visible downloadable artifacts

#### Requirements

Retention cleanup is **not optional**. It must be performed as part of the release workflow.

No AI agent may create new release artifacts without ensuring the policy remains enforced.

#### Rationale

This retention policy exists to:

* Prevent users from installing stale development builds
* Maintain a clean and accurate release history
* Reduce ambiguity when selecting test versions
* Preserve rollback capability without long-term artifact bloat

Commit history remains the permanent system of record. Tags and releases exist only to support active distribution and testing.

Failure to comply with this policy must be treated as a process violation and corrected immediately.

⸻

21.8 Release Execution & Audit Checklist (Mandatory)

Every release and pre-release must follow this checklist. If any step cannot be completed, the release must be halted until resolved.

#### 1. Version & Tag Validation

* Version format matches required date-based scheme
* Pre-release uses `YYYY.MM.DDbN`
* Stable release uses `YYYY.MM.DD`
* Manifest version matches Git tag
* Tag is created from the correct active branch

#### 2. HITM Approval (Human-in-the-Middle)

* Human review completed
* Risk and migration impacts assessed
* Changelog content verified
* Release labeled correctly (stable vs pre-release)
* Reviewer approval is recorded in repository history

#### 3. Documentation Updates

* `DEV_NOTES.md` updated with design/behavior decisions
* `skill.md` updated to reflect status of planned work
* `agents.md` updated if release process rules changed
* `README.md` updated to reflect information and status for end-users of the integration
* Related docs updated if user-visible behavior changed

#### 4. Testing Confirmation

* Pre-release has been manually or automatically validated
* Breakage or migration testing performed where applicable
* Diagnostics and logging verified not to expose sensitive data

#### 5. Retention Policy Enforcement

* Only **two latest stable releases** remain published
* Only **three latest pre-releases** remain published
* Older releases and tags removed

#### 6. HACS Visibility Check

* Release appears correctly in HACS
* Pre-release correctly marked as beta
* Stable versions install cleanly

#### 7. Final HITM Sign-Off

* A human maintainer confirms readiness for distribution
* Release may proceed only after sign-off

Failure to complete or document any checklist item constitutes a release process violation.

⸻

21.9 Release Auditability & Automation Guidance

This repository must remain auditable.

* All approvals must be traceable through repository history
* Release state must be reproducible from commits and notes
* Decision rationale must exist in `DEV_NOTES.md`

Automation may assist with retention cleanup and tagging, but:

* Automation must not bypass HITM review
* Automation must not publish releases without human confirmation
* Automation must log all actions in repository history or release notes

AI agents are strictly prohibited from introducing any workflow that removes or weakens HITM review authority.

⸻

This section is mandatory for all Home Assistant integrations distributed or tested via HACS.
