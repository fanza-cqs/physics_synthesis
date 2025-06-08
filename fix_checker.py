#!/usr/bin/env python3
"""
Quick diagnostic to find what broke when disabling upload_replace
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path.cwd()
if project_root.name != "physics_synthesis":
    project_root = project_root.parent
sys.path.insert(0, str(project_root))

print(f"🔍 DIAGNOSING UPLOAD_REPLACE REMOVAL ISSUES")
print("=" * 60)

def check_file_imports(file_path: Path, description: str):
    """Check if a file can be imported."""
    print(f"\n📄 Checking {description}: {file_path.name}")
    
    if not file_path.exists():
        print(f"❌ File doesn't exist: {file_path}")
        return False
    
    try:
        # Try to read and check for syntax issues
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for common issues
        issues = []
        
        # Check for upload_replace references that might be broken
        if "upload_replace" in content and "DISABLED" not in content:
            issues.append("Still has upload_replace references")
        
        # Check for setup_upload_replace_mode references
        if "setup_upload_replace_mode" in content:
            issues.append("Still references setup_upload_replace_mode")
        
        # Check for mode3_upload_and_replace_fixed references
        if "mode3_upload_and_replace_fixed" in content:
            issues.append("Still references mode3_upload_and_replace_fixed")
        
        if issues:
            print(f"⚠️  Potential issues found:")
            for issue in issues:
                print(f"   • {issue}")
        else:
            print(f"✅ File looks clean")
        
        return len(issues) == 0
        
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

# Check key files that might be affected
files_to_check = [
    (project_root / "src" / "downloaders" / "zotero_pdf_integrator_fixed.py", "Main integrator"),
    (project_root / "src" / "downloaders" / "zotero_pdf_integrator_parts" / "part6_main_function.py", "Part 6"),
    (project_root / "src" / "downloaders" / "enhanced_literature_syncer.py", "Enhanced syncer"),
    (project_root / "src" / "downloaders" / "__init__.py", "Downloaders init"),
]

all_clean = True
for file_path, description in files_to_check:
    is_clean = check_file_imports(file_path, description)
    all_clean = all_clean and is_clean

print(f"\n🧪 TESTING CRITICAL IMPORTS")
print("-" * 40)

# Test the main import chain
try:
    print("1️⃣ Testing part6 import...")
    from src.downloaders.zotero_pdf_integrator_parts.part6_main_function import get_available_modes
    modes = get_available_modes()
    print(f"✅ Available modes: {modes}")
    
    if 'upload_replace' in modes:
        print("⚠️  upload_replace still in available modes!")
        all_clean = False
    
except Exception as e:
    print(f"❌ Part6 import failed: {e}")
    all_clean = False

try:
    print("2️⃣ Testing main integrator import...")
    from src.downloaders.zotero_pdf_integrator_fixed import integrate_pdfs_with_zotero_fixed
    print("✅ Main integrator imports OK")
except Exception as e:
    print(f"❌ Main integrator import failed: {e}")
    all_clean = False

try:
    print("3️⃣ Testing enhanced syncer import...")
    from src.downloaders.enhanced_literature_syncer import EnhancedZoteroLiteratureSyncer
    print("✅ Enhanced syncer imports OK")
except Exception as e:
    print(f"❌ Enhanced syncer import failed: {e}")
    print(f"📋 Error details: {str(e)}")
    all_clean = False

print(f"\n🎯 QUICK FIXES NEEDED")
print("-" * 30)

if not all_clean:
    print("❌ Issues found! Here's what to check:")
    print("1. Remove 'upload_replace' from get_available_modes() in part6")
    print("2. Remove setup_upload_replace_mode from imports in __init__.py")
    print("3. Comment out mode3_upload_and_replace_fixed references")
    print("4. Update mode validation in enhanced_literature_syncer.py")
    
    print(f"\n🔧 MANUAL CHECK LIST:")
    print("□ part6_main_function.py: get_available_modes() only returns ['download_only', 'attach']")
    print("□ __init__.py: no setup_upload_replace_mode in imports")
    print("□ enhanced_literature_syncer.py: validates only download_only/attach")
    print("□ All files compile without syntax errors")
else:
    print("✅ All files look clean!")
    print("🤔 The issue might be in the test script import line")
    print("   Make sure test script uses: from src.downloaders.enhanced_literature_syncer import ...")

print(f"\n💡 IMMEDIATE ACTION:")
print("Run this to test the direct import:")
print("python -c \"from src.downloaders.enhanced_literature_syncer import EnhancedZoteroLiteratureSyncer; print('SUCCESS')\"")