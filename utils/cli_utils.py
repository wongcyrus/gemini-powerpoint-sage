"""
Utility functions for CLI argument parsing and path resolution.
"""

import os
import sys
from typing import List, Optional

def parse_languages(languages_str: str) -> List[str]:
    """
    Parse comma-separated languages string into a list, ensuring English is first.
    
    Args:
        languages_str: Comma-separated language codes (e.g., "en,zh-CN")
        
    Returns:
        List of language codes with 'en' as the first element if present.
    """
    lang_list = [lang.strip() for lang in languages_str.split(",")]
    if "en" not in lang_list:
        lang_list.insert(0, "en")
    elif lang_list[0] != "en":
        lang_list.remove("en")
        lang_list.insert(0, "en")
    return lang_list

def resolve_pptx_path(pptx_arg: str) -> str:
    """
    Resolve and validate the PowerPoint file path.
    Handles whitespace normalization and fuzzy matching.
    
    Args:
        pptx_arg: The input path argument.
        
    Returns:
        The absolute path to the resolved PPTX/PPTM file.
        
    Raises:
        FileNotFoundError: If the file cannot be resolved.
    """
    # Normalize PPTX path (trim whitespace, replace non-breaking spaces)
    normalized_pptx_arg = pptx_arg.strip().replace('\u00A0', ' ')
    
    if os.path.exists(normalized_pptx_arg):
        return os.path.abspath(normalized_pptx_arg)
        
    # Attempt fuzzy match by collapsing multiple spaces
    pptx_dir_try = os.path.dirname(normalized_pptx_arg) or os.getcwd()
    base_try = os.path.basename(normalized_pptx_arg)
    collapsed_target = ' '.join(base_try.split())
    
    try:
        for fname in os.listdir(pptx_dir_try):
            if ' '.join(fname.split()) == collapsed_target:
                resolved = os.path.join(pptx_dir_try, fname)
                if os.path.exists(resolved):
                    return os.path.abspath(resolved)
    except Exception:
        pass
        
    # Construct helpful error message
    msg = f"PPTX/PPTM file not found: {pptx_arg}\n"
    msg += "Hint: Remove trailing spaces or unusual characters."
    try:
        nearby = [f for f in os.listdir(pptx_dir_try) 
                 if f.lower().endswith(('.pptx', '.pptm'))]
        if nearby:
            msg += "\nNearby candidates:\n" + "\n".join(f"  - {f}" for f in nearby)
    except Exception:
        pass
        
    raise FileNotFoundError(msg)

def resolve_pdf_path(pdf_arg: Optional[str], pptx_path: str) -> Optional[str]:
    """
    Resolve the PDF path, either from argument or auto-detection.
    
    Args:
        pdf_arg: The PDF path argument provided by user.
        pptx_path: The resolved PPTX path (used for auto-detection).
        
    Returns:
        The absolute path to the PDF file, or None if not found/resolved.
    """
    pptx_dir = os.path.dirname(pptx_path)
    pptx_base = os.path.splitext(os.path.basename(pptx_path))[0]
    
    # 1. Check explicit argument
    if pdf_arg:
        pdf_abs = os.path.abspath(pdf_arg)
        # Enforce same directory for simplicity/safety (as per original logic)
        if os.path.dirname(pdf_abs) != pptx_dir:
            print("Warning: Provided PDF must be in the same folder as the PPTX/PPTM.")
            return None
        if os.path.exists(pdf_abs):
            return pdf_abs
        else:
            print(f"Warning: Provided PDF not found: {pdf_arg}")
            return None
            
    # 2. Auto-detect
    candidate = os.path.join(pptx_dir, pptx_base + ".pdf")
    if os.path.exists(candidate):
        return candidate
        
    return None
