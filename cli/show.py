import click


@click.command()
def sonic_app_cli_example():
    """ This is an sonic-app-cli example command """

    click.echo("Hello from sonic-app-cli example")


def register(cli):
    cli.add_command(sonic_app_cli_example)
