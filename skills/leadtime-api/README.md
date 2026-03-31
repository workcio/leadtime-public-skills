# leadtime-api

An agent skill for interacting with the [Leadtime](https://leadtime.app) Public API. Teaches AI agents (Cursor, Claude, Codex, etc.) how to discover endpoints, authenticate, and make API calls against your Leadtime workspace.

## Installation

```bash
npx skills install workcio/leadtime-public-skills/skills/leadtime-api
```

Or clone manually:

```bash
git clone https://github.com/workcio/leadtime-public-skills.git
# Copy or symlink skills/leadtime-api/ into your agent's skills directory
```

## What it does

- **API key management** — stores credentials in `.leadtime-api-key.json` with support for multiple workspaces
- **OpenAPI spec caching** — fetches the live spec from `leadtime.app` and caches it per session in `/tmp`
- **Endpoint discovery** — search and inspect any endpoint via the `openapi-helper.py` script
- **Authenticated requests** — `leadtime-api.sh` wrapper handles auth, JSON formatting, and profile selection
- **Multi-workspace** — switch between Leadtime workspaces with named profiles

## Prerequisites

- **Python 3.6+** (for OpenAPI helper and JSON parsing)
- **curl** (for API requests)
- **bash** (for the wrapper script)
- A **Leadtime account** with a Personal Access Token (PAT)

## Quick start

1. **Get an API key** — go to [leadtime.app/leadtime/profile/api-tokens](https://leadtime.app/leadtime/profile/api-tokens) and create a Personal Access Token

2. **Let the agent handle setup** — when you ask the agent to do something with Leadtime, it will:
   - Check for existing credentials in `./.leadtime-api-key.json` or `~/.leadtime-api-key.json`
   - Prompt you for a key if none is found
   - Validate the key against the API
   - Optionally save it for future sessions

3. **Use it** — ask your agent things like:
   - "List my Leadtime projects"
   - "Check task 947 on Leadtime"
   - "Create a new task in project X"
   - "Update the status of task 123"

## File structure

```
leadtime-api/
├── SKILL.md                          # Agent instructions
├── README.md                         # This file
└── scripts/
    ├── leadtime-api.sh               # API request wrapper
    └── openapi-helper.py             # OpenAPI spec query tool
```

## Credential storage

Credentials are stored in `.leadtime-api-key.json` (never committed to repos):

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
      "workspaceId": "...",
      "domain": "acme",
      "addedAt": "2026-04-01T12:00:00Z"
    }
  ]
}
```

The agent searches for this file in:
1. Current working directory (`./.leadtime-api-key.json`)
2. Home directory (`~/.leadtime-api-key.json`)

## Scripts

### `leadtime-api.sh`

Generic API wrapper with auth, profile selection, and JSON pretty-printing.

```bash
# Get a task
bash scripts/leadtime-api.sh GET /tasks/947

# Search tasks
bash scripts/leadtime-api.sh GET /tasks/grid -q "page=1&pageSize=10"

# Update a task
bash scripts/leadtime-api.sh PATCH /tasks/947 -d '{"title":"Updated title"}'

# Use a specific profile
bash scripts/leadtime-api.sh GET /workspace/details --profile 1
```

### `openapi-helper.py`

Search and inspect the OpenAPI specification.

```bash
# Find endpoints related to "task"
python3 scripts/openapi-helper.py search task

# Get full details for an endpoint
python3 scripts/openapi-helper.py operation GET /tasks/{identifier}

# Inspect a DTO schema
python3 scripts/openapi-helper.py schema CreateTaskDto
```

## Security

- API keys are stored locally in `.leadtime-api-key.json` with `chmod 600`
- Keys are never logged, printed back to the user, or committed to repositories
- Add `.leadtime-api-key.json` to your `.gitignore`

## License

MIT
