# netsight-ops

**netsight-ops** is the runtime service platform for NetSight. It ships the HTTP
API server (FastAPI + GraphQL) and the runtime MCP operations server as
installable services on top of the
[netsight-sdk](https://github.com/magicboxlab-ai/netsight-sdk) core library.

## Install

```sh
# Installs netsight-ops + pulls netsight-sdk automatically
pip install netsight-ops
```

## Quick start

```sh
# List registered services
netsight-ops list

# Start the HTTP API
netsight-ops serve api --port 8000

# Start the runtime MCP server (stdio transport)
netsight-ops serve mcp
```

## Architecture

netsight-ops defines a `Service` protocol and a `ServiceRegistry` that
discovers installed services via the `netsight_ops.services` entry-point
group. Third-party services (webhooks, metrics exporters, syslog
collectors, etc.) register themselves as entry points and are
auto-discovered at startup.

## For developers

```sh
git clone https://github.com/magicboxlab-ai/netsight-ops.git
cd netsight-ops
python3.14 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest
```

See [SEMVER.md](SEMVER.md) for the versioning policy.

## License

MIT — see [LICENSE](LICENSE).
