"""Real standard capabilities. Host construction establishes filesystem/tool trust."""

from pathlib import Path

from openverify.model import Context, Result
from openverify.relay.adapters.catalog import Catalog
from openverify.relay.core.aggregation import reduce_results
from openverify.standard.astgrep import astgrep_provider
from openverify.standard.command import command_observation_provider
from openverify.standard.control import control_providers
from openverify.standard.filesystem import FileAccess, filesystem_providers
from openverify.standard.git import git_providers
from openverify.standard.pytest import pytest_provider
from openverify.standard.ruff import ruff_provider
from openverify.standard.scope import scope_providers
from openverify.standard.structured import structured_providers
from openverify.standard.text import text_provider
from openverify.standard.tools import Tools, installed_tools


def standard_catalog(
    *, roots: tuple[Path, ...] | None = None, tools: Tools | None = None
) -> Catalog:
    access = (
        tools.access
        if tools
        else FileAccess(roots if roots is not None else (Path.cwd().resolve(),))
    )
    tools = tools or installed_tools(access)
    catalog = Catalog()

    async def aggregate(inputs: Context, config: Context) -> Result:
        return reduce_results(inputs, config)

    # Aggregate's dynamic member names are constrained by VCP membership validation.
    from openverify.relay.providers import provider

    aggregate_provider = provider(
        provider_id="openverify.standard.aggregate",
        capability_id="openverify.aggregate",
        kind="AGGREGATE",
        input_schema={"type": "object", "required": ["subject", "criterion", "members"]},
        config_schema={"type": "object"},
        output_schema={
            "type": "object",
            "required": ["result"],
            "properties": {"result": {"type": "object"}},
            "additionalProperties": False,
        },
    )(aggregate)
    for implementation in [
        text_provider(),
        *structured_providers(),
        *filesystem_providers(access),
        *scope_providers(),
        *git_providers(access),
        *control_providers(),
        command_observation_provider(),
        ruff_provider(tools),
        pytest_provider(tools),
        astgrep_provider(tools),
        aggregate_provider,
    ]:
        catalog.register(implementation, concurrency_safe=True)
    return catalog


__all__ = ("standard_catalog",)
