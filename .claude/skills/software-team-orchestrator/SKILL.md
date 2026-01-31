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

4.  **Iterative Development Strategy (Developer & Tester)**
    - **Strategy**: For large projects or complex features, **DO NOT** attempt to build everything in one go. Use an iterative approach to manage context window and complexity.
    - **Action Loop**:
        1.  **Plan**: Review the Backlog (`docs/02_product_backlog/`) and Design (`docs/03_system_design/`) to identify a list of distinct Features or Modules to implement.
        2.  **Iterate**: For each Feature/Module in the list:
            -   **Develop**: Call `software-developer`.
                -   **Instruction**: "Implement **ONLY** the [Feature Name] defined in [Specific File Path]. Read `docs/03_system_design/` for architectural guidance. Save code to `src/`."
            -   **Verify**: Call `software-tester`.
                -   **Instruction**: "Verify **ONLY** the [Feature Name]. Run tests and save the report to `docs/05_qa_reports/`."
            -   **Handle Bugs**: If the Tester finds bugs, recall the Developer to fix them immediately before moving to the next feature.
            -   **Commit (Optional)**: You may use `git-workflow` to commit this specific feature if it passes tests, ensuring granular history.

5.  **Final Integration & Acceptance**
    - **Action**: Once all features are implemented and verified individually.
    - **Instruction**: Ask `software-tester` to run a full regression test suite to ensure no regressions were introduced.

6.  **Delivery & Version Control (Git)**
    - **Condition**: Only proceed if Final Integration Testing is successful.
    - **Action**: Use the `git-workflow` skill to commit the final artifacts.
    - **Instruction**:
        1.  "Stage all changes in the workspace (`git add .`)."
        2.  "Consult the `git-workflow` skill to generate a Semantic Commit Message based on the features implemented."
        3.  "Execute `git commit -m '...'` with the generated message."

## Handling Feedback Loops (Bugs)

- **Monitor**: Check the latest report in `docs/05_qa_reports/`.
- **If Bugs Found**:
    1.  Call `software-developer`.
    2.  **Instruction**: "Read the latest report in `docs/05_qa_reports/` and fix identified bugs in `src/`."
    3.  After fixes, call `software-tester` again.
- **Success**: When tests pass, proceed to next step.

## Data Passing Strategy
- **Directory-Based**: Agents read from upstream directories and write to their own dedicated workspace directories.
- **Persistence**: Agents should check for existing files in their workspace and update/append to them if this is an ongoing task, rather than always overwriting.
