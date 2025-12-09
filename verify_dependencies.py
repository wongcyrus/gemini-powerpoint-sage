#!/usr/bin/env python3
"""Verify all dependencies are installed and importable."""

import sys
from typing import List, Tuple


def check_imports() -> List[Tuple[str, bool, str]]:
    """Check if all required packages can be imported."""
    results = []
    
    # Core dependencies
    packages = [
        ("google.adk.agents", "google-adk"),
        ("google.genai", "google-genai"),
        ("pptx", "python-pptx"),
        ("fitz", "pymupdf"),
        ("PIL", "Pillow"),
        ("dotenv", "python-dotenv"),
        ("yaml", "pyyaml"),
    ]
    
    # Optional dependencies
    optional_packages = [
        ("fastmcp", "fastmcp"),
        ("pydantic", "pydantic"),
    ]
    
    print("Checking core dependencies...")
    print("=" * 60)
    
    for module_name, package_name in packages:
        try:
            __import__(module_name)
            results.append((package_name, True, "OK"))
            print(f"✅ {package_name:20s} - OK")
        except ImportError as e:
            results.append((package_name, False, str(e)))
            print(f"❌ {package_name:20s} - MISSING")
    
    print("\nChecking optional dependencies...")
    print("=" * 60)
    
    for module_name, package_name in optional_packages:
        try:
            __import__(module_name)
            results.append((package_name, True, "OK"))
            print(f"✅ {package_name:20s} - OK (optional)")
        except ImportError:
            results.append((package_name, False, "Not installed (optional)"))
            print(f"⚠️  {package_name:20s} - Not installed (optional)")
    
    return results


def check_versions():
    """Check versions of installed packages."""
    print("\n\nChecking package versions...")
    print("=" * 60)
    
    try:
        import pkg_resources
        
        packages = [
            "google-adk",
            "google-genai",
            "python-pptx",
            "pymupdf",
            "Pillow",
            "python-dotenv",
            "pyyaml",
        ]
        
        for package in packages:
            try:
                version = pkg_resources.get_distribution(package).version
                print(f"  {package:20s} : {version}")
            except pkg_resources.DistributionNotFound:
                print(f"  {package:20s} : NOT INSTALLED")
    except ImportError:
        print("⚠️  pkg_resources not available, skipping version check")


def main():
    """Main verification function."""
    print("\n" + "=" * 60)
    print("  Gemini PowerPoint Sage - Dependency Verification")
    print("=" * 60 + "\n")
    
    results = check_imports()
    check_versions()
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    core_results = results[:7]  # First 7 are core
    optional_results = results[7:]  # Rest are optional
    
    core_success = sum(1 for _, success, _ in core_results if success)
    core_total = len(core_results)
    
    optional_success = sum(1 for _, success, _ in optional_results if success)
    optional_total = len(optional_results)
    
    print(f"Core dependencies: {core_success}/{core_total} installed")
    print(f"Optional dependencies: {optional_success}/{optional_total} installed")
    
    if core_success == core_total:
        print("\n✅ All core dependencies are installed!")
        print("   You can run the application.")
        return 0
    else:
        print("\n❌ Some core dependencies are missing!")
        print("   Run: pip install -r requirements.txt")
        return 1


if __name__ == "__main__":
    sys.exit(main())
