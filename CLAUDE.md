# netsight-ops — Project Memory for Claude Code

This is **netsight-ops** — the runtime service platform for NetSight. It ships
two built-in services (`api`: HTTP API Server, `mcp`: Runtime MCP Server) and
discovers third-party services via the `netsight_ops.services` entry-point
group. It depends on `netsight-sdk>=1.0.0,<2.0.0` for all device-query logic.

## What this repo is

`netsight-ops` is the production runtime layer on top of the NetSight SDK. Its
responsibilities are:

- Expose NetSight device operations over HTTP (FastAPI + GraphQL) and MCP
  (stdio transport).
- Provide a `Service` protocol and `ServiceRegistry` so third parties can
  package and plug in additional runtime services.
- Ship a `netsight-ops` CLI (`list`, `serve <name>`, `status`) that starts
  any registered service.

The SDK (`netsight-sdk`) handles device connection, parsing, and the allowlist
gate. Ops wraps it — it never reimplements those concerns.

## Project layout

```
netsight_ops/
├── __init__.py          # __version__, SERVICE_API_VERSION, re-exports
├── registry.py          # Service (Protocol), ServiceBase, ServiceInfo,
│                        #   ServiceConfig, ServiceRegistry, service_registry
├── loader.py            # entry-point discovery (netsight_ops.services group)
├── exceptions.py        # ServiceRegistrationError, ServiceConflictError,
│                        #   ServiceIncompatibleError
├── cli.py               # netsight-ops CLI (list / serve / status)
├── api/                 # Built-in HTTP API service
│   ├── __init__.py      # create_fastapi_app(), HTTPAPIService, register()
│   ├── server.py        # create_app() — assembles the FastAPI app
│   ├── auth/            # APIKeyBackend, JWTBackend, OAuthBackend, AuthContext
│   ├── routes/          # auth_router, devices_router, plugins_router, schema_router
│   ├── graphql/         # Strawberry schema
│   ├── models/          # Pydantic response models
│   └── websocket/       # WebSocket handlers
├── mcp/                 # Built-in runtime MCP service
│   ├── __init__.py      # MCPOpsService, create_mcp_server(), run_stdio(), register()
│   ├── server.py        # NetSightMCPServer
│   └── transport.py     # run_stdio()
└── testing/             # Fixtures and helpers for service authors
tests/                   # pytest test suite (NOT UNITTEST/ — that is the SDK's convention)
pyproject.toml
```

## Key types

| Symbol | Where defined | What it is |
|---|---|---|
| `Service` | `netsight_ops.registry` | `@runtime_checkable Protocol` every service implements |
| `ServiceBase` | `netsight_ops.registry` | Optional convenience base class with sensible defaults |
| `ServiceInfo` | `netsight_ops.registry` | Frozen dataclass — metadata for one registered service |
| `ServiceConfig` | `netsight_ops.registry` | Mutable dataclass passed to `Service.start()` |
| `ServiceRegistry` | `netsight_ops.registry` | Central registry; mirrors SDK's `PackRegistry` shape |
| `service_registry` | `netsight_ops.registry` | Module-level singleton; the live registry at runtime |
| `SERVICE_API_VERSION` | `netsight_ops` | Integer; loader checks each service's `declared_service_api` matches |
| `HTTPAPIService` | `netsight_ops.api` | Built-in HTTP service (FastAPI + GraphQL) |
| `MCPOpsService` | `netsight_ops.mcp` | Built-in runtime MCP service (stdio) |

## Service protocol

```python
class Service(Protocol):
    @property
    def name(self) -> str: ...
    def start(self, *, config: ServiceConfig) -> None: ...
    def stop(self) -> None: ...
    def health(self) -> dict: ...
```

`start()` and `stop()` must both be idempotent. `health()` returns a shallow
dict for readiness probes.

## Entry-point group

Services register via `pyproject.toml`:

```toml
[project.entry-points."netsight_ops.services"]
my-service = "my_package:register"
```

The `register` callable receives the `ServiceRegistry` singleton and calls
`registry.register(ServiceInfo(...))`. The loader (called by
`service_registry.ensure_loaded()`) validates `declared_service_api`,
`min_ops_version`, and `min_sdk_version` before accepting the registration.

## Cross-repo relationship

| Repo | PyPI name | Role |
|---|---|---|
| `github.com/magicboxlab-ai/netsight-sdk` | `netsight-sdk` | Core library: device connection, parsing, allowlist gate, dev MCP server |
| `github.com/magicboxlab-ai/netsight-ops` | `netsight-ops` | Runtime platform: HTTP API, runtime MCP, service registry |
| `github.com/magicboxlab-ai/netsight-packs-paloalto` | per-pack | Vendor packs; install into the SDK, not ops |

Key distinctions:

- The **dev MCP server** (`netsight.mcp_dev`) lives in the SDK. It exposes
  codebase-introspection tools for AI-assisted development. Do not confuse it
  with the runtime MCP server here.
- The **runtime MCP server** (`netsight_ops.mcp`) lives here. It exposes live
  device operations to AI agents.
- Ops imports from the SDK's public API only. It never touches SDK internals.
- Vendor packs (`netsight.packs` entry-point group) are an SDK concern.
  Ops consumes them indirectly through the SDK device-query API.

## Development setup

```sh
git clone https://github.com/magicboxlab-ai/netsight-ops.git
cd netsight-ops
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'   # pulls netsight-sdk transitively
pytest tests/
```

`netsight-sdk` must be installed (transitively via the dependency or
separately as an editable install if you need a local SDK checkout).

## Important rules

- **Logging**: use stdlib `logging` with a module-level
  `logger = logging.getLogger(__name__)`. Do NOT use OSLog — that is a
  Swift/Apple-platform convention and is not importable in Python.
- **Tests**: live in `tests/` (not `UNITTEST/` — that is the SDK's
  convention for its own test suite).
- **Plans**: save implementation plans in `TASKS/` (create it if needed);
  move to `TASKS/DONE/` when fully implemented.
- **Commit style**: conventional commits (`feat:`, `fix:`, `refactor:`, etc.).
  Update `CHANGELOG.md` with every user-facing change.
- **Security**: run `ruff check` before committing. For dependency additions,
  verify the package is safe before adding to `pyproject.toml`.
- **Service API contract**: incrementing `SERVICE_API_VERSION` in
  `netsight_ops/__init__.py` is a breaking change — it will reject all
  third-party services that have not been updated to match.
