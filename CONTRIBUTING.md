# Contributing to netsight-ops

## Setting up

```sh
git clone https://github.com/magicboxlab-ai/netsight-ops.git
cd netsight-ops
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'   # installs netsight-sdk transitively
pytest tests/             # all tests should pass on a clean checkout
```

Python 3.14 or later is required. The SDK (`netsight-sdk>=1.0.0,<2.0.0`) is
pulled in automatically; if you need to work against a local SDK checkout,
install it in editable mode before installing ops:

```sh
pip install -e /path/to/netsight-sdk
pip install -e '.[dev]'
```

## Project structure

```
netsight_ops/       Package root
  registry.py       Service protocol, ServiceBase, ServiceRegistry, ServiceConfig
  loader.py         Entry-point discovery (netsight_ops.services group)
  exceptions.py     Exception hierarchy
  cli.py            netsight-ops CLI
  api/              Built-in HTTP API service (FastAPI + GraphQL + auth)
  mcp/              Built-in runtime MCP service (stdio transport)
  testing/          Fixtures and helpers for service authors
tests/              pytest test suite
pyproject.toml      Build metadata, dependencies, entry-point declarations
CHANGELOG.md        User-facing changelog (keep this updated)
```

## Adding a new built-in service

1. Create a sub-package under `netsight_ops/`:

   ```
   netsight_ops/my_service/
       __init__.py     # exports MyService and register()
       server.py       # implementation
   ```

2. Implement the `Service` protocol (or subclass `ServiceBase`):

   ```python
   from netsight_ops.registry import ServiceBase, ServiceConfig

   class MyService(ServiceBase):
       _name = "my-service"

       def start(self, *, config: ServiceConfig) -> None:
           super().start(config=config)
           # ... bind and listen

       def stop(self) -> None:
           super().stop()
           # ... teardown
   ```

3. Expose a `register()` function that the loader will call:

   ```python
   def register(registry) -> None:
       from netsight_ops.registry import ServiceInfo
       registry.register(ServiceInfo(
           name="my-service",
           display_name="My Service",
           description="One-line summary",
           version="0.1.0",
           distribution="netsight-ops",
           factory=MyService,
           cli_verb="my-service",
           transport="tcp",
       ))
   ```

4. Declare the entry point in `pyproject.toml`:

   ```toml
   [project.entry-points."netsight_ops.services"]
   my-service = "netsight_ops.my_service:register"
   ```

5. Add tests in `tests/` and update `CHANGELOG.md`.

## Adding a third-party service

Third-party services live in a separate repository and package. The pattern is:

1. Create a new Python package (e.g. `my-netsight-service`).
2. Implement the `Service` protocol using `netsight-ops` as a dependency.
3. Declare `netsight_ops.services` entry point in your `pyproject.toml`:

   ```toml
   [project.entry-points."netsight_ops.services"]
   my-service = "my_netsight_service:register"
   ```

4. Set `declared_service_api` in your `ServiceInfo` to match the
   `SERVICE_API_VERSION` of the `netsight-ops` release you target. The loader
   rejects services whose `declared_service_api` does not match the running
   platform version.

5. Optionally constrain compatible versions with `min_ops_version` and
   `min_sdk_version` (PEP 440 specifier strings) in your `ServiceInfo`.

Once installed in the same environment as `netsight-ops`, the service is
auto-discovered at startup via `service_registry.ensure_loaded()`.

## PR checklist

- [ ] All existing tests pass: `pytest tests/`
- [ ] New behaviour is covered by tests in `tests/`
- [ ] Code passes the linter: `ruff check netsight_ops/ tests/`
- [ ] Type annotations are consistent: `mypy netsight_ops/`
- [ ] Commit messages follow the conventional commit format:
      `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`
- [ ] `CHANGELOG.md` has an entry under `[Unreleased]` for every
      user-facing change (new feature, bug fix, or breaking change)
- [ ] Breaking changes to the public API or `SERVICE_API_VERSION` are
      called out explicitly in the PR description

## Code of Conduct

This project follows the
[Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).
By contributing you agree to abide by its terms.
