from click.testing import CliRunner

from ai_cli.cli import main


def test_main_exists():
    runner = CliRunner()
    result = runner.invoke(main, ["hello"])
    assert result.exit_code == 0
