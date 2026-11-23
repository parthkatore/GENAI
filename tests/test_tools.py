"""
tests/test_tools.py — Agent tool unit tests.
--------------------------------------------
Tests backend.app.tools.led_resistor_calculator directly (pure arithmetic — no
network, no LLM) and tests rag_search with a stubbed rag_answer to
confirm the dispatcher and E12 rounding are both correct.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from backend.app.tools import call_tool, led_resistor_calculator


class TestLedResistorCalculator:
    """led_resistor_calculator — Ohm's law + E12 rounding."""

    def test_standard_5v_red_led_20ma(self):
        """Classic 5V red LED (Vf=2V, 20mA) must suggest 150 Ω."""
        result = led_resistor_calculator(
            supply_voltage=5.0,
            led_forward_voltage=2.0,
            led_current_ma=20.0,
        )
        assert "150" in result, f"Expected 150 Ω, got: {result}"

    def test_3v3_blue_led_10ma(self):
        """3.3V blue LED (Vf=3.0V, 10mA) → R_exact=30Ω → E12=33Ω."""
        result = led_resistor_calculator(
            supply_voltage=3.3,
            led_forward_voltage=3.0,
            led_current_ma=10.0,
        )
        # Exact = (3.3 - 3.0) / 0.010 = 30 Ω → next E12 = 33 Ω
        assert "33" in result, f"Expected 33 Ω, got: {result}"

    def test_result_contains_formula_line(self):
        """Result must include the formula R = (Vs - Vf) / I."""
        result = led_resistor_calculator(5.0, 2.0, 20.0)
        assert "Formula" in result or "=" in result

    def test_zero_current_returns_error(self):
        """Zero LED current must return an error string, not raise."""
        result = led_resistor_calculator(5.0, 2.0, 0.0)
        assert "Error" in result or "error" in result.lower()

    def test_supply_less_than_forward_voltage_returns_error(self):
        """Supply voltage below LED forward voltage must return an error."""
        result = led_resistor_calculator(2.0, 3.3, 20.0)
        assert "Error" in result or "error" in result.lower()

    def test_e12_rounding_always_rounds_up(self):
        """The returned E12 value must always be >= the exact resistance."""
        from backend.app.tools import _next_e12  # access the helper directly

        # Spot-check several values
        assert _next_e12(100) == 100
        assert _next_e12(101) == 120   # 101 Ω → next E12 = 120 Ω
        assert _next_e12(150) == 150
        assert _next_e12(151) == 180
        assert _next_e12(1000) == 1000
        assert _next_e12(1001) == 1200


class TestRagSearchTool:
    """rag_search — dispatches to rag_answer and formats citations."""

    def test_rag_search_returns_string(self):
        """rag_search must return a plain string regardless of the answer."""
        mock_resp = MagicMock()
        mock_resp.answer = "pinMode() configures a pin as INPUT or OUTPUT."
        mock_resp.out_of_scope = False
        mock_resp.citations = []

        with patch("backend.app.rag.rag_answer", return_value=mock_resp):
            from backend.app.tools import rag_search

            result = rag_search("What does pinMode do?")
        assert isinstance(result, str)
        assert "pinMode" in result

    def test_rag_search_out_of_scope_returns_dont_know(self):
        """Out-of-scope questions must return the standard refusal string."""
        mock_resp = MagicMock()
        mock_resp.answer = "I don't know based on the available Arduino documentation."
        mock_resp.out_of_scope = True
        mock_resp.citations = []

        with patch("backend.app.rag.rag_answer", return_value=mock_resp):
            from backend.app.tools import rag_search

            result = rag_search("How do I wire an HC-SR04 sensor?")
        assert "don't know" in result.lower() or "i don" in result.lower()

    def test_rag_search_includes_sources_when_citations_exist(self):
        """When citations are present, the result must include 'Sources:'."""
        mock_citation = MagicMock()
        mock_citation.title = "pinMode()"
        mock_citation.source = "data/raw/pinMode.adoc"
        mock_citation.page = 1
        mock_citation.score = 0.85

        mock_resp = MagicMock()
        mock_resp.answer = "pinMode configures pin direction."
        mock_resp.out_of_scope = False
        mock_resp.citations = [mock_citation]

        with patch("backend.app.rag.rag_answer", return_value=mock_resp):
            from backend.app.tools import rag_search

            result = rag_search("pinMode")
        assert "Sources:" in result or "Sources" in result


class TestCallToolDispatcher:
    """call_tool — central dispatcher routes to the correct function."""

    def test_dispatch_led_resistor_calculator(self):
        """call_tool('led_resistor_calculator', ...) must invoke the calculator."""
        result = call_tool(
            "led_resistor_calculator",
            {"supply_voltage": 5.0, "led_forward_voltage": 2.0, "led_current_ma": 20.0},
        )
        assert isinstance(result, str)
        assert "150" in result

    def test_dispatch_unknown_tool_raises_value_error(self):
        """call_tool with an unknown tool name must raise ValueError."""
        with pytest.raises(ValueError, match="Unknown tool"):
            call_tool("nonexistent_tool", {})

    def test_dispatch_rag_search(self):
        """call_tool('rag_search', ...) must delegate to rag_search."""
        mock_resp = MagicMock()
        mock_resp.answer = "analogRead returns 0–1023."
        mock_resp.out_of_scope = False
        mock_resp.citations = []

        with patch("backend.app.rag.rag_answer", return_value=mock_resp):
            result = call_tool("rag_search", {"question": "What is analogRead?"})
        assert isinstance(result, str)
        assert "analogRead" in result or "0" in result
