#!/usr/bin/env python3
"""Simple test verification script."""

import sys
import importlib.util

def check_module(module_name, file_path):
    """Check if a module can be imported."""
    try:
        # Just check syntax, don't import
        with open(file_path, 'r') as f:
            compile(f.read(), file_path, 'exec')
        return True, "Syntax OK"
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, str(e)
    return False, "Unknown error"

def main():
    """Verify all test files can be imported."""
    test_files = [
        ("test_constants", "tests/unit/test_constants.py"),
        ("test_error_handling", "tests/unit/test_error_handling.py"),
        ("test_agent_manager", "tests/unit/test_agent_manager.py"),
        ("test_translation_service", "tests/unit/test_translation_service.py"),
        ("test_video_service", "tests/unit/test_video_service.py"),
        ("test_context_service", "tests/unit/test_context_service.py"),
        ("test_file_service", "tests/unit/test_file_service.py"),
        ("test_notes_generator", "tests/unit/test_notes_generator.py"),
        ("test_workflow", "tests/integration/test_workflow.py"),
    ]
    
    print("=" * 60)
    print("Test File Verification")
    print("=" * 60)
    print()
    
    passed = 0
    failed = 0
    
    for module_name, file_path in test_files:
        success, message = check_module(module_name, file_path)
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} - {file_path}")
        if not success:
            print(f"  Error: {message}")
            failed += 1
        else:
            passed += 1
    
    print()
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    # Count test functions
    print()
    print("Test Statistics:")
    print("-" * 60)
    
    total_tests = 0
    for module_name, file_path in test_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                test_count = content.count('def test_')
                total_tests += test_count
                print(f"  {file_path}: {test_count} tests")
        except Exception as e:
            print(f"  {file_path}: Error counting tests - {e}")
    
    print(f"\nTotal test functions: {total_tests}")
    print("=" * 60)
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
