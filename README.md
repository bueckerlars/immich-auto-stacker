# immich-auto-stacker

Periodic automation for [Immich](https://immich.app/) that groups related assets into stacks using configurable filename rules. It is inspired by [mattdavis90/immich-stacker](https://github.com/mattdavis90/immich-stacker) but runs as a long-lived process (or single run) in Python, with optional continuous scanning.

The Immich web UI supports manual stacking; this tool applies the same idea at scale via the [Immich API](https://api.immich.app/introduction).

## Features

- Match assets with two regular expressions: which files participate (`IMMICH_MATCH`) and which file becomes the stack parent (`IMMICH_PARENT`).
- Paginated metadata search, optional time filter (`IMMICH_NEWER_THAN`), and optional grouping by file creation time (`IMMICH_COMPARE_CREATED`).
- Skips parents that already belong to a non-empty stack.
- Dry-run and read-only modes for safe testing.
- TLS verification can be disabled for private certificates (use with care).
- Configurable scan interval or one-shot mode for cron-style deployments.

## Requirements

- Python 3.13 or later
- [uv](https://docs.astral.sh/uv/) (recommended)
- An Immich API key with at least `asset.read` and `stack.*` (see [Immich API keys](https://immich.app/docs/features/command-line-interface#api-keys))

HTTP client models and types are provided by [immich-sdk](https://github.com/bueckerlars/immich-sdk) (installed from Git as specified in `pyproject.toml`).

## Installation

```bash
git clone https://github.com/bueckerlars/immich-auto-stacker.git
cd immich-auto-stacker
uv sync
```

For development (tests, linting, type checking, [Poe the Poet](https://github.com/nat-n/poethepoet) task runner):

```bash
uv sync --all-extras
```

## Configuration

All settings use the `IMMICH_` prefix and can be loaded from the environment or a `.env` file in the working directory.

### Required

| Variable         | Description                                                                                                                                                               |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `IMMICH_API_KEY` | API key sent as `x-api-key`.                                                                                                                                              |
| `IMMICH_MATCH`   | Regex applied to each asset `originalFileName`. Matching files are grouped by the filename with all regex matches removed (same idea as the Go reference implementation). |
| `IMMICH_PARENT`  | Regex: if it matches the filename, that asset is the stack parent for its group.                                                                                          |

You must set at least one of:

| Variable            | Description                                                                                                                                                                                                           |
| ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `IMMICH_SERVER_URL` | Server root URL, e.g. `https://photos.example.com` (validated as a URL).                                                                                                                                              |
| `IMMICH_ENDPOINT`   | Legacy alias: full URL including `/api` if you migrate from [immich-stacker](https://github.com/mattdavis90/immich-stacker). A trailing `/api` is stripped for the HTTP client, which expects paths under `/api/...`. |

### Optional

| Variable                 | Default | Description                                                                                                                       |
| ------------------------ | ------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `IMMICH_LOG_LEVEL`       | `INFO`  | Logging level.                                                                                                                    |
| `IMMICH_COMPARE_CREATED` | `false` | Append file creation time to the group key when filenames are not unique.                                                         |
| `IMMICH_NEWER_THAN`      | `0h`    | Only consider assets with `taken` time newer than now minus this duration. Format: `<number>s`, `m`, or `h` (e.g. `24h`, `300s`). |
| `IMMICH_SCAN_INTERVAL`   | `1h`    | Delay between scans when not in once mode. Same duration format as `NEWER_THAN`.                                                  |
| `IMMICH_ONCE`            | `false` | If `true`, run a single scan and exit (suitable for external schedulers).                                                         |
| `IMMICH_READ_ONLY`       | `false` | Do not call stack creation; only log what would happen.                                                                           |
| `IMMICH_DRY_RUN`         | `false` | Same as read-only for stack writes; logs intended stacks.                                                                         |
| `IMMICH_INSECURE_TLS`    | `false` | Disable TLS certificate verification (emits a warning at startup).                                                                |

## Usage

```bash
export IMMICH_SERVER_URL=https://immich.example.com
export IMMICH_API_KEY=your-api-key
export IMMICH_MATCH='\.(JPG|RW2)$'
export IMMICH_PARENT='\.JPG$'
uv run python -m immich_auto_stacker
```

Or use the console script after `uv sync`:

```bash
uv run immich-auto-stacker
```

With dev dependencies installed, you can start the same entry point via [poethepoet](https://github.com/nat-n/poethepoet):

```bash
uv run poe run
```

The process listens for `SIGTERM` and `SIGINT` so it stops cleanly under Docker and process managers.

## Example rules

These mirror the examples in [immich-stacker](https://github.com/mattdavis90/immich-stacker):

**RAW + JPEG (JPEG as parent)**

```text
IMMICH_MATCH=\.(JPG|RW2)$
IMMICH_PARENT=\.JPG$
```

**Burst sequences (cover as parent)**

```text
IMMICH_MATCH=BURST[0-9]{3}(_COVER)?\.jpg$
IMMICH_PARENT=_COVER\.jpg$
```

Regex escaping in shell or Docker Compose may require extra backslashes; using a `.env` file often avoids mistakes.

## Docker

Build:

```bash
docker build -t immich-auto-stacker .
```

Run (example):

```bash
docker run --rm \
  -e IMMICH_SERVER_URL=https://immich.example.com \
  -e IMMICH_API_KEY=your-api-key \
  -e IMMICH_MATCH='\.(JPG|RW2)$' \
  -e IMMICH_PARENT='\.JPG$' \
  immich-auto-stacker
```

Or use `--env-file` with a file containing the variables above.

### Docker Compose

An example [docker-compose.example.yml](docker-compose.example.yml) builds the image from this repository and sets **all configuration in the compose file** (`environment:`), including required variables (`IMMICH_SERVER_URL`, `IMMICH_API_KEY`, `IMMICH_MATCH`, `IMMICH_PARENT`) and optional ones with defaults. You do **not** need a `.env` file for Compose.

1. Copy the example and edit placeholders (especially URL, API key, and regexes if your filenames differ):

   ```bash
   cp docker-compose.example.yml docker-compose.yml
   # edit docker-compose.yml
   ```

2. Build and start (detached):

   ```bash
   docker compose -f docker-compose.yml up -d --build
   ```

3. Follow logs:

   ```bash
   docker compose logs -f immich-auto-stacker
   ```

4. Stop and remove the container:

   ```bash
   docker compose down
   ```

The service uses `restart: unless-stopped` so it keeps running between host reboots (when Docker starts). `init: true` improves signal handling for graceful shutdown (`docker compose stop`).

**Secrets:** Avoid committing a `docker-compose.yml` that contains a real API key. For production, use [Docker secrets](https://docs.docker.com/compose/how-tos/use-secrets/), or keep `IMMICH_API_KEY: ${IMMICH_API_KEY}` and export the variable in the shell before `docker compose up`.

For local runs without Compose, a `.env` file next to the app is still supported by pydantic-settings; see [.env.example](.env.example) as a template.

For a **single run per container start**, set `IMMICH_ONCE: "true"` under `environment:` and consider `restart: "no"` in your compose file.

## Development

Install dev dependencies, then register hooks (including the **commit-msg** hook for [Conventional Commits](https://www.conventionalcommits.org/)):

```bash
uv sync --all-extras
uv run pre-commit install
```

After `install`, commit messages are checked against the Conventional Commits format (via [conventional-pre-commit](https://github.com/compilerla/conventional-pre-commit)). Example: `feat: add burst stacking rule`.

Run all checks on tracked files:

```bash
uv run pre-commit run --all-files
```

Useful shortcuts (with dev extras):

| Command | Purpose |
|--------|---------|
| `uv run ruff check src tests` | Lint |
| `uv run ruff format src tests` | Format |
| `uv run pyright src/immich_auto_stacker` | Type check (strict) |
| `uv run pytest` | Tests |
| `uv run poe lint` / `poe format` / `poe typecheck` | Same via [poethepoet](https://github.com/nat-n/poethepoet) |

Pre-commit runs file hygiene checks, **Ruff** (lint + format), **toml-sort**, **codespell**, **pyright**, and the hooks above. Private keys and accidental submodules are rejected.

The codebase targets **pyright strict** mode.

## License

This project is licensed under the [MIT License](LICENSE).
