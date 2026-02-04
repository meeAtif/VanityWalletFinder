import PyInstaller.__main__
import os
import shutil

APP_NAME = "VanityWalletFinder"
ICON_FILE = "icon.png"


if os.path.exists("dist"): shutil.rmtree("dist")
if os.path.exists("build"): shutil.rmtree("build")

print(f"Building {APP_NAME}...")


args = [
    'gui.py',
    f'--name={APP_NAME}',
    '--onefile',
    '--noconsole',
    '--hidden-import=bip_utils',
    '--hidden-import=coincurve',
    '--hidden-import=PIL',
    '--collect-all=customtkinter',
    '--collect-all=bip_utils',
    '--clean',
]


if os.path.exists(ICON_FILE):
    print(f"Found icon: {ICON_FILE}")
    args.append(f'--icon={ICON_FILE}')
else:
    print(f"No icon found at {ICON_FILE}. Using default icon.")


PyInstaller.__main__.run(args)

print("\n" + "="*30)
print(f"Build complete! Executable is in the 'dist' folder.")
print(f"You can rename 'dist/{APP_NAME}.exe' to '{APP_NAME}_v1.1.exe' if you like.")
print("="*30)
