#!/usr/bin/env python3
"""
Quick deployment test script to verify Render compatibility
Tests basic functionality without requiring Discord connection
"""

import os
import sys
from pathlib import Path

def test_file_structure():
    """Test that all required files exist"""
    required_files = [
        'start.py',
        'main.py',
        'requirements-render.txt',
        'render.yaml',
        'Procfile',
        'RENDER_DEPLOY.md',
        '.gitignore'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All deployment files present")
        return True

def test_imports():
    """Test that all imports work"""
    try:
        import aiohttp
        import discord
        import groq
        import openai
        import psutil
        import requests
        import yaml
        print("✅ All required packages can be imported")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_directory_creation():
    """Test directory creation"""
    try:
        dirs = ['config', 'data', 'temp_keepalive']
        for dir_name in dirs:
            Path(dir_name).mkdir(exist_ok=True)
        print("✅ Directory creation works")
        return True
    except Exception as e:
        print(f"❌ Directory creation failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Render deployment readiness...\n")
    
    tests = [
        ("File Structure", test_file_structure),
        ("Package Imports", test_imports),
        ("Directory Creation", test_directory_creation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"Testing {test_name}...")
        if test_func():
            passed += 1
        print()
    
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Ready for Render deployment!")
        print("\nNext steps:")
        print("1. Push code to GitHub")
        print("2. Create Render web service")
        print("3. Set environment variables")
        print("4. Deploy!")
    else:
        print("❌ Some tests failed. Check the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()