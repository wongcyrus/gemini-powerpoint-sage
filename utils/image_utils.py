"""Image handling utilities for Gemini Powerpoint Sage."""

import io
import logging
from typing import Dict

from PIL import Image
from google.genai import types

logger = logging.getLogger(__name__)

# Global registry for images
IMAGE_REGISTRY: Dict[str, Image.Image] = {}

# Maximum dimension for images sent to Gemini (to avoid size limits)
MAX_IMAGE_DIMENSION = 2048


def resize_image_if_needed(image: Image.Image) -> Image.Image:
    """
    Resize image if it exceeds maximum dimensions while preserving aspect ratio.
    
    Args:
        image: PIL Image to check and potentially resize
        
    Returns:
        Resized (or original) PIL Image
    """
    width, height = image.size
    if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
        # Calculate new dimensions
        if width > height:
            new_width = MAX_IMAGE_DIMENSION
            new_height = int(height * (MAX_IMAGE_DIMENSION / width))
        else:
            new_height = MAX_IMAGE_DIMENSION
            new_width = int(width * (MAX_IMAGE_DIMENSION / height))
            
        logger.info(
            f"Resizing image from {width}x{height} to {new_width}x{new_height} "
            "to fit Gemini limits"
        )
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    return image


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
    # 1. Initial Resize (Dimension Safety)
    image = resize_image_if_needed(image)

    # 2. Byte Size Safety (Payload Limit)
    # Target: Keep individual images under 4MB to allow ~4-5 images per request
    # within the official 20MB payload limit.
    MAX_BYTES = 4 * 1024 * 1024
    
    buf = io.BytesIO()
    image.save(buf, format='PNG')
    img_bytes = buf.getvalue()
    
    if len(img_bytes) > MAX_BYTES:
        logger.info(f"Image too large ({len(img_bytes)/1024/1024:.2f}MB). Converting to JPEG...")
        
        # Handle transparency for JPEG conversion
        if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
            bg = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            bg.paste(image, mask=image.split()[3])
            image_to_save = bg
        else:
            image_to_save = image.convert('RGB')
            
        buf = io.BytesIO()
        image_to_save.save(buf, format='JPEG', quality=85)
        img_bytes = buf.getvalue()
        
        # If still too large, downscale further
        if len(img_bytes) > MAX_BYTES:
            logger.warning(f"JPEG still too large ({len(img_bytes)/1024/1024:.2f}MB). Downscaling...")
            new_width = int(image.width * 0.75)
            new_height = int(image.height * 0.75)
            image_to_save = image_to_save.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            buf = io.BytesIO()
            image_to_save.save(buf, format='JPEG', quality=80)
            img_bytes = buf.getvalue()

    if hasattr(types.Part, 'from_bytes'):
        return types.Part.from_bytes(
            data=img_bytes,
            mime_type='image/jpeg' if buf.getvalue().startswith(b'\xff\xd8') else 'image/png'
        )
    else:
        return types.Part(
            mime_type='image/jpeg' if buf.getvalue().startswith(b'\xff\xd8') else 'image/png',
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
