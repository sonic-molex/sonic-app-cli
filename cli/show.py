import click


@click.command()
def otcli_example():
    """ This is an ot-cli example command """

    click.echo("Hello from ot-cli example")


def register(cli):
    cli.add_command(otcli_example)
