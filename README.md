# leadtime-public-skills

Public, shareable agent skills for [Leadtime](https://leadtime.app) — usable with Cursor, Claude, Codex, and similar AI coding tools.

## Available skills

| Skill | Description |
|-------|-------------|
| [leadtime-api](skills/leadtime-api/) | Interact with the Leadtime Public API — discover endpoints, authenticate, manage tasks, projects, and more |

## Installation

For most agents (Cursor, Codex, CLI workflows), use **`npx skills`** below. **Cowork / Claude Desktop** is the exception: it needs a zip upload instead.

### CLI (`npx skills`) — default

Install a specific skill:

```bash
npx skills add workcio/leadtime-public-skills --skill leadtime-api
```

List skills in this repo:

```bash
npx skills add workcio/leadtime-public-skills --list
```

### Cowork / Claude Desktop

Cowork installs skills from a **zip** file, not from `npx skills`.

1. **Download the skill archive** (always points at `main`):

   **[leadtime-api.zip](https://github.com/workcio/leadtime-public-skills/raw/main/skills/leadtime-api.zip)**

2. In the app, open **Customize** in the sidebar, then the **Skills** tab.

3. Click the **+** button at the top of the skills list.

4. Choose **Create skill** → **Upload a skill**.

5. Select the downloaded `leadtime-api.zip` file.

After upload, the **leadtime-api** skill appears in your personal skills and is available in conversations.

### Manual (clone)

Clone the repo and copy or symlink the `skills/leadtime-api/` folder into your agent’s skills directory.

## Zip packaging

The Cowork-ready artifact is committed at `skills/leadtime-api.zip` (same file as the download link above).

Build it manually with:

```bash
python3 scripts/build-skill-zips.py
```

A reusable pre-commit hook lives at `.githooks/pre-commit`. To enable it locally:

```bash
ln -sf ../../.githooks/pre-commit .git/hooks/pre-commit
chmod +x .githooks/pre-commit .git/hooks/pre-commit
```

When enabled, every commit regenerates the zip artifact(s) under `skills/*.zip` and stages them automatically.

## Contributing

PRs welcome. Each skill lives in its own folder under `skills/` and must include a `SKILL.md` and `README.md`.

## License

MIT
