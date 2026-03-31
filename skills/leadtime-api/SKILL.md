---
name: leadtime-api
description: Works with live Leadtime data through the production Public API on leadtime.app. Use when the user asks to check, create, update, or inspect tasks, projects, organizations, workspace data, or other Leadtime entities. Handles API key storage, OpenAPI spec caching, and multi-workspace profiles. Triggers on "check task", "list projects", "create via Leadtime API", "update task in Leadtime", "query Leadtime", or any request involving Leadtime production data.
---

# Leadtime Public API

Interact with the Leadtime production API at `https://leadtime.app/api/public`.

## Skill location

All scripts referenced below live relative to this skill's directory. Determine the skill root from the path of this `SKILL.md` file:

```bash
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." 2>/dev/null && pwd)"
# fallback: if running from SKILL.md context, the agent knows the install path
```

Helper scripts are in `$SKILL_DIR/scripts/`.

## Setup — API key

### 1. Check for existing credentials

Before prompting the user, search for `.leadtime-api-key.json` in this order:

1. Current working directory (`./.leadtime-api-key.json`)
2. Home directory (`~/.leadtime-api-key.json`)

```bash
for candidate in "./.leadtime-api-key.json" "$HOME/.leadtime-api-key.json"; do
  if [[ -f "$candidate" ]]; then
    KEYFILE="$candidate"
    break
  fi
done
```

If found, load and present available profiles to the user (company name + username). Let the user pick or default to the first profile.

### 2. Ask for an API key (if none found)

Prompt the user:

> I need a Leadtime API key to access your workspace.
> Create a Personal Access Token at: https://leadtime.app/leadtime/profile/api-tokens
> Then paste the key here.

### 3. Validate and enrich the key

After receiving the key, call the API to fetch account and workspace info:

```bash
# Fetch account info
curl -fsS -H "Authorization: Bearer $API_KEY" \
  -H "Accept: application/json" \
  https://leadtime.app/api/public/account/info

# Fetch workspace details
curl -fsS -H "Authorization: Bearer $API_KEY" \
  -H "Accept: application/json" \
  https://leadtime.app/api/public/workspace/details
```

Build a profile entry from the response:

```json
{
  "apiKey": "lt_...",
  "apiBase": "https://leadtime.app/api/public",
  "companyName": "Acme GmbH",
  "username": "Jane Doe",
  "email": "jane@acme.com",
  "workspaceId": "uuid",
  "domain": "acme",
  "addedAt": "2026-04-01T12:00:00Z"
}
```

### 4. Ask about persistent storage

Ask the user whether to save the key for future sessions:

> Should I save this API key for future use? I can store it in:
> 1. Your home directory (~/.leadtime-api-key.json) — available everywhere
> 2. This project directory (./.leadtime-api-key.json) — project-scoped
> 3. Don't save — I'll ask again next session

If the user agrees, write/merge the profile into the chosen `.leadtime-api-key.json`:

```bash
chmod 600 "$KEYFILE"
```

### Key file format (`.leadtime-api-key.json`)

```json
{
  "version": 1,
  "profiles": [
    {
      "apiKey": "lt_...",
      "apiBase": "https://leadtime.app/api/public",
      "companyName": "Acme GmbH",
      "username": "Jane Doe",
      "email": "jane@acme.com",
      "workspaceId": "uuid",
      "domain": "acme",
      "addedAt": "2026-04-01T12:00:00Z"
    }
  ]
}
```

Multiple workspaces are supported — each has its own entry in the `profiles` array. When the user has multiple profiles, show a summary and let them pick.

**Never** print the full API key back to the user. **Never** commit `.leadtime-api-key.json` to a repository.

## Setup — OpenAPI spec

Cache the OpenAPI specification in `/tmp` for the current session:

```bash
OPENAPI_FILE="/tmp/leadtime-openapi.json"
if [[ ! -f "$OPENAPI_FILE" ]]; then
  curl -fsS -o "$OPENAPI_FILE" https://leadtime.app/api/public/docs/json
fi
```

Re-fetch if:
- The file doesn't exist (new session)
- You get an unexpected 400/404 (spec may have changed)
- Discovering endpoints for a domain you haven't used yet

## Mandatory API workflow (NEVER skip steps)

Every API call — read or write — MUST follow this workflow. **Never guess field names, parameter types, or endpoint paths.**

### 1. DISCOVER — find the endpoint

```bash
python3 "$SKILL_DIR/scripts/openapi-helper.py" search <keyword>
```

Example: `search comment` finds `POST /tasks/{identifier}/comments`

### 2. LEARN — read the full schema BEFORE calling

```bash
python3 "$SKILL_DIR/scripts/openapi-helper.py" operation <METHOD> <path>
```

Shows exact field names, required vs optional, types, formats, enums, nested schemas, and response structure.

**This step is NOT optional.** The #1 cause of failed API calls is guessing field names instead of reading the schema.

### 3. PREPARE — build the payload

- Write JSON payloads to a temp file (avoids shell quoting issues with HTML)
- Use **exact** field names from step 2
- Include only required fields + fields the user asked to set

```bash
cat > /tmp/payload.json <<'EOF'
{ "comment": "<p>HTML content here</p>" }
EOF
```

### 4. EXECUTE — call the API

```bash
bash "$SKILL_DIR/scripts/leadtime-api.sh" POST /tasks/943/comments -f /tmp/payload.json
```

### 5. VERIFY — re-fetch after mutations

After any create/update/delete, re-fetch the entity to confirm the change took effect.

### Common mistakes this workflow prevents

| Mistake | Example | Fix |
|---------|---------|-----|
| Wrong field name | `{"body": "..."}` instead of `{"comment": "..."}` | Step 2: read the schema |
| Wrong ID type | Passing user UUID where employee UUID is expected | Step 2: read field descriptions |
| Missing required field | Omitting `comment` | Step 2: check required fields |
| Guessing endpoint path | `POST /tasks/943/comment` (singular) | Step 1: search first |
| Shell quoting breaks JSON | Inline `-d '{...}'` with HTML | Step 3: use temp file with `-f` |

## Helper scripts

### `leadtime-api.sh` — API wrapper

```bash
bash "$SKILL_DIR/scripts/leadtime-api.sh" METHOD /path [options]

Options:
  --keyfile PATH   Path to .leadtime-api-key.json (auto-detected if omitted)
  --profile INDEX  Profile index in the keyfile (default: 0)
  -d JSON          Inline JSON request body
  -f FILE          Read JSON request body from file
  -q QUERY         Append query string
  -o FILE          Write response body to file
  -H HEADER        Extra header (repeatable)
  --raw            Print raw response body
```

Examples:

```bash
bash "$SKILL_DIR/scripts/leadtime-api.sh" GET /tasks/947
bash "$SKILL_DIR/scripts/leadtime-api.sh" GET /tasks/grid -q "page=1&pageSize=10"
bash "$SKILL_DIR/scripts/leadtime-api.sh" PATCH /tasks/947 -d '{"title":"Updated"}'
bash "$SKILL_DIR/scripts/leadtime-api.sh" GET /tasks/947 --profile 1
```

### `openapi-helper.py` — query cached OpenAPI spec

```bash
# Search endpoints by keyword
python3 "$SKILL_DIR/scripts/openapi-helper.py" search <keyword>

# Full schema for a specific operation
python3 "$SKILL_DIR/scripts/openapi-helper.py" operation <METHOD> <path>

# DTO/schema definition
python3 "$SKILL_DIR/scripts/openapi-helper.py" schema <SchemaName>
```

## Help center lookup

The API exposes Leadtime's help center. Use proactively when you need to understand a Leadtime feature:

```bash
# Search articles
bash "$SKILL_DIR/scripts/leadtime-api.sh" GET "/help-center/search?searchTerm=task%20types" --raw

# Fetch full article
bash "$SKILL_DIR/scripts/leadtime-api.sh" GET "/help-center/article?articleId=ID&helpcenterCollectionId=CID&language=en" --raw
```

## Embedded images

Task descriptions and comments may contain HTML with embedded files:

```html
<div data-type="appImage" fileId="FILE_ID" filename="image.png" width="500">image.png</div>
```

To inspect: parse `fileId` from HTML, then fetch `https://leadtime.app/api/files/public/{fileId}`.

## Pass/fail reporting

When exercising multiple endpoints, end with a summary:

```
## Results

| # | Endpoint | Method | Status | Notes |
|---|----------|--------|--------|-------|
| 1 | /tasks/947 | GET | PASS | Returned task data |
| 2 | /tasks/947 | PATCH | PASS | Title updated |

**Overall: PASS** (2/2)
```
