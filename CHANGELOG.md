# Changelog

All notable changes to netsight-ops are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] — 2026-04-10

### Added

- **Service platform.** ``Service`` protocol, ``ServiceBase`` convenience
  class, ``ServiceInfo`` frozen dataclass, ``ServiceRegistry`` singleton,
  ``ServiceConfig`` configuration.
- **Entry-point discovery.** ``netsight_ops.services`` entry-point group.
  Services register themselves via a ``register()`` callable; the
  ``ServiceRegistry.ensure_loaded()`` method discovers them at startup.
- **Compatibility checks.** ``SERVICE_API_VERSION = 1`` integer +
  ``min_ops_version`` / ``min_sdk_version`` PEP 440 specifiers on
  ``ServiceInfo``. Checked at load time; incompatible services are
  unregistered and recorded in ``load_errors()``.
- **Built-in services:**
  - ``api`` — FastAPI + GraphQL + JWT/OAuth/APIKey auth (migrated from
    the former ``netsight.api``).
  - ``mcp`` — Runtime MCP stdio server exposing live device operations
    (migrated from the former ``netsight.mcp``).
- **CLI.** ``netsight-ops list``, ``netsight-ops serve <service>``.
  Rich-table output.
- **Testing utilities.** ``netsight_ops.testing`` module with
  ``make_test_registry()``, ``assert_valid_service()``,
  ``run_service_briefly()``.
- **Library surface.** ``create_fastapi_app()``, ``HTTPAPIService``,
  ``MCPOpsService``, ``create_mcp_server()`` for embedding.

### Dependencies

- ``netsight-sdk>=1.0.0,<2.0.0`` (hard dependency)
- ``fastapi>=0.100.0``
- ``strawberry-graphql>=0.200.0``
- ``python-jose[cryptography]>=3.3.0``
- ``passlib[bcrypt]>=1.7.4``
- ``uvicorn>=0.23.0``
- ``websockets>=11.0``
