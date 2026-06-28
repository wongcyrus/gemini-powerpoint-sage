"""Tests for refinement processor behavior."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from services.refinement_processor import RefinementProcessor


class TestRefinementProcessor:
    """Tests for TTS note refinement."""

    @pytest.mark.asyncio
    async def test_refine_updates_slide_notes_and_saves_output(self):
        """Refinement should rewrite note text and persist the updated progress file."""
        processor = RefinementProcessor(Mock())
        progress_data = {
            "slides": {
                "slide_1": {"slide_index": 1, "note": "Original note"},
                "slide_2": {"slide_index": 2, "note": ""},
            }
        }

        with patch(
            "services.refinement_processor.load_progress",
            return_value=progress_data,
        ), patch(
            "services.refinement_processor.run_stateless_agent",
            AsyncMock(return_value="Refined note"),
        ) as mock_run_agent, patch(
            "services.refinement_processor.save_progress",
        ) as mock_save:
            await processor.refine("input.json", "output_refined.json")

        mock_run_agent.assert_awaited_once()
        saved_payload = mock_save.call_args.args[1]
        assert saved_payload["slides"]["slide_1"]["note"] == "Refined note"
        assert saved_payload["slides"]["slide_1"]["refined_from_original"] is True
        assert "refined_from_original" not in saved_payload["slides"]["slide_2"]

    @pytest.mark.asyncio
    async def test_refine_skips_invalid_progress_files(self):
        """Refinement should stop early when the input JSON does not contain slides."""
        processor = RefinementProcessor(Mock())

        with patch(
            "services.refinement_processor.load_progress",
            return_value={"status": "broken"},
        ), patch(
            "services.refinement_processor.run_stateless_agent",
            AsyncMock(),
        ) as mock_run_agent, patch(
            "services.refinement_processor.save_progress",
        ) as mock_save:
            await processor.refine("input.json", "output_refined.json")

        mock_run_agent.assert_not_called()
        mock_save.assert_not_called()

    @pytest.mark.asyncio
    async def test_refine_keeps_original_note_when_agent_returns_empty(self):
        """Refinement should leave the existing note untouched if the agent yields no output."""
        processor = RefinementProcessor(Mock())
        progress_data = {"slides": {"slide_1": {"slide_index": 1, "note": "Keep me"}}}

        with patch(
            "services.refinement_processor.load_progress",
            return_value=progress_data,
        ), patch(
            "services.refinement_processor.run_stateless_agent",
            AsyncMock(return_value=""),
        ), patch(
            "services.refinement_processor.save_progress",
        ) as mock_save:
            await processor.refine("input.json", "output_refined.json")

        saved_payload = mock_save.call_args.args[1]
        assert saved_payload["slides"]["slide_1"]["note"] == "Keep me"
        assert "refined_from_original" not in saved_payload["slides"]["slide_1"]
