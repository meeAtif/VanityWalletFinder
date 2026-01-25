import PyInstaller.__main__
import os
import shutil

# Clean previous builds
if os.path.exists("dist"): shutil.rmtree("dist")
if os.path.exists("build"): shutil.rmtree("build")

print("Building executable...")

PyInstaller.__main__.run([
    'gui.py',
    '--name=VanityWalletFinder',
    '--onefile',
    '--noconsole',
    '--hidden-import=bip_utils',
    '--hidden-import=coincurve',
    '--hidden-import=PIL',
    '--collect-all=customtkinter',
    '--collect-all=bip_utils',
    '--clean',
])

print("Build complete. Check 'dist' folder.")
