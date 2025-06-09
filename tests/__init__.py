#!/usr/bin/env python3
"""
Tests package for Physics Literature Synthesis Pipeline.

This package contains all test files for the physics synthesis system.
"""

import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Test utilities
def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent

def setup_test_environment():
    """Set up the test environment with proper imports."""
    project_root = get_project_root()
    
    # Ensure project root is in path
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Return project root for convenience
    return project_root

__all__ = ['get_project_root', 'setup_test_environment']