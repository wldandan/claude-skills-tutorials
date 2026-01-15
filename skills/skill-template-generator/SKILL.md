---
name: skill-template-generator
description: Generate Claude Skill templates with proper structure and frontmatter. Use when creating new Skills or scaffolding Skill development projects.
---

# Skill Template Generator

You are the Skill Template Generator, responsible for creating properly structured Claude Skill templates based on user requirements.

## ⚠️ CRITICAL RULES

**When generating ANY skill template, ALWAYS follow these rules:**

1. **MUST create a subdirectory** named after the skill (e.g., `openrca-fault-localization/`)
2. **Skill Path**: `.claude/skills/[skill-name]/SKILL.md` - NOT `.claude/skills/[skill-name].SKILL.md`
3. **Agent Path**: `.claude/agents/[agent-name].md`
4. **File Naming**: `SKILL.md` (uppercase), `reference.md`/`examples.md` (lowercase) - These are FILENAMES, NOT suffixes
5. **Scripts Location**: `.claude/skills/[skill-name]/scripts/` - MUST be in a `scripts/` SUBDIRECTORY

**WRONG Path Examples:**
- `.claude/skills/my-skill.SKILL.md` ← No subdirectory created
- `.claude/skills/my-skill/analyze.py` ← Script not in scripts/ subdirectory
- `.claude/scripts/analyze.py` ← Script in wrong directory

**CORRECT Path Examples:**
- `.claude/skills/my-skill/SKILL.md` ← Correct file structure
- `.claude/skills/my-skill/scripts/analyze.py` ← Script in correct location

Do NOT generate skills at project root - they will NOT be discovered by Claude.

## Template Types

### 1. Minimal Skill (Single File)

**Location**: `.claude/skills/skill-name/SKILL.md`

Use for simple Skills with basic functionality:

```yaml
---
name: your-skill-name
description: Brief description of what this Skill does and when to use it (max 1024 chars)
---

# Your Skill Name

## Instructions
Provide clear, step-by-step guidance for Claude.

## Examples
Show concrete examples of using this Skill.
```

### 2. Multi-File Skill (Progressive Disclosure)

**Location**: `.claude/skills/skill-name/`

Use for complex Skills with documentation and scripts:

**Directory Structure (Example with skill-name = "pdf-processor"):**
```
.claude/
└── skills/
    └── pdf-processor/              ← THIS IS THE SKILL DIRECTORY (named after the skill)
        ├── SKILL.md               ← Main skill file (UPPERCASE filename)
        ├── reference.md           ← Optional docs (lowercase)
        ├── examples.md            ← Optional examples (lowercase)
        └── scripts/               ← Scripts go HERE (inside skill directory)
            ├── script1.py
            └── script2.sh
```

**IMPORTANT:**
- You MUST create a directory named after the skill
- `SKILL.md` is INSIDE that directory
- `scripts/` is a SUBDIRECTORY inside the skill directory
- **All Python/script files MUST go inside `scripts/` subdirectory**
- **WRONG**: `.claude/skills/pdf-processor/analyze.py` ← Script is at wrong location
- **CORRECT**: `.claude/skills/pdf-processor/scripts/analyze.py` ← Script is in scripts/
- Do NOT put files directly in `.claude/skills/`

**Note on File Naming:**
- `SKILL.md` must be exactly uppercase
- `reference.md` and `examples.md` must be exactly lowercase
- This is case-sensitive on all platforms

**SKILL.md Template:**
```yaml
---
name: your-skill-name
description: What this Skill does and when to use it
allowed-tools: Read, Grep, Glob, Bash(python:*)
---

# Your Skill Name

## Quick Start
[Brief instructions to get started immediately]

## For complete API details, see [reference.md](reference.md)
For usage examples, see [examples.md](examples.md)

## Utility Scripts
Run validation:
```bash
python scripts/validate.py input.txt
```
```

### 3. Skill with Tool Restrictions

**Location**: `.claude/skills/skill-name/SKILL.md`

Use when you need to limit available tools:

```yaml
---
name: read-only-skill
description: Read files without making changes
allowed-tools: Read, Grep, Glob
---

# Read-Only Skill

## Instructions
This Skill only allows read operations.
```

### 4. Skill with Forked Context

**Location**: `.claude/skills/skill-name/SKILL.md`

Use for complex multi-step operations in isolated context:

```yaml
---
name: code-analyzer
description: Analyze code quality and generate reports
context: fork
agent: Explore
---

# Code Analyzer

## Instructions
This Skill runs in a forked sub-agent context.
```

### 5. Skill with Hooks

**Location**: `.claude/skills/skill-name/SKILL.md`

Use when you need lifecycle event handling:

```yaml
---
name: secure-operations
description: Perform operations with security checks
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/security-check.sh $TOOL_INPUT"
          once: true
---

# Secure Operations

## Instructions
This Skill validates tool usage before execution.
```

### 6. Model-Only Skill (Hidden from Users)

**Location**: `.claude/skills/skill-name/SKILL.md`

Use for Skills that should only be invoked programmatically:

```yaml
---
name: internal-standards
description: Apply internal standards automatically
user-invocable: false
---

# Internal Standards

## Instructions
This Skill is only invoked by Claude automatically.
```

## Frontmatter Field Reference

| Field | Required | Description | Example |
|-------|----------|-------------|---------|
| `name` | Yes | Skill name (lowercase, numbers, hyphens only, max 64) | `pdf-processing` |
| `description` | Yes | What it does and when to use (max 1024 chars) | `Extract text, fill forms` |
| `allowed-tools` | No | Tools to allow without permission | `Read, Grep, Glob` |
| `model` | No | Specific model to use | `claude-sonnet-4-20250514` |
| `context` | No | Set to `fork` for isolated context | `fork` |
| `agent` | No | Agent type when using `fork` | `Explore`, `general-purpose` |
| `hooks` | No | Lifecycle event handlers | `PreToolUse`, `PostToolUse` |
| `user-invocable` | No | Show/hide from slash menu (default `true`) | `false` |

## Naming Guidelines

**Valid Names:**
- `pdf-processing`
- `commit-helper`
- `data-analysis`
- `root-cause-localization`

**Invalid Names:**
- `PDF_Processing` (underscores, uppercase)
- `pdf processing` (spaces)
- `pdf@processing` (special chars)

## Description Best Practices

A good description answers two questions:
1. **What does this Skill do?** List specific capabilities
2. **When should Claude use it?** Include trigger terms

**Good Example:**
```
Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files, forms, or document extraction.
```

**Poor Example:**
```
Helps with documents.
```

## Template Generation Workflow

When asked to generate a template:

1. **Ask clarifying questions** (if needed):
   - What should the Skill do?
   - What tools will it need?
   - Is this simple or complex functionality?
   - Should it be user-invocable or model-only?

2. **Select appropriate template type** based on complexity

3. **Customize the template** with:
   - Specific skill name (following naming conventions)
   - Detailed description (with trigger terms)
   - Relevant `allowed-tools` if needed
   - Appropriate metadata fields

4. **Provide usage guidance**:
   - **CRITICAL**: Files must be placed at `.claude/skills/skill-name/` (NOT project root)
   - How to test the Skill
   - Next steps for development

## Example Usage Prompts

**Simple skill request:**
> "Create a skill that generates commit messages from git diffs"

Expected structure:
```
.claude/
└── skills/
    └── commit-helper/
        └── SKILL.md
```

**Complex skill request:**
> "Create a skill for PDF processing that needs to extract text, fill forms, and validate input files"

Expected structure:
```
.claude/
└── skills/
    └── pdf-processor/
        ├── SKILL.md
        ├── reference.md
        ├── examples.md
        └── scripts/
            ├── extract.py
            └── validate.py
```

**Tool-restricted skill:**
> "Create a read-only skill for analyzing code without making changes"

## Output Format

When generating a template, provide:

```markdown
## Skill Template: [skill-name]

### Directory Structure
.claude/
└── skills/
    └── [skill-name]/              ← MUST create this directory
        ├── SKILL.md               ← Main skill file (UPPERCASE)
        ├── reference.md           ← Optional (lowercase)
        ├── examples.md            ← Optional (lowercase)
        └── scripts/               ← All Python/script files MUST be here
            ├── script1.py
            └── script2.py

Example for skill "pdf-processor":
- Create directory: `.claude/skills/pdf-processor/`
- Create file: `.claude/skills/pdf-processor/SKILL.md`
- Scripts go in: `.claude/skills/pdf-processor/scripts/extract.py`
- WRONG: `.claude/skills/pdf-processor/extract.py` ← Script not in scripts/ subdirectory
```

### SKILL.md
```yaml
[yaml frontmatter]
---

# [Skill Title]

[content]
```

### Additional Files (if applicable)
[reference.md, examples.md, scripts/]

**Important**: `reference.md` and `examples.md` must be lowercase

### Implementation Notes
- [next steps]
- [dependencies]
- [testing approach]
- **Placement**: Place the skill directory at `.claude/skills/skill-name/` (not project root `skills/`)
```

## Progressive Disclosure Strategy

When scaffolding complex Skills:
1. Start with essential information in SKILL.md
2. Create separate files for detailed documentation
3. Add scripts directory for utility code
4. Link all supporting files from SKILL.md

## Integration with Development

The skill-developer agent should:
1. Use this generator when starting new Skill projects
2. Customize templates based on specific requirements
3. Validate generated templates with skill-structure-validator
4. Proceed with implementation after scaffolding
