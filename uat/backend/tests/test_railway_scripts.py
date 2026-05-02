"""
test_railway_scripts.py
=======================
Tests for Railway deployment scripts to ensure they're properly configured.
"""

import pytest
import os
import sys
import importlib.util
from pathlib import Path


def get_script_path(script_name: str) -> Path:
    """Get path to script file."""
    backend_dir = Path(__file__).parent.parent
    return backend_dir / "scripts" / script_name


class TestScriptStructure:
    """Test that scripts are properly structured and importable."""
    
    def test_scripts_directory_exists(self):
        """Ensure scripts directory exists."""
        backend_dir = Path(__file__).parent.parent
        scripts_dir = backend_dir / "scripts"
        assert scripts_dir.exists(), "scripts directory should exist"
        assert scripts_dir.is_dir(), "scripts should be a directory"
    
    def test_health_check_script_exists(self):
        """Ensure health check script exists."""
        script_path = get_script_path("check_railway_health.py")
        assert script_path.exists(), "check_railway_health.py should exist"
    
    def test_metrics_script_exists(self):
        """Ensure metrics collection script exists."""
        script_path = get_script_path("collect_deployment_metrics.py")
        assert script_path.exists(), "collect_deployment_metrics.py should exist"
    
    def test_health_check_script_has_shebang(self):
        """Ensure health check script has proper shebang."""
        script_path = get_script_path("check_railway_health.py")
        with open(script_path, 'r') as f:
            first_line = f.readline()
        assert first_line.startswith('#!'), "Script should have shebang"
        assert 'python' in first_line, "Shebang should reference python"
    
    def test_metrics_script_has_shebang(self):
        """Ensure metrics script has proper shebang."""
        script_path = get_script_path("collect_deployment_metrics.py")
        with open(script_path, 'r') as f:
            first_line = f.readline()
        assert first_line.startswith('#!'), "Script should have shebang"
        assert 'python' in first_line, "Shebang should reference python"


class TestScriptImports:
    """Test that scripts can import required dependencies."""
    
    def test_health_check_imports_railway_api(self):
        """Ensure health check script can import railway_api."""
        # This validates the sys.path manipulation in the script
        script_path = get_script_path("check_railway_health.py")
        
        # Read and check for railway_api import
        with open(script_path, 'r') as f:
            content = f.read()
        
        assert 'from railway_api import' in content, \
            "Script should import from railway_api"
        assert 'sys.path.insert' in content, \
            "Script should manipulate sys.path for imports"
    
    def test_metrics_script_imports_railway_api(self):
        """Ensure metrics script can import railway_api."""
        script_path = get_script_path("collect_deployment_metrics.py")
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        assert 'from railway_api import' in content, \
            "Script should import from railway_api"
        assert 'sys.path.insert' in content, \
            "Script should manipulate sys.path for imports"


class TestScriptDocumentation:
    """Test that scripts have proper documentation."""
    
    def test_health_check_has_docstring(self):
        """Ensure health check script has module docstring."""
        script_path = get_script_path("check_railway_health.py")
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Check for docstring
        assert '"""' in content or "'''" in content, \
            "Script should have docstring"
        assert "RAILWAY_API_TOKEN" in content, \
            "Docstring should document required env vars"
    
    def test_metrics_script_has_docstring(self):
        """Ensure metrics script has module docstring."""
        script_path = get_script_path("collect_deployment_metrics.py")
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        assert '"""' in content or "'''" in content, \
            "Script should have docstring"
        assert "RAILWAY_API_TOKEN" in content, \
            "Docstring should document required env vars"


class TestScriptFunctionality:
    """Test basic functionality of scripts."""
    
    def test_health_check_has_main_function(self):
        """Ensure health check script has main function."""
        script_path = get_script_path("check_railway_health.py")
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        assert 'async def main()' in content, \
            "Script should have async main function"
        assert 'return' in content, \
            "Main function should return exit code"
    
    def test_metrics_script_has_main_function(self):
        """Ensure metrics script has main function."""
        script_path = get_script_path("collect_deployment_metrics.py")
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        assert 'async def main()' in content, \
            "Script should have async main function"
        assert 'return' in content, \
            "Main function should return exit code"
    
    def test_health_check_validates_env_vars(self):
        """Ensure health check script validates required env vars."""
        script_path = get_script_path("check_railway_health.py")
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        assert 'os.environ.get("RAILWAY_API_TOKEN")' in content, \
            "Script should check for RAILWAY_API_TOKEN"
        assert 'os.environ.get("RAILWAY_PROJECT_ID")' in content, \
            "Script should check for RAILWAY_PROJECT_ID"
    
    def test_metrics_script_validates_env_vars(self):
        """Ensure metrics script validates required env vars."""
        script_path = get_script_path("collect_deployment_metrics.py")
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        assert 'os.environ.get("RAILWAY_API_TOKEN")' in content, \
            "Script should check for RAILWAY_API_TOKEN"
        assert 'os.environ.get("RAILWAY_PROJECT_ID")' in content, \
            "Script should check for RAILWAY_PROJECT_ID"


class TestScriptErrorHandling:
    """Test that scripts handle errors appropriately."""
    
    def test_health_check_handles_exceptions(self):
        """Ensure health check script has exception handling."""
        script_path = get_script_path("check_railway_health.py")
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        assert 'try:' in content, "Script should have try-except blocks"
        assert 'except' in content, "Script should catch exceptions"
        assert 'logger.error' in content or 'logging.error' in content, \
            "Script should log errors"
    
    def test_metrics_script_handles_exceptions(self):
        """Ensure metrics script has exception handling."""
        script_path = get_script_path("collect_deployment_metrics.py")
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        assert 'try:' in content, "Script should have try-except blocks"
        assert 'except' in content, "Script should catch exceptions"
        assert 'logger.error' in content or 'logging.error' in content, \
            "Script should log errors"


class TestScriptOutput:
    """Test that scripts produce expected output."""
    
    def test_health_check_outputs_json(self):
        """Ensure health check script outputs JSON results."""
        script_path = get_script_path("check_railway_health.py")
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        assert 'json.dump' in content, "Script should write JSON output"
        assert '.json' in content, "Output file should be JSON"
    
    def test_metrics_script_outputs_json(self):
        """Ensure metrics script outputs JSON results."""
        script_path = get_script_path("collect_deployment_metrics.py")
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        assert 'json.dump' in content, "Script should write JSON output"
        assert 'metrics.json' in content, "Should output to metrics.json"


class TestScriptExitCodes:
    """Test that scripts return proper exit codes."""
    
    def test_health_check_returns_exit_codes(self):
        """Ensure health check script returns proper exit codes."""
        script_path = get_script_path("check_railway_health.py")
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        assert 'sys.exit' in content, "Script should call sys.exit"
        assert 'return 0' in content, "Script should return 0 for success"
        assert 'return 1' in content, "Script should return 1 for failure"
    
    def test_metrics_script_returns_exit_codes(self):
        """Ensure metrics script returns proper exit codes."""
        script_path = get_script_path("collect_deployment_metrics.py")
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        assert 'sys.exit' in content, "Script should call sys.exit"
        assert 'return 0' in content, "Script should return 0 for success"
        assert 'return 1' in content, "Script should return 1 for failure"
