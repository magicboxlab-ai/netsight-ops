"""Tests for netsight_ops.api.graphql — types, resolvers, and schema execution."""

from __future__ import annotations


from netsight_ops.api.graphql.schema import schema
from netsight_ops.api.graphql.types import PatternStepType, PatternType, PluginType, RelationType


# ---------------------------------------------------------------------------
# Type instantiation — PluginType
# ---------------------------------------------------------------------------


def test_plugin_type_fields() -> None:
    """PluginType stores name, description, and operations correctly."""
    pt = PluginType(name="my_plugin", description="A test plugin", operations=["op_a", "op_b"])
    assert pt.name == "my_plugin"
    assert pt.description == "A test plugin"
    assert pt.operations == ["op_a", "op_b"]


def test_plugin_type_empty_operations() -> None:
    """PluginType accepts an empty operations list."""
    pt = PluginType(name="empty", description="", operations=[])
    assert pt.operations == []


# ---------------------------------------------------------------------------
# Type instantiation — PatternStepType
# ---------------------------------------------------------------------------


def test_pattern_step_type_fields() -> None:
    """PatternStepType stores operation and description correctly."""
    step = PatternStepType(operation="show_system_info", description="Get system info")
    assert step.operation == "show_system_info"
    assert step.description == "Get system info"


# ---------------------------------------------------------------------------
# Type instantiation — PatternType
# ---------------------------------------------------------------------------


def test_pattern_type_fields() -> None:
    """PatternType stores name, description, and steps correctly."""
    steps = [PatternStepType(operation="show_system_info", description="Step 1")]
    pt = PatternType(name="health-check", description="Check health", steps=steps)
    assert pt.name == "health-check"
    assert pt.description == "Check health"
    assert len(pt.steps) == 1
    assert pt.steps[0].operation == "show_system_info"


# ---------------------------------------------------------------------------
# Type instantiation — RelationType
# ---------------------------------------------------------------------------


def test_relation_type_fields() -> None:
    """RelationType stores source, target, and relation_type correctly."""
    rel = RelationType(source="op_a", target="op_b", relation_type="complementary")
    assert rel.source == "op_a"
    assert rel.target == "op_b"
    assert rel.relation_type == "complementary"


# ---------------------------------------------------------------------------
# Schema execution — plugins query
# ---------------------------------------------------------------------------


def test_plugins_query_no_errors() -> None:
    """{ plugins { name } } executes without errors."""
    result = schema.execute_sync("{ plugins { name } }")
    assert result.errors is None or result.errors == []


def test_plugins_query_returns_list() -> None:
    """{ plugins { name } } returns a list in result.data['plugins']."""
    result = schema.execute_sync("{ plugins { name } }")
    assert result.data is not None
    assert isinstance(result.data["plugins"], list)


def test_plugins_query_at_least_one_result() -> None:
    """Plugins query returns at least one plugin (panos_xml auto-registers)."""
    result = schema.execute_sync("{ plugins { name } }")
    assert result.data is not None
    assert len(result.data["plugins"]) >= 1


def test_plugins_query_includes_name_field() -> None:
    """Each plugin result has a non-empty 'name' field."""
    result = schema.execute_sync("{ plugins { name } }")
    assert result.data is not None
    for plugin in result.data["plugins"]:
        assert isinstance(plugin["name"], str)
        assert plugin["name"]


def test_plugins_query_full_fields() -> None:
    """{ plugins { name description operations } } returns all three fields."""
    result = schema.execute_sync("{ plugins { name description operations } }")
    assert result.errors is None or result.errors == []
    assert result.data is not None
    for plugin in result.data["plugins"]:
        assert "name" in plugin
        assert "description" in plugin
        assert "operations" in plugin
        assert isinstance(plugin["operations"], list)


def test_plugins_query_paloalto_pack_registered() -> None:
    """paloalto-firewall-xml pack is present in plugins query results."""
    result = schema.execute_sync("{ plugins { name } }")
    assert result.data is not None
    names = [p["name"] for p in result.data["plugins"]]
    assert "paloalto-firewall-xml" in names


# ---------------------------------------------------------------------------
# Schema execution — patterns query
# ---------------------------------------------------------------------------


def test_patterns_query_no_errors() -> None:
    """{ patterns { name description } } executes without errors."""
    result = schema.execute_sync("{ patterns { name description } }")
    assert result.errors is None or result.errors == []


def test_patterns_query_returns_list() -> None:
    """Patterns query returns a list."""
    result = schema.execute_sync("{ patterns { name description } }")
    assert result.data is not None
    assert isinstance(result.data["patterns"], list)


def test_patterns_query_at_least_four_patterns() -> None:
    """Patterns query returns at least 4 builtin patterns."""
    result = schema.execute_sync("{ patterns { name description } }")
    assert result.data is not None
    assert len(result.data["patterns"]) >= 4


def test_patterns_query_with_steps() -> None:
    """{ patterns { name steps { operation description } } } returns steps."""
    result = schema.execute_sync("{ patterns { name steps { operation description } } }")
    assert result.errors is None or result.errors == []
    assert result.data is not None
    for pattern in result.data["patterns"]:
        assert isinstance(pattern["steps"], list)
        assert len(pattern["steps"]) >= 1


def test_patterns_query_known_pattern_present() -> None:
    """'device-health-check' pattern is present in patterns query results."""
    result = schema.execute_sync("{ patterns { name } }")
    assert result.data is not None
    names = [p["name"] for p in result.data["patterns"]]
    assert "device-health-check" in names


def test_patterns_query_all_have_descriptions() -> None:
    """Every pattern returned has a non-empty description."""
    result = schema.execute_sync("{ patterns { name description } }")
    assert result.data is not None
    for pattern in result.data["patterns"]:
        assert isinstance(pattern["description"], str)
        assert pattern["description"]


# ---------------------------------------------------------------------------
# Schema execution — relations query
# ---------------------------------------------------------------------------


def test_relations_query_no_errors() -> None:
    """{ relations { source target relationType } } executes without errors."""
    result = schema.execute_sync("{ relations { source target relationType } }")
    assert result.errors is None or result.errors == []


def test_relations_query_returns_list() -> None:
    """Relations query returns a list."""
    result = schema.execute_sync("{ relations { source target relationType } }")
    assert result.data is not None
    assert isinstance(result.data["relations"], list)


def test_relations_query_at_least_six_relations() -> None:
    """Relations query returns at least 6 relations from the default graph."""
    result = schema.execute_sync("{ relations { source target relationType } }")
    assert result.data is not None
    assert len(result.data["relations"]) >= 6


def test_relations_query_fields_present() -> None:
    """Every relation has source, target, and relationType fields."""
    result = schema.execute_sync("{ relations { source target relationType } }")
    assert result.data is not None
    for rel in result.data["relations"]:
        assert "source" in rel
        assert "target" in rel
        assert "relationType" in rel
        assert isinstance(rel["source"], str)
        assert isinstance(rel["target"], str)
        assert isinstance(rel["relationType"], str)


def test_relations_query_known_relation_present() -> None:
    """The 'show_routing_table'/'show_arp_table' complementary relation is present."""
    result = schema.execute_sync("{ relations { source target relationType } }")
    assert result.data is not None
    found = any(
        r["source"] == "show_routing_table"
        and r["target"] == "show_arp_table"
        and r["relationType"] == "complementary"
        for r in result.data["relations"]
    )
    assert found, "Expected show_routing_table->show_arp_table complementary relation"


# ---------------------------------------------------------------------------
# Schema introspection
# ---------------------------------------------------------------------------


def test_schema_introspection_query_type() -> None:
    """GraphQL introspection returns 'Query' as the query type name."""
    result = schema.execute_sync("{ __schema { queryType { name } } }")
    assert result.errors is None or result.errors == []
    assert result.data is not None
    assert result.data["__schema"]["queryType"]["name"] == "Query"


def test_schema_introspection_fields() -> None:
    """GraphQL introspection reports plugins, patterns, and relations fields."""
    result = schema.execute_sync("{ __type(name: \"Query\") { fields { name } } }")
    assert result.errors is None or result.errors == []
    assert result.data is not None
    field_names = {f["name"] for f in result.data["__type"]["fields"]}
    assert "plugins" in field_names
    assert "patterns" in field_names
    assert "relations" in field_names
