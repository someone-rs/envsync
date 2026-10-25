# envsync

**Keep `.env` in sync with `.env.example` — before the missing variable breaks production.**

Every project has a `.env.example` that drifts. Someone adds `STRIPE_WEBHOOK_SECRET`
to the example, nobody adds it to their local `.env`, and the app crashes at
runtime with a cryptic error three deploys later. `envsync` catches that drift
in one command — and in CI, where it belongs.

## Install

```bash
pip install git+https://github.com/someone-rs/envsync.git
```

Python 3.9+, no dependencies.

## Quickstart

```bash
$ envsync
example: .env.example (4 keys)
env:     .env (3 keys)

  MISSING    STRIPE_WEBHOOK_SECRET — present in .env.example, absent from .env
  EMPTY      REDIS_URL — present in .env but set to an empty value

1 missing, 2 findings total.
```

Fix it in place:

```bash
$ envsync --fix
envsync: added 1 missing key(s) to .env
```

Then fill in the values — `envsync` never invents secrets for you.

## What it checks

| Finding | Meaning | Fails by default? |
| --- | --- | --- |
| `missing` | Key in `.env.example`, absent from `.env` | ✅ Yes |
| `empty` | Key present but set to nothing | No (yes with `--strict`) |
| `extra` | Key in `.env`, absent from `.env.example` | No (yes with `--strict`) |
| `duplicate` | Same key defined twice in `.env` | ✅ Yes |
| `malformed` | A line that isn't `KEY=value` | ✅ Yes |

The parser understands `export KEY=value`, single/double quotes (a `#` inside
quotes is *not* a comment), inline comments on unquoted values, and blank lines.

## Options

```
envsync [--example FILE] [--env FILE] [--json] [--strict]
        [--ignore KEY,KEY] [--fix]
```

- `--json` — machine-readable report for other tooling.
- `--strict` — also fail on extra keys and empty values.
- `--ignore DATABASE_URL,DEBUG` — skip keys that are intentionally optional.
- `--fix` — append missing keys as `KEY=` to the env file.

## Exit codes (CI-friendly)

| Code | Meaning |
| --- | --- |
| `0` | In sync |
| `1` | Findings that fail the check |
| `2` | Error (e.g. file not found) |

```yaml
# GitHub Actions
- run: pip install git+https://github.com/someone-rs/envsync.git
- run: envsync --strict
```

## Real example

`.env.example`:

```dotenv
DATABASE_URL=postgres://localhost/app
REDIS_URL=redis://localhost:6379
STRIPE_WEBHOOK_SECRET=whsec_...
```

`envsync --json` on a `.env` missing the last key:

```json
{
  "example_keys": 3,
  "env_keys": 2,
  "findings": [
    {
      "kind": "missing",
      "key": "STRIPE_WEBHOOK_SECRET",
      "detail": "present in .env.example, absent from .env"
    }
  ]
}
```

## License

MIT — see [LICENSE](LICENSE).
