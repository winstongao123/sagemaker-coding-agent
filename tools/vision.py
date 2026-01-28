"""
Vision Tool - Image analysis using Claude vision
"""
import base64
import os

# Lazy import
Tool = None


def _get_tool_class():
    global Tool
    if Tool is None:
        from core.tools import Tool as T
        Tool = T
    return Tool


def view_image(args: dict, ctx) -> dict:
    """Load image for Claude vision analysis."""
    path = args["file_path"]

    # Handle relative paths
    if not os.path.isabs(path):
        path = os.path.join(ctx.working_dir, path)

    if not os.path.exists(path):
        return {"error": f"Image not found: {path}"}

    # Determine media type
    ext = os.path.splitext(path)[1].lower()
    media_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }

    media_type = media_types.get(ext)
    if not media_type:
        return {"error": f"Unsupported image format: {ext}. Supported: png, jpg, jpeg, gif, webp"}

    # Check file size (max 20MB for Claude)
    file_size = os.path.getsize(path)
    if file_size > 20 * 1024 * 1024:
        return {"error": f"Image too large: {file_size / (1024*1024):.1f}MB (max 20MB)"}

    try:
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")

        # Return as image content block for Bedrock
        # This will be handled specially by the agent loop
        return {
            "__image__": True,
            "type": "image",
            "source": {"type": "base64", "media_type": media_type, "data": data},
            "description": f"Image loaded from {path}",
        }

    except IOError as e:
        return {"error": f"Error reading image: {e}"}


def _format_image_result(result: dict) -> str:
    """Format image result for display."""
    if "error" in result:
        return f"Error: {result['error']}"

    if result.get("__image__"):
        return f"Image loaded successfully: {result.get('description', 'unknown')}"

    return str(result)


# Tool definition
def get_tool():
    """Get vision tool."""
    Tool = _get_tool_class()

    return Tool(
        name="view_image",
        description="View an image file (PNG, JPG, GIF, WebP) for AI analysis. Returns image data that Claude can analyze.",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to image file",
                }
            },
            "required": ["file_path"],
        },
        execute=lambda args, ctx: _format_image_result(view_image(args, ctx)),
        requires_approval=False,
    )


# Export tool
VIEW_IMAGE = get_tool()


# Also export the raw image loader for special handling
def get_image_data(args: dict, ctx) -> dict:
    """Get raw image data for embedding in messages."""
    return view_image(args, ctx)
