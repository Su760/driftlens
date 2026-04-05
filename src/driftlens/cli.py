import click


@click.group()
@click.version_option()
def cli() -> None:
    """DriftLens — code quality drift monitor for AI-generated code."""
