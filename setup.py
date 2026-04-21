#!/usr/bin/env python3
"""
Quick setup script for Coverage Gap Analyzer.
Runs initial setup tasks and verifies installation.
"""

import os
import sys
from pathlib import Path


def check_python_version():
    """Verify Python version is 3.11+."""
    if sys.version_info < (3, 11):
        print("❌ Python 3.11 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✓ Python version: {sys.version.split()[0]}")
    return True


def check_dependencies():
    """Check if required packages are installed."""
    required = [
        "langchain",
        "langchain_anthropic",
        "langgraph",
        "dotenv"
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package.replace("-", "_"))
            print(f"✓ {package} installed")
        except ImportError:
            missing.append(package)
            print(f"✗ {package} not found")
    
    if missing:
        print("\n❌ Missing dependencies. Install with:")
        print("   pip install -r requirements.txt")
        return False
    
    return True


def check_api_key():
    """Check if API key is configured."""
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key == "your-api-key-here":
        print("❌ ANTHROPIC_API_KEY not configured")
        print("   1. Copy .env.template to .env")
        print("   2. Add your API key from https://console.anthropic.com")
        return False
    
    print("✓ API key configured")
    return True


def create_sample_data():
    """Generate sample coverage reports."""
    try:
        from mock_data import save_sample_reports
        files = save_sample_reports()
        print(f"✓ Created {len(files)} sample coverage reports")
        return True
    except Exception as e:
        print(f"✗ Error creating sample data: {e}")
        return False


def create_directories():
    """Create necessary directories."""
    dirs = ["data", "outputs"]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    print(f"✓ Created directories: {', '.join(dirs)}")
    return True


def test_basic_functionality():
    """Run a basic functionality test."""
    print("\n" + "="*60)
    print("Running basic functionality test...")
    print("="*60)
    
    try:
        from coverage_parser import CoverageParser
        from mock_data import get_minimal_report
        
        report = get_minimal_report()
        parser = CoverageParser(report)
        gaps = parser.parse()
        
        print(f"✓ Parsed {len(gaps)} coverage gaps")
        print("✓ Parser working correctly")
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def main():
    """Run all setup checks."""
    print("="*60)
    print("Coverage Gap Analyzer - Setup Verification")
    print("="*60)
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("API Key", check_api_key),
        ("Directories", create_directories),
        ("Sample Data", create_sample_data),
        ("Basic Test", test_basic_functionality),
    ]
    
    results = []
    for name, check_fn in checks:
        print(f"\nChecking {name}...")
        results.append(check_fn())
    
    print("\n" + "="*60)
    if all(results):
        print("✅ Setup complete! All checks passed.")
        print("\nNext steps:")
        print("  1. Review the sample coverage reports in data/")
        print("  2. Run the analyzer: python agent.py")
        print("  3. Check outputs/ for generated reports")
        print("  4. Read ROADMAP.md for next steps")
    else:
        print("❌ Setup incomplete. Please fix the issues above.")
        return 1
    
    print("="*60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
