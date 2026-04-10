"""Tests for netsight_ops.mcp.server — NetSightMCPServer.

Validates that the MCP server correctly exposes tools, resources, prompts,
and error guidance from the live netsight codebase without relying on static
documentation.
"""

from __future__ import annotations

import pytest

from netsight_ops.mcp.server import NetSightMCPServer


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def server() -> NetSightMCPServer:
    """Return a fresh NetSightMCPServer instance for each test."""
    return NetSightMCPServer()


# ---------------------------------------------------------------------------
# list_tools
# ---------------------------------------------------------------------------


def test_list_tools_returns_non_empty_list(server: NetSightMCPServer) -> None:
    """list_tools() returns a non-empty list of tool definitions."""
    tools = server.list_tools()
    assert isinstance(tools, list)
    assert len(tools) > 0


def test_list_tools_has_show_system_info(server: NetSightMCPServer) -> None:
    """list_tools() includes a tool named 'show_system_info'."""
    tools = server.list_tools()
    names = [t["name"] for t in tools]
    assert "show_system_info" in names


def test_list_tools_each_has_required_keys(server: NetSightMCPServer) -> None:
    """Every tool definition has 'name', 'description', and 'parameters' keys."""
    tools = server.list_tools()
    for tool in tools:
        assert "name" in tool, f"Tool missing 'name': {tool}"
        assert "description" in tool, f"Tool missing 'description': {tool}"
        assert "parameters" in tool, f"Tool missing 'parameters': {tool}"


def test_list_tools_no_keygen(server: NetSightMCPServer) -> None:
    """list_tools() does not expose the internal 'keygen' operation."""
    tools = server.list_tools()
    names = [t["name"] for t in tools]
    assert "keygen" not in names


def test_list_tools_parameters_is_json_schema_object(server: NetSightMCPServer) -> None:
    """Each tool's 'parameters' field is a JSON Schema object with 'type' == 'object'."""
    tools = server.list_tools()
    for tool in tools:
        params = tool["parameters"]
        assert isinstance(params, dict), f"Tool '{tool['name']}' parameters is not a dict"
        assert params.get("type") == "object", (
            f"Tool '{tool['name']}' parameters type is '{params.get('type')}', expected 'object'"
        )


def test_list_tools_no_duplicates(server: NetSightMCPServer) -> None:
    """list_tools() does not return duplicate tool names."""
    tools = server.list_tools()
    names = [t["name"] for t in tools]
    assert len(names) == len(set(names)), f"Duplicate tool names found: {names}"


# ---------------------------------------------------------------------------
# list_resources
# ---------------------------------------------------------------------------


def test_list_resources_returns_list(server: NetSightMCPServer) -> None:
    """list_resources() returns a list."""
    resources = server.list_resources()
    assert isinstance(resources, list)


def test_list_resources_has_patterns_uri(server: NetSightMCPServer) -> None:
    """list_resources() includes the 'netsight://patterns' URI."""
    resources = server.list_resources()
    uris = [r["uri"] for r in resources]
    assert "netsight://patterns" in uris


def test_list_resources_has_relations_uri(server: NetSightMCPServer) -> None:
    """list_resources() includes the 'netsight://relations' URI."""
    resources = server.list_resources()
    uris = [r["uri"] for r in resources]
    assert "netsight://relations" in uris


def test_list_resources_has_plugins_uri(server: NetSightMCPServer) -> None:
    """list_resources() includes the 'netsight://plugins' URI."""
    resources = server.list_resources()
    uris = [r["uri"] for r in resources]
    assert "netsight://plugins" in uris


def test_list_resources_has_error_uris(server: NetSightMCPServer) -> None:
    """list_resources() includes netsight://errors/{name} for each known error."""
    resources = server.list_resources()
    uris = {r["uri"] for r in resources}
    expected_errors = {
        "CommandDeniedError",
        "AuthenticationError",
        "DeviceConnectionError",
        "PluginNotFoundError",
        "RateLimitError",
        "ResponseSizeError",
    }
    for error_name in expected_errors:
        expected_uri = f"netsight://errors/{error_name}"
        assert expected_uri in uris, f"Missing error resource URI: {expected_uri}"


def test_list_resources_each_has_uri(server: NetSightMCPServer) -> None:
    """Every resource in list_resources() has a 'uri' key."""
    resources = server.list_resources()
    for resource in resources:
        assert "uri" in resource, f"Resource missing 'uri': {resource}"


# ---------------------------------------------------------------------------
# list_prompts
# ---------------------------------------------------------------------------


def test_list_prompts_returns_list(server: NetSightMCPServer) -> None:
    """list_prompts() returns a list."""
    prompts = server.list_prompts()
    assert isinstance(prompts, list)


def test_list_prompts_has_device_health_check(server: NetSightMCPServer) -> None:
    """list_prompts() includes the 'device-health-check' prompt."""
    prompts = server.list_prompts()
    names = [p["name"] for p in prompts]
    assert "device-health-check" in names


def test_list_prompts_each_has_required_keys(server: NetSightMCPServer) -> None:
    """Every prompt has 'name', 'description', and 'arguments' keys."""
    prompts = server.list_prompts()
    for prompt in prompts:
        assert "name" in prompt, f"Prompt missing 'name': {prompt}"
        assert "description" in prompt, f"Prompt missing 'description': {prompt}"
        assert "arguments" in prompt, f"Prompt missing 'arguments': {prompt}"


def test_list_prompts_each_has_device_argument(server: NetSightMCPServer) -> None:
    """Every prompt's arguments list contains a required 'device' argument."""
    prompts = server.list_prompts()
    for prompt in prompts:
        args = prompt["arguments"]
        device_args = [a for a in args if a.get("name") == "device"]
        assert len(device_args) == 1, (
            f"Prompt '{prompt['name']}' missing required 'device' argument"
        )
        assert device_args[0].get("required") is True, (
            f"Prompt '{prompt['name']}' device argument is not required"
        )


# ---------------------------------------------------------------------------
# get_resource — patterns
# ---------------------------------------------------------------------------


def test_get_resource_patterns_returns_list(server: NetSightMCPServer) -> None:
    """get_resource('netsight://patterns') returns a list."""
    result = server.get_resource("netsight://patterns")
    assert isinstance(result, list)


def test_get_resource_patterns_has_at_least_four_items(server: NetSightMCPServer) -> None:
    """get_resource('netsight://patterns') returns at least 4 items."""
    result = server.get_resource("netsight://patterns")
    assert len(result) >= 4


def test_get_resource_patterns_each_has_steps(server: NetSightMCPServer) -> None:
    """Every pattern returned has a 'steps' key."""
    result = server.get_resource("netsight://patterns")
    for pattern in result:
        assert "steps" in pattern, f"Pattern missing 'steps': {pattern}"


# ---------------------------------------------------------------------------
# get_resource — relations
# ---------------------------------------------------------------------------


def test_get_resource_relations_returns_list(server: NetSightMCPServer) -> None:
    """get_resource('netsight://relations') returns a list."""
    result = server.get_resource("netsight://relations")
    assert isinstance(result, list)


def test_get_resource_relations_has_at_least_four_items(server: NetSightMCPServer) -> None:
    """get_resource('netsight://relations') returns at least 4 items."""
    result = server.get_resource("netsight://relations")
    assert len(result) >= 4


def test_get_resource_relations_each_has_source_and_target(server: NetSightMCPServer) -> None:
    """Every relation returned has 'source' and 'target' keys."""
    result = server.get_resource("netsight://relations")
    for rel in result:
        assert "source" in rel, f"Relation missing 'source': {rel}"
        assert "target" in rel, f"Relation missing 'target': {rel}"


# ---------------------------------------------------------------------------
# get_resource — plugins
# ---------------------------------------------------------------------------


def test_get_resource_plugins_returns_list(server: NetSightMCPServer) -> None:
    """get_resource('netsight://plugins') returns a list."""
    result = server.get_resource("netsight://plugins")
    assert isinstance(result, list)


def test_get_resource_plugins_includes_paloalto_pack(server: NetSightMCPServer) -> None:
    """get_resource('netsight://plugins') includes the paloalto-firewall-xml pack."""
    result = server.get_resource("netsight://plugins")
    names = [p.get("name") for p in result]
    assert "paloalto-firewall-xml" in names


def test_get_resource_plugins_each_has_ops(server: NetSightMCPServer) -> None:
    """Every plugin entry has an 'operations' key."""
    result = server.get_resource("netsight://plugins")
    for plugin in result:
        assert "operations" in plugin, f"Plugin missing 'operations': {plugin}"


# ---------------------------------------------------------------------------
# get_resource — errors
# ---------------------------------------------------------------------------


def test_get_resource_error_command_denied_has_name_and_guidance(
    server: NetSightMCPServer,
) -> None:
    """get_resource('netsight://errors/CommandDeniedError') has 'name' and 'guidance' keys."""
    result = server.get_resource("netsight://errors/CommandDeniedError")
    assert isinstance(result, dict)
    assert "name" in result, f"Error resource missing 'name': {result}"
    assert "guidance" in result, f"Error resource missing 'guidance': {result}"


def test_get_resource_error_authentication_error(server: NetSightMCPServer) -> None:
    """get_resource('netsight://errors/AuthenticationError') has correct name."""
    result = server.get_resource("netsight://errors/AuthenticationError")
    assert result.get("name") == "AuthenticationError"


def test_get_resource_error_device_connection_error(server: NetSightMCPServer) -> None:
    """get_resource('netsight://errors/DeviceConnectionError') has name and guidance."""
    result = server.get_resource("netsight://errors/DeviceConnectionError")
    assert "name" in result
    assert "guidance" in result


def test_get_resource_error_rate_limit_error(server: NetSightMCPServer) -> None:
    """get_resource('netsight://errors/RateLimitError') has name and guidance."""
    result = server.get_resource("netsight://errors/RateLimitError")
    assert "name" in result
    assert "guidance" in result


def test_get_resource_error_response_size_error(server: NetSightMCPServer) -> None:
    """get_resource('netsight://errors/ResponseSizeError') has name and guidance."""
    result = server.get_resource("netsight://errors/ResponseSizeError")
    assert "name" in result
    assert "guidance" in result


def test_get_resource_error_plugin_not_found(server: NetSightMCPServer) -> None:
    """get_resource('netsight://errors/PluginNotFoundError') has name and guidance."""
    result = server.get_resource("netsight://errors/PluginNotFoundError")
    assert "name" in result
    assert "guidance" in result


def test_get_resource_error_all_have_description(server: NetSightMCPServer) -> None:
    """All error resources have a 'description' key."""
    error_names = [
        "CommandDeniedError",
        "AuthenticationError",
        "DeviceConnectionError",
        "PluginNotFoundError",
        "RateLimitError",
        "ResponseSizeError",
    ]
    for name in error_names:
        result = server.get_resource(f"netsight://errors/{name}")
        assert "description" in result, (
            f"Error resource '{name}' missing 'description'"
        )


# ---------------------------------------------------------------------------
# get_resource — unknown URI
# ---------------------------------------------------------------------------


def test_get_resource_unknown_uri_returns_error_dict(server: NetSightMCPServer) -> None:
    """get_resource() with an unknown URI returns a dict with an 'error' key."""
    result = server.get_resource("netsight://does-not-exist")
    assert isinstance(result, dict)
    assert "error" in result


def test_get_resource_unknown_uri_error_message_contains_uri(
    server: NetSightMCPServer,
) -> None:
    """The error message for an unknown URI references the URI string."""
    uri = "netsight://totally-unknown"
    result = server.get_resource(uri)
    assert uri in result.get("error", "")


# ---------------------------------------------------------------------------
# auto-registration
# ---------------------------------------------------------------------------


def test_paloalto_pack_is_registered_after_init(server: NetSightMCPServer) -> None:
    """paloalto-firewall-xml pack is registered in the global registry after server init."""
    from netsight_ops.packs.registry import pack_registry

    assert pack_registry.has("paloalto-firewall-xml"), (
        "paloalto-firewall-xml pack should be registered after NetSightMCPServer.__init__"
    )
