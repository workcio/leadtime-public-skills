# leadtime-public-skills

Public, shareable agent skills for [Leadtime](https://leadtime.app) — usable with Cursor, Claude, Codex, and similar AI coding tools.

## Available skills

| Skill | Description |
|-------|-------------|
| [leadtime-api](skills/leadtime-api/) | Interact with the Leadtime Public API — discover endpoints, authenticate, manage tasks, projects, and more |

## Installation

Install a specific skill:

```bash
npx skills add workcio/leadtime-public-skills --skill leadtime-api
```

List skills in this repo:

```bash
npx skills add workcio/leadtime-public-skills --list
```

Or clone the repo and copy/symlink the skill folder into your agent's skills directory.

## Contributing

PRs welcome. Each skill lives in its own folder under `skills/` and must include a `SKILL.md` and `README.md`.

## License

MIT
