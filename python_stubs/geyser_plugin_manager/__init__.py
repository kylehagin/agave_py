"""Manager for loading and running Geyser plugins."""

from dataclasses import dataclass, field
from typing import List

from agave_geyser_plugin_interface.geyser_plugin_interface import GeyserPlugin


@dataclass
class LoadedGeyserPlugin:
    name: str
    plugin: GeyserPlugin


@dataclass
class GeyserPluginManager:
    plugins: List[LoadedGeyserPlugin] = field(default_factory=list)

    def unload(self) -> None:
        for p in self.plugins:
            p.plugin.on_unload()
        self.plugins.clear()

    def load_plugin(self, plugin: GeyserPlugin) -> str:
        """Register ``plugin`` and return its name."""

        name = plugin.name()
        self.plugins.append(LoadedGeyserPlugin(name, plugin))
        # TODO: replicate dynamic loading from a shared library
        return name

