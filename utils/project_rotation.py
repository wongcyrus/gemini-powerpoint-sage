"""Google Cloud Project rotation utility for load balancing across multiple projects."""

import os
import logging
from typing import List, Optional
import threading

logger = logging.getLogger(__name__)


class ProjectRotator:
    """Manages rotation through multiple Google Cloud projects to avoid quota limits."""
    
    def __init__(self):
        self._projects: List[str] = []
        self._current_index = 0
        self._lock = threading.Lock()
        self._initialized = False
    
    def _ensure_initialized(self) -> None:
        """Ensure projects are loaded (lazy initialization)."""
        if not self._initialized:
            with self._lock:
                if not self._initialized:  # Double-check locking
                    self._load_projects()
                    self._initialized = True
    
    def _load_projects(self) -> None:
        """Load projects from environment variable."""
        # First check for the new GOOGLE_CLOUD_PROJECTS variable (comma-separated)
        projects_env = os.getenv("GOOGLE_CLOUD_PROJECTS", "")
        print(f"🔍 DEBUG: GOOGLE_CLOUD_PROJECTS env var = '{projects_env}'")
        
        if projects_env:
            # Parse comma-separated projects
            self._projects = [p.strip() for p in projects_env.split(",") if p.strip()]
            print(f"🔍 DEBUG: Parsed {len(self._projects)} projects: {self._projects}")
            logger.info(f"Loaded {len(self._projects)} Google Cloud projects for rotation: {self._projects}")
            return
        
        # Fallback to single project from GOOGLE_CLOUD_PROJECT
        single_project = os.getenv("GOOGLE_CLOUD_PROJECT", "")
        print(f"🔍 DEBUG: GOOGLE_CLOUD_PROJECT env var = '{single_project}'")
        
        if single_project:
            self._projects = [single_project]
            print(f"🔍 DEBUG: Using single project: {single_project}")
            logger.info(f"Using single Google Cloud project: {single_project}")
        else:
            print(f"🔍 DEBUG: No Google Cloud projects configured")
            logger.warning("No Google Cloud projects configured")
            self._projects = []
    
    def get_next_project(self) -> Optional[str]:
        """Get the next project in rotation and set it as current GOOGLE_CLOUD_PROJECT."""
        self._ensure_initialized()
        
        if not self._projects:
            logger.warning("No projects available for rotation")
            return None
        
        with self._lock:
            current_project = self._projects[self._current_index]
            self._current_index = (self._current_index + 1) % len(self._projects)
            
            # Set the environment variable for the current process
            os.environ["GOOGLE_CLOUD_PROJECT"] = current_project
            logger.debug(f"Rotated to Google Cloud project: {current_project}")
            
            return current_project
    
    def get_current_project(self) -> Optional[str]:
        """Get the currently set project without rotation."""
        return os.getenv("GOOGLE_CLOUD_PROJECT")
    
    def get_project_count(self) -> int:
        """Get the number of available projects."""
        self._ensure_initialized()
        return len(self._projects)
    
    def reset_rotation(self) -> None:
        """Reset rotation to start from the first project."""
        self._ensure_initialized()
        
        with self._lock:
            self._current_index = 0
            if self._projects:
                os.environ["GOOGLE_CLOUD_PROJECT"] = self._projects[0]
                logger.debug(f"Reset rotation to first project: {self._projects[0]}")


# Global instance for project rotation
_project_rotator = ProjectRotator()


def rotate_project() -> Optional[str]:
    """
    Rotate to the next Google Cloud project and set GOOGLE_CLOUD_PROJECT environment variable.
    
    Returns:
        The project ID that was set, or None if no projects are configured.
    """
    return _project_rotator.get_next_project()


def get_current_project() -> Optional[str]:
    """
    Get the currently set Google Cloud project.
    
    Returns:
        The current project ID or None if not set.
    """
    return _project_rotator.get_current_project()


def get_project_count() -> int:
    """
    Get the number of available projects for rotation.
    
    Returns:
        Number of configured projects.
    """
    return _project_rotator.get_project_count()


def reset_project_rotation() -> None:
    """Reset project rotation to start from the first project."""
    _project_rotator.reset_rotation()


def reload_projects() -> None:
    """Force reload projects from environment variables."""
    _project_rotator._initialized = False
    _project_rotator._ensure_initialized()