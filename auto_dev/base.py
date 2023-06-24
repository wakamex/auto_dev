"""
Base CLI for auto_dev.
"""
import os

import rich_click as click

from auto_dev.constants import DEFAULT_ENCODING
from auto_dev.utils import get_logger

plugin_folder = os.path.join(os.path.dirname(__file__), 'commands')
click.rich_click.USE_RICH_MARKUP = True


class CLIs:
    """C;I class."""

    def list_commands(self):
        """List commands."""
        results = []
        for filename in os.listdir(plugin_folder):
            if filename.endswith('.py') and filename != '__init__.py':
                results.append(filename[:-3])
        results.sort()
        return results

    def get_command(self, name):
        """Get the command."""
        name_space = {}
        file_name = os.path.join(plugin_folder, name + '.py')
        with open(file_name, encoding=DEFAULT_ENCODING) as file:
            code = compile(file.read(), file_name, 'exec')
            eval(code, name_space, name_space)  # pylint: disable=eval-used
        return name_space[name]

    def get_all_commands(
        self,
    ):
        """Iterate over all commands."""
        for name in self.list_commands():
            yield name, self.get_command(name)


def build_cli(plugins=False):
    """Build the CLI."""

    @click.group()
    @click.option("-v", "--verbose", is_flag=True, default=False)
    @click.option(
        "-l",
        "--log-level",
        default="INFO",
        help="Set the logging level",
        type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    )
    @click.option("-n", "--num-processes", default=1, help="Number of processes to use for linting", type=int)
    @click.pass_context
    def cli(ctx, log_level=False, verbose=False, num_processes=1):
        """Cli linting tooling."""
        ctx.obj = {}
        ctx.obj["VERBOSE"] = verbose
        ctx.obj["LOGGER"] = get_logger(log_level=log_level)
        ctx.obj["NUM_PROCESSES"] = num_processes

    if plugins:
        plugins = CLIs().get_all_commands()
        for name, plugin in plugins:
            cli.add_command(plugin, name=name)
    return cli
