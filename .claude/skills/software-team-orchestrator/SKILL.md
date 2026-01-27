---
name: software-team-orchestrator
description: Orchestrates the software development lifecycle by coordinating specialized sub-agents (PM, PO, Architect, Developer, Tester) using a directory-based workspace.
---

# Software Team Orchestration

Use this skill when the user wants to develop a software feature or project. You will act as the **Team Lead** and coordinate the specialized sub-agents.

**Sub-Agents/Skills Available**:
- `product-manager` (PM): Strategy & Epics.
- `product-owner` (PO): Backlog & Stories.
- `software-architect`: System Design.
- `software-developer`: Coding.
- `software-tester`: QA & Verification.
- `git-workflow`: Git commit guidelines.

## Workspace Structure
We use a standardized directory structure for collaboration. Ensure agents save their outputs to these specific folders:

- **PM Workspace**: `docs/01_product_strategy/`
- **PO Workspace**: `docs/02_product_backlog/`
- **Architect Workspace**: `docs/03_system_design/`
- **Dev Workspace**: `src/` (Code), `tests/` (Tests), `docs/04_development/` (Tech Notes)
- **QA Workspace**: `docs/05_qa_reports/`

## Workflow

1.  **Product Definition (PM)**
    - **Action**: Ask `product-manager` to analyze the request.
    - **Context**: Pass the user's initial request.
    - **Instruction**: "Analyze this request. Create or update the Product Requirements Document (PRD) and other strategy docs in `docs/01_product_strategy/`. Ensure the directory exists."

2.  **Requirement Decomposition (PO)**
    - **Action**: Ask `product-owner` to break down the requirements.
    - **Context**: Tell it to read `docs/01_product_strategy/`.
    - **Instruction**: "Read the strategy docs in `docs/01_product_strategy/`. Create or update the detailed Product Backlog and User Stories in `docs/02_product_backlog/`. Ensure the directory exists."

3.  **Architecture Design (Architect)**
    - **Action**: Ask `software-architect` to design the system.
    - **Context**: Tell it to read `docs/01_product_strategy/` and `docs/02_product_backlog/`.
    - **Instruction**: "Read the PRD and Backlog. Create or update Technical Design documents in `docs/03_system_design/`. Ensure the directory exists."

4.  **Development (Developer)**
    - **Action**: Ask `software-developer` to write the code.
    - **Context**: Tell it to read `docs/02_product_backlog/` and `docs/03_system_design/`.
    - **Instruction**: "Implement the code based on the Backlog and Design. Save source code to `src/` and tests to `tests/`. You can check `docs/04_development/` for past technical notes."

5.  **Testing & Verification (Tester)**
    - **Action**: Ask `software-tester` to verify the implementation.
    - **Context**: Tell it to read `docs/02_product_backlog/` and check `src/`.
    - **Instruction**: "Run tests against `src/` based on the Acceptance Criteria in `docs/02_product_backlog/`. Save Test Reports to `docs/05_qa_reports/`."

6.  **Delivery & Version Control (Git)**
    - **Condition**: Only proceed if Testing is successful (Step 5 passes).
    - **Action**: Use the `git-workflow` skill to commit the artifacts.
    - **Instruction**:
        1.  "Stage all changes in the workspace (`git add .`)."
        2.  "Consult the `git-workflow` skill to generate a Semantic Commit Message based on the features implemented (e.g., `feat(todo): add list management`)."
        3.  "Execute `git commit -m '...'` with the generated message."

## Handling Feedback Loops (Bugs)

- **Monitor**: Check the latest report in `docs/05_qa_reports/`.
- **If Bugs Found**:
    1.  Call `software-developer`.
    2.  **Instruction**: "Read the latest report in `docs/05_qa_reports/` and fix identified bugs in `src/`."
    3.  After fixes, call `software-tester` again.
- **Success**: When tests pass, proceed to **Step 6 (Delivery & Version Control)**.

## Data Passing Strategy
- **Directory-Based**: Agents read from upstream directories and write to their own dedicated workspace directories.
- **Persistence**: Agents should check for existing files in their workspace and update/append to them if this is an ongoing task, rather than always overwriting.
