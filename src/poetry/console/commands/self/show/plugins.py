from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING
from typing import DefaultDict

from poetry.console.commands.self.self_command import SelfCommand


if TYPE_CHECKING:
    from poetry.core.packages.package import Package


class SelfShowPluginsCommand(SelfCommand):
    name = "self show plugins"
    description = "Shows information about the currently installed plugins."
    help = """\
The <c1>self show plugins</c1> command lists all installed Poetry plugins.

Plugins can be added and removed using the <c1>self add</c1> and <c1>self remove</c1> \
commands respectively.

<warning>This command does not list packages that do not provide a Poetry plugin.</>
"""

    def _system_project_handle(self) -> int:
        from poetry.plugins.application_plugin import ApplicationPlugin
        from poetry.plugins.plugin import Plugin
        from poetry.plugins.plugin_manager import PluginManager
        from poetry.repositories.installed_repository import InstalledRepository
        from poetry.utils.env import EnvManager
        from poetry.utils.helpers import canonicalize_name
        from poetry.utils.helpers import pluralize

        plugins: DefaultDict[str, dict[str, Package | list[str]]] = defaultdict(
            lambda: {
                "package": None,
                "plugins": [],
                "application_plugins": [],
            }
        )

        system_env = EnvManager.get_system_env(naive=True)
        entry_points = PluginManager(ApplicationPlugin.group).get_plugin_entry_points(
            env=system_env
        ) + PluginManager(Plugin.group).get_plugin_entry_points(env=system_env)
        installed_repository = InstalledRepository.load(
            system_env, with_dependencies=True
        )

        packages_by_name = {pkg.name: pkg for pkg in installed_repository.packages}

        for entry_point in entry_points:
            plugin = entry_point.load()
            category = "plugins"
            if issubclass(plugin, ApplicationPlugin):
                category = "application_plugins"

            package = packages_by_name[canonicalize_name(entry_point.distro.name)]
            plugins[package.pretty_name]["package"] = package
            plugins[package.pretty_name][category].append(entry_point)

        for name, info in plugins.items():
            package = info["package"]
            description = " " + package.description if package.description else ""
            self.line("")
            self.line(f"  • <c1>{name}</c1> (<c2>{package.version}</c2>){description}")
            provide_line = "     "
            if info["plugins"]:
                count = len(info["plugins"])
                provide_line += f" <info>{count}</info> plugin{pluralize(count)}"

            if info["application_plugins"]:
                if info["plugins"]:
                    provide_line += " and"

                count = len(info["application_plugins"])
                provide_line += (
                    f" <info>{count}</info> application plugin{pluralize(count)}"
                )

            self.line(provide_line)

            if package.requires:
                self.line("")
                self.line("      <info>Dependencies</info>")
                for dependency in package.requires:
                    self.line(
                        f"        - {dependency.pretty_name}"
                        f" (<c2>{dependency.pretty_constraint}</c2>)"
                    )

        return 0
