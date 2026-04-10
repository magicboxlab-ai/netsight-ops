# Semantic Versioning — netsight-ops

netsight-ops follows [Semantic Versioning 2.0.0](https://semver.org/).

## Public API surface

The following symbols form the versioned public API. A breaking change to any
of them requires a MAJOR version bump.

| Symbol | Module |
|---|---|
| `__version__` | `netsight_ops` |
| `SERVICE_API_VERSION` | `netsight_ops` |
| `Service` | `netsight_ops` / `netsight_ops.registry` |
| `ServiceBase` | `netsight_ops` / `netsight_ops.registry` |
| `ServiceInfo` | `netsight_ops` / `netsight_ops.registry` |
| `ServiceRegistry` | `netsight_ops` / `netsight_ops.registry` |
| `ServiceConfig` | `netsight_ops` / `netsight_ops.registry` |
| `service_registry` | `netsight_ops` / `netsight_ops.registry` |
| `create_fastapi_app` | `netsight_ops.api` |
| `HTTPAPIService` | `netsight_ops.api` |
| `MCPOpsService` | `netsight_ops.mcp` |
| `create_mcp_server` | `netsight_ops.mcp` |
| `netsight_ops.testing.*` | `netsight_ops.testing` |
| `netsight_ops.exceptions.*` | `netsight_ops.exceptions` |

Everything under `netsight_ops._*` or any sub-module not listed above is
**internal** and may change without notice in any release.

## Bump rules

| Change | Bump | Examples |
|---|---|---|
| Remove or rename a public symbol | MAJOR | Delete `ServiceBase`; rename `ServiceConfig.host` |
| Increment `SERVICE_API_VERSION` | MAJOR | Causes all third-party services to be rejected until updated |
| Incompatible change to `Service` protocol | MAJOR | Add a required method to the protocol |
| New public symbol (backward-compatible) | MINOR | Add `ServiceBase.restart()`; add a new exception class |
| New optional field on `ServiceInfo` | MINOR | Add `metadata` dict (already defaults to `{}`) |
| Bug fix with no API change | PATCH | Fix loader handling of a malformed entry point |
| Docs, tests, tooling only | PATCH | Update CHANGELOG, fix a typo in a docstring |
| Dependency bounds update (non-breaking) | PATCH or MINOR | Widen `fastapi` upper bound |

## SERVICE_API_VERSION semantics

`SERVICE_API_VERSION` is an integer counter that expresses the contract between
the loader and third-party services.

- Every `ServiceInfo` must declare `declared_service_api` equal to the
  `SERVICE_API_VERSION` of the `netsight-ops` release it targets.
- The loader (`netsight_ops.loader`) rejects any service whose
  `declared_service_api` does not exactly match the running platform value.
- Incrementing `SERVICE_API_VERSION` is therefore a **breaking change** for
  all existing third-party service packages and always requires a MAJOR
  version bump of `netsight-ops`.
- The current value is `1`.
