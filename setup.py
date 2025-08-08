"""
Setup script for building Semantic Search Assistant executable
"""
import sys
from cx_Freeze import setup, Executable
import os

# Dependencies are automatically detected, but it might need fine tuning.
build_options = {
    'packages': [
        'asyncio', 'uvicorn', 'fastapi', 'lancedb', 'sentence_transformers',
        'PyPDF2', 'fitz', 'docx', 'markdown', 'bs4', 'langchain', 'pandas',
        'numpy', 'pyarrow', 'watchdog', 'aiofiles', 'multipart', 'psutil',
        'pyperclip', 'keyboard', 'pyautogui', 'win32api', 'win32con', 'win32gui',
        'win32clipboard', 'tkinter', 'threading', 'json', 'pathlib', 'logging',
        'sqlite3', 'urllib', 'http', 'email', 'xml', 'html', 'winreg'
    ],
    'excludes': ['test', 'unittest', 'pydoc', 'doctest'],
    'include_files': [
        'config.json',
        'requirements.txt',
    ],
    'zip_include_packages': ['*'],
    'zip_exclude_packages': []
}

# GUI applications require a different base on Windows (the default is for a console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

executables = [
    Executable(
        'enhanced_global_monitor.py',
        base=base,
        target_name='SemanticSearchAssistant.exe',
        icon=None  # You can add an icon file here if you have one
    )
]

setup(
    name='Semantic Search Assistant',
    version='1.0.0',
    description='Professional Semantic Search Assistant with Highlight Capture',
    author='Your Name',
    options={'build_exe': build_options},
    executables=executables
)
