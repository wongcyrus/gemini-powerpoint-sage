"""Image handling utilities for Gemini Powerpoint Sage."""

import io
import logging
from typing import Dict

from PIL import Image
from google.genai import types

logger = logging.getLogger(__name__)

# Global registry for images
IMAGE_REGISTRY: Dict[str, Image.Image] = {}


def create_image_part(image: Image.Image) -> types.Part:
    """
    Create a Part object from a PIL Image safely.
    
    Handles different versions of the Google GenAI SDK that may have
    different methods for creating image parts.
    
    Args:
        image: PIL Image object to convert
        
    Returns:
        types.Part object containing the image
    """
    if hasattr(types.Part, 'from_image'):
        return types.Part.from_image(image=image)
    else:
        buf = io.BytesIO()
        image.save(buf, format='PNG')
        img_bytes = buf.getvalue()
        if hasattr(types.Part, 'from_bytes'):
            return types.Part.from_bytes(
                data=img_bytes,
                mime_type='image/png'
            )
        else:
            return types.Part(
                mime_type='image/png',
                data=img_bytes
            )


def register_image(image_id: str, image: Image.Image) -> None:
    """
    Register an image in the global registry.
    
    Args:
        image_id: Unique identifier for the image
        image: PIL Image object to register
    """
    IMAGE_REGISTRY[image_id] = image


def get_image(image_id: str) -> Image.Image:
    """
    Retrieve an image from the global registry.
    
    Args:
        image_id: Unique identifier for the image
        
    Returns:
        PIL Image object or None if not found
    """
    return IMAGE_REGISTRY.get(image_id)


def unregister_image(image_id: str) -> None:
    """
    Remove an image from the global registry.
    
    Args:
        image_id: Unique identifier for the image to remove
    """
    if image_id in IMAGE_REGISTRY:
        del IMAGE_REGISTRY[image_id]


def clear_registry() -> None:
    """Clear all images from the registry."""
    IMAGE_REGISTRY.clear()
