"""Click entry point — thin wiring over cli/commands.py."""

from __future__ import annotations

import click

from taskflow.cli import commands


@click.group()
def main() -> None:
    """taskflow — synthetic multi-module task manager."""


@main.command()
@click.argument("text")
@click.option("--due")
@click.option("--priority", default="normal",
              type=click.Choice([p for p in ["low", "normal", "high", "urgent"]]))
@click.option("--recur", default="none",
              type=click.Choice(["none", "daily", "weekly", "monthly", "yearly"]))
def add(text: str, due: str, priority: str, recur: str) -> None:
    for line in commands.cmd_add(commands._store(), text, due, priority, recur):
        click.echo(line)


@main.command(name="list")
@click.option("--overdue", is_flag=True)
def list_(overdue: bool) -> None:
    for line in commands.cmd_list(commands._store(), overdue):
        click.echo(line)


@main.command()
@click.argument("task_id", type=int)
def done(task_id: int) -> None:
    for line in commands.cmd_done(commands._store(), task_id):
        click.echo(line)


@main.command()
@click.argument("task_id", type=int)
def rm(task_id: int) -> None:
    for line in commands.cmd_rm(commands._store(), task_id):
        click.echo(line)


@main.command()
def standup() -> None:
    for line in commands.cmd_standup(commands._store()):
        click.echo(line)


if __name__ == "__main__":
    main()
