"""Test Suite for MCP Sample Implementation.

Demonstrates unit and integration testing patterns for MCP servers and agents.
"""

import base64
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Note: These tests are templates. Adapt them for your environment.


class TestMCPServer:
    """Tests for the MCP server implementation."""

    @pytest.mark.asyncio
    async def test_server_initialization(self):
        """Test that MCP server initializes correctly."""
        from mcp_sample.veo_server import mcp

        assert mcp is not None
        assert mcp.name == "Veo 3.1 MCP Server"

    @pytest.mark.asyncio
    async def test_tool_registration(self):
        """Test that tools are registered with the server."""
        from mcp_sample.veo_server import mcp

        # Get registered tools
        tools = [tool.name for tool in mcp.list_tools()]

        assert "generate_video_with_image" in tools
        assert "list_video_models" in tools

    @pytest.mark.asyncio
    async def test_video_generation_invalid_inputs(self):
        """Test tool handles invalid inputs gracefully."""
        from mcp_sample.veo_server import (
            generate_video_with_image,
        )

        # Empty prompt
        result = await generate_video_with_image(
            prompt="",
            image_data="base64_data",
        )
        assert result["status"] == "error"

        # Empty image
        result = await generate_video_with_image(
            prompt="Generate video",
            image_data="",
        )
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_video_generation_missing_credentials(self):
        """Test tool handles missing credentials."""
        from mcp_sample.veo_server import (
            generate_video_with_image,
        )

        with patch.dict("os.environ", {}, clear=True):
            result = await generate_video_with_image(
                prompt="Generate video",
                image_data="base64_data",
            )

            assert result["status"] == "error"
            assert "credentials" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_list_models(self):
        """Test model listing functionality."""
        from mcp_sample.veo_server import list_video_models

        result = await list_video_models()

        assert result["status"] == "success"
        assert "models" in result
        assert len(result["models"]) > 0
        assert result["models"][0]["name"] == "veo-3.1-generate-preview"


class TestToolCallbacks:
    """Tests for tool callback implementation."""

    @pytest.mark.asyncio
    async def test_before_tool_modifier_artifact_loading(self):
        """Test before_tool_callback loads artifacts correctly."""
        from mcp_sample.tool_callbacks import before_tool_modifier
        from google.adk.tools.mcp_tool.mcp_tool import McpTool

        # Mock tool
        tool = MagicMock(spec=McpTool)
        tool.name = "generate_video_with_image"

        # Mock context
        mock_artifact = MagicMock()
        mock_artifact.inline_data.data = b"test_image_data"

        tool_context = AsyncMock()
        tool_context.load_artifact.return_value = mock_artifact

        # Test arguments
        args = {"image_data": "slide_1.png"}

        # Call modifier
        await before_tool_modifier(tool, args, tool_context)

        # Verify artifact was loaded
        tool_context.load_artifact.assert_called_once_with(
            filename="slide_1.png"
        )

        # Verify image_data was converted to base64
        expected_base64 = base64.b64encode(b"test_image_data").decode(
            "utf-8"
        )
        assert args["image_data"] == expected_base64

    @pytest.mark.asyncio
    async def test_before_tool_modifier_non_video_tool(self):
        """Test before_tool_callback skips non-video tools."""
        from mcp_sample.tool_callbacks import before_tool_modifier
        from google.adk.tools.mcp_tool.mcp_tool import McpTool

        # Mock tool with different name
        tool = MagicMock(spec=McpTool)
        tool.name = "other_tool"

        tool_context = AsyncMock()
        args = {"image_data": "slide_1.png"}

        # Call modifier
        await before_tool_modifier(tool, args, tool_context)

        # Verify no artifact was loaded
        tool_context.load_artifact.assert_not_called()

        # Verify args unchanged
        assert args["image_data"] == "slide_1.png"

    @pytest.mark.asyncio
    async def test_after_tool_modifier_artifact_saving(self):
        """Test after_tool_callback saves artifacts correctly."""
        from mcp_sample.tool_callbacks import after_tool_modifier
        from google.adk.tools.mcp_tool.mcp_tool import McpTool
        from google.genai.types import Part

        # Mock tool
        tool = MagicMock(spec=McpTool)
        tool.name = "generate_video_with_image"

        # Mock context
        tool_context = AsyncMock()
        tool_context.function_call_id = "abc123"
        tool_context.save_artifact = AsyncMock()

        # Tool response with video data
        video_bytes = b"test_video_data"
        video_base64 = base64.b64encode(video_bytes).decode("utf-8")

        tool_response = {
            "status": "success",
            "message": "Video generated",
            "video_data": video_base64,
        }

        # Call modifier
        result = await after_tool_modifier(
            tool, {}, tool_context, tool_response
        )

        # Verify artifact was saved
        tool_context.save_artifact.assert_called_once()

        # Verify response modified
        assert "artifact_id" in result
        assert result["artifact_id"] == "video_abc123.mp4"
        assert "video_data" not in result


class TestMCPTools:
    """Tests for MCP toolset configuration."""

    def test_stdio_mcp_toolset_creation(self):
        """Test STDIO MCP toolset can be created."""
        from mcp_sample.mcp_tools import create_stdio_mcp_toolset

        toolset = create_stdio_mcp_toolset()

        assert toolset is not None
        assert toolset.connection_params is not None

    def test_http_mcp_toolset_creation(self):
        """Test HTTP MCP toolset can be created."""
        from mcp_sample.mcp_tools import create_http_mcp_toolset

        toolset = create_http_mcp_toolset()

        assert toolset is not None
        assert toolset.connection_params is not None


class TestAgentConfig:
    """Tests for agent configuration."""

    def test_video_agent_creation(self):
        """Test video agent can be created."""
        from mcp_sample.agent_config import create_video_agent

        agent = create_video_agent()

        assert agent is not None
        assert agent.name == "presentation-video-generator"
        assert agent.model == "gemini-2.5-flash"


# Integration tests (requires live Vertex AI access)
@pytest.mark.integration
class TestIntegration:
    """Integration tests requiring live services."""

    @pytest.mark.asyncio
    async def test_agent_with_mcp_server(self):
        """Test agent can communicate with MCP server.
        
        Note: Requires GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION
        environment variables to be set.
        """
        import os

        if not os.getenv("GOOGLE_CLOUD_PROJECT"):
            pytest.skip("Missing Google Cloud credentials")

        from mcp_sample.agent_config import video_agent

        # This would require actual image data to test fully
        # For now, just verify agent initialization
        assert video_agent is not None


if __name__ == "__main__":
    # Run tests with: pytest tests/
    pytest.main([__file__, "-v"])
