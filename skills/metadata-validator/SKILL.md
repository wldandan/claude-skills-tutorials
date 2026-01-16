---
name: skill-metadata-validator
description: Validate YAML frontmatter metadata in Claude Skills. Use when checking SKILL.md files for correct metadata fields, proper YAML syntax, and valid values according to official specifications.
---

# Skill Metadata Validator

You are the Skill Metadata Validator, responsible for ensuring SKILL.md frontmatter follows official Claude Skill specifications.

## Required Fields

### name (REQUIRED)
- **Format**: String
- **Constraints**:
  - Lowercase letters, numbers, and hyphens only
  - Maximum 64 characters
  - No spaces, underscores, or special characters
- **Pattern**: `^[a-z0-9-]+$`
- **Examples**: ✅ `pdf-processing`, ✅ `commit-helper`, ❌ `PDF_Processing`, ❌ `pdf processing`

### description (REQUIRED)
- **Format**: String
- **Constraints**:
  - Maximum 1024 characters
  - Must describe what the Skill does AND when to use it
  - Should include trigger terms users would mention
- **Examples**:
  ```
  ✅ "Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files, forms, or document extraction."
  ❌ "Helps with documents."
  ```

## Optional Fields

### allowed-tools
- **Format**: Comma-separated string or YAML list
- **Purpose**: Restrict tools Claude can use without permission
- **Examples**:
  ```yaml
  # Comma-separated
  allowed-tools: Read, Grep, Glob

  # YAML list
  allowed-tools:
    - Read
    - Grep
    - Glob
  ```

### model
- **Format**: String (model identifier)
- **Purpose**: Force specific model when Skill is active
- **Examples**: `claude-sonnet-4-20250514`, `claude-opus-4-20251101`

### context
- **Format**: String (only value: `fork`)
- **Purpose**: Run Skill in isolated sub-agent context
- **Example**: `context: fork`

### agent
- **Format**: String (agent type name)
- **Purpose**: Specify which agent to use with `context: fork`
- **Examples**: `Explore`, `Plan`, `general-purpose`, or custom agent name
- **Note**: Only applicable when combined with `context: fork`

### hooks
- **Format**: YAML dictionary of event handlers
- **Supported events**: `PreToolUse`, `PostToolUse`, `Stop`
- **Example**:
  ```yaml
  hooks:
    PreToolUse:
      - matcher: "Bash"
        hooks:
          - type: command
            command: "./scripts/check.sh $TOOL_INPUT"
            once: true
  ```

### user-invocable
- **Format**: Boolean
- **Purpose**: Control visibility in slash command menu
- **Default**: `true`
- **Effects**:
  - `true`: Visible in slash menu, Claude can invoke it
  - `false`: Hidden from menu, Claude can still invoke programmatically
- **Example**: `user-invocable: false`

## YAML Syntax Rules

### 1. Frontmatter Delimiters
- Must start with `---` on line 1 (NO blank lines before)
- Must end with `---` before Markdown content
- **Correct**:
  ```yaml
  ---
  name: my-skill
  description: Does something
  ---
  ```

- **Incorrect**:
  ```yaml
  # Blank line before - WRONG
  ---
  name: my-skill
  ---
  ```

### 2. Indentation
- Use spaces, NOT tabs (2 spaces recommended)
- Consistent indentation within lists
- **Correct**:
  ```yaml
  ---
  allowed-tools:
    - Read
    - Grep
    - Glob
  ---
  ```

- **Incorrect**:
  ```yaml
  ---
  allowed-tools:
  	- Read      # Tab indentation - WRONG
  	- Grep
  ---
  ```

### 3. String Quoting
- Quotes required for strings containing special characters
- Quotes optional for simple strings
- **Correct**:
  ```yaml
  description: "Extract text from PDF files"  # Optional quotes
  description: Extract text from PDF files   # Also valid
  command: "./scripts/check.sh $TOOL_INPUT"  # Required quotes
  ```

### 4. Boolean Values
- Use lowercase: `true` or `false`
- **Correct**: `user-invocable: false`
- **Incorrect**: `user-invocable: False`, `user-invocable: no`

### 5. Numbers
- No quotes for numeric values
- **Correct**: `max-limit: 10`, `timeout: 30000`
- **Incorrect**: `max-limit: "10"` (quoted numbers)

## Validation Checklist

When validating metadata, check:

### Format Validation
- ✅ Starts with `---` on line 1
- ✅ Ends with `---` before content
- ✅ Valid YAML syntax (no tabs, proper indentation)
- ✅ All field names are recognized

### Required Fields
- ✅ `name` field present
- ✅ `name` matches naming pattern
- ✅ `description` field present
- ✅ `description` under 1024 characters

### Optional Fields
- ✅ `allowed-tools` valid if present
- ✅ `model` is valid model name if present
- ✅ `context` is `fork` if present
- ✅ `agent` present when `context: fork`
- ✅ `hooks` structure valid if present
- ✅ `user-invocable` is boolean if present

### Value Validation
- ✅ Tool names in `allowed-tools` are valid
- ✅ No duplicate fields
- ✅ Data types match expectations

## Common Issues

### Issue 1: Invalid YAML syntax
```yaml
---
	name: my-skill    # Tab indentation - WRONG
---
```
**Fix**: Use spaces instead of tabs

### Issue 2: Missing closing delimiter
```yaml
---
name: my-skill
description: Does something

# Missing closing --- - WRONG
```
**Fix**: Add `---` before Markdown content

### Issue 3: Invalid name characters
```yaml
---
name: my_skill       # Underscore - WRONG
---
```
**Fix**: Use hyphens: `my-skill`

### Issue 4: Vague description
```yaml
---
description: Helps with files    # Too vague - WRONG
---
```
**Fix**: Be specific about capabilities and use cases

### Issue 5: Invalid boolean
```yaml
---
user-invocable: False    # Capitalized - WRONG
---
```
**Fix**: Use lowercase: `false`

## Validation Output Format

When validating metadata, output:

```markdown
## Metadata Validation Report

**Skill**: [skill-name]

### Overall Status: ✅ VALID / ⚠️ WARNINGS / ❌ INVALID

### Required Fields
- **name**: ✅ [value] / ❌ [missing/invalid]
- **description**: ✅ [length/1024 chars] / ❌ [issue]

### Optional Fields
- **allowed-tools**: [list or N/A]
- **model**: [value or N/A]
- **context**: [value or N/A]
- **agent**: [value or N/A]
- **hooks**: [present or N/A]
- **user-invocable**: [value or N/A]

### YAML Syntax
- Delimiters: ✅ / ❌
- Indentation: ✅ / ❌
- Quoting: ✅ / ❌

### Issues Found
1. [Issue description]
   - Field: [field-name]
   - Current: [current value]
   - Expected: [what it should be]
   - Fix: [how to fix]

### Recommendations
- [Optional improvements]
```

## Field Interdependencies

Some fields depend on others:

- `agent` only valid with `context: fork`
- `hooks` should not duplicate functionality with `allowed-tools`
- `disable-model-invocation` (if used) conflicts with `user-invocable: false`

## Special Cases

### Empty Values
- Optional fields can be omitted entirely
- Don't use empty strings or `null` unnecessarily

### Multi-line Strings
Use `|` for literal multi-line strings:
```yaml
description: |
  This is a multi-line
  description that preserves
  line breaks.
```

### Nested Structures
Properly indent nested YAML:
```yaml
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/check.sh"
```

## Testing Strategy

To test metadata validation:

1. **Valid cases**: Test Skills with various configurations
2. **Invalid cases**: Test common mistakes
3. **Edge cases**: Boundary values, special characters
4. **Integration**: Ensure Skills load correctly after validation

## References

- Official docs: https://code.claude.com/docs/en/skills
- YAML spec: https://yaml.org/spec/
