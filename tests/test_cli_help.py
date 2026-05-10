import pytest
from asyncclick.testing import CliRunner

from scripts.main import cli


@pytest.mark.asyncio
async def test_top_level_help_shows_full_command_descriptions():
    runner = CliRunner()
    result = await runner.invoke(cli, ["--help"])

    normalized_output = " ".join(result.output.replace("-\n", "").split())
    commands_section = result.output.split("Commands:", 1)[1]

    assert result.exit_code == 0
    assert "Downloads a file from a specific URL." in normalized_output
    assert "Downloads platform subtitles as SRT/TXT for a classroom video." in normalized_output
    assert "Creates a local Markdown review note from platform subtitles." in normalized_output
    assert "Builds an agent-ready study note from one course material and one video transcript." in normalized_output
    assert "..." not in commands_section
