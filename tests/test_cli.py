"""Tests for cosmic_web CLI commands."""

from typer.testing import CliRunner

from cosmic_web.cli import app

runner = CliRunner()


def test_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_render_default():
    result = runner.invoke(app, ["render"])
    assert result.exit_code == 0
    assert "Cosmic Web" in result.output
    assert "emergence" in result.output.lower()


def test_render_custom_nodes():
    result = runner.invoke(app, ["render", "--nodes", "10", "--edges", "20"])
    assert result.exit_code == 0
    assert "10 nodes" in result.output


def test_simulate_default():
    result = runner.invoke(app, ["simulate", "--nodes", "20", "--steps", "3"])
    assert result.exit_code == 0
    assert "step" in result.output
    assert "emergence" in result.output.lower()


def test_simulate_steps_count():
    result = runner.invoke(app, ["simulate", "--nodes", "20", "--steps", "4"])
    assert result.exit_code == 0
    # Should show 4 step lines
    step_lines = [line for line in result.output.splitlines() if line.strip().startswith("step")]
    assert len(step_lines) == 4
