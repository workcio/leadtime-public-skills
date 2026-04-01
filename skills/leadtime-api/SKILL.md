---
name: leadtime-api
description: Works with live Leadtime data through the production Public API on leadtime.app. Use when the user asks to check, create, update, or inspect tasks, projects, organizations, workspace data, or other Leadtime entities. Also use it to answer product questions about how Leadtime features work by querying the built-in help center before or alongside data/API calls. Handles API key storage, OpenAPI spec caching, and multi-workspace profiles. Triggers on "check task", "list projects", "create via Leadtime API", "update task in Leadtime", "query Leadtime", "how does Leadtime feature X work", or any request involving Leadtime production data.
---

# Leadtime Public API

**IMPORTANT: Verbosity Rule**
Do not narrate internal steps to the user (e.g., "Let me download the OpenAPI spec", "Let me search for the endpoint", "Let me check for API keys"). Perform these steps silently and only communicate the final result or ask for required input (like the API key).

Interact with the Leadtime production API at `https://leadtime.app/api/public`.

## Skill location

All scripts referenced below live relative to this skill's directory. Determine the skill root from the path of this `SKILL.md` file:

```bash
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." 2>/dev/null && pwd)"
# fallback: if running from SKILL.md context, the agent knows the install path
```

Helper scripts are in `$SKILL_DIR/scripts/`.

## Setup — API key

### 1. Check for credentials

Before prompting the user, silently check if `.leadtime-api-key.json` exists in the current working directory.

```bash
KEYFILE="./.leadtime-api-key.json"
if [[ -f "$KEYFILE" ]]; then
  # Use this keyfile
fi
```

If found, use it. You do not need to ask the user.

### 2. Ask for key (if none found)

If the file doesn't exist, prompt the user:

> I need a Leadtime API key to access your workspace.
> Create a Personal Access Token at: https://leadtime.app/leadtime/profile/api-tokens
> Then paste the key here.

### 3. Execute the user's request immediately

Once you receive the key, **do what the user originally asked for immediately** using the key in memory (e.g., pass it via `--api-key "$API_KEY"`). Do not ask to save the key yet.

### 4. Ask to save the key (after completing the task)

Only *after* you have successfully completed the user's original request and provided the answer, ask if they want to save the key for future use:

> Would you like me to save this API key in the current folder (`./.leadtime-api-key.json`) for future sessions?

### 5. Validate and save (if user says yes)

If the user agrees to save the key, fetch the account and workspace info to build the profile:

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

Build the profile entry and write it to `./.leadtime-api-key.json`:

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

```bash
chmod 600 ./.leadtime-api-key.json
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

If there is no keyfile (user chose not to save), pass the key:

```bash
bash "$SKILL_DIR/scripts/leadtime-api.sh" --api-key "$API_KEY" POST /tasks/943/comments -f /tmp/payload.json
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

Authentication (first match wins):
  --api-key KEY    Bearer token directly (no keyfile; use when user chose not to save)
  --keyfile PATH   Path to .leadtime-api-key.json (auto-detected if omitted)
  --profile INDEX  Profile index in the keyfile (default: 0; keyfile only)
  (env) LEADTIME_API_KEY   Fallback if no keyfile and no --api-key
  (env) LEADTIME_API_BASE  Optional API base when using --api-key or LEADTIME_API_KEY

Other options:
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
bash "$SKILL_DIR/scripts/leadtime-api.sh" --api-key "$API_KEY" GET /tasks/947
LEADTIME_API_KEY=lt_... bash "$SKILL_DIR/scripts/leadtime-api.sh" GET /workspace/details
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

The API exposes Leadtime's help center through two endpoints:

- `GET /help-center/search?searchTerm=...`
- `GET /help-center/article?articleId=...&helpcenterCollectionId=...&language=en|de`

Use these proactively in two situations:

1. **Answering user questions about Leadtime features** when the user asks what something is, how it works, what it is for, or how to use it.
2. **Teaching yourself the domain before calling other endpoints** when you need product context first. If a user asks about an unfamiliar Leadtime domain (for example Objects, project planning, task types, document templates, or workflows), search the help center first so you understand the business meaning before exploring or mutating API data.

Recommended workflow:

1. Search the help center for the feature/domain name.
2. Read the most relevant article(s).
3. Summarize the product meaning in plain language.
4. Only then discover and call data endpoints if the user also needs live workspace data or mutations.

This avoids guessing what a Leadtime concept means based only on endpoint names or database fields.

```bash
# Search articles
bash "$SKILL_DIR/scripts/leadtime-api.sh" GET "/help-center/search?searchTerm=task%20types" --raw

# Fetch full article
bash "$SKILL_DIR/scripts/leadtime-api.sh" GET "/help-center/article?articleId=ID&helpcenterCollectionId=CID&language=en" --raw
```

Example uses:

- User asks: "What are Objects in Leadtime?" -> search help center first, then answer from docs.
- User asks: "List our objects and explain what objects are used for." -> search help center first for product context, then call `/objects` or related endpoints for live data.
- You need to understand a Leadtime area before working with it -> read help-center docs first, then inspect OpenAPI operations for exact endpoints and schemas.

## Embedded images

Task descriptions and comments may contain HTML with embedded files:

```html
<div data-type="appImage" fileId="FILE_ID" filename="image.png" width="500">image.png</div>
```

To inspect: parse `fileId` from HTML, then fetch `https://leadtime.app/api/files/public/{fileId}`.

