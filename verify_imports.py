"""Verify all critical imports work correctly."""
import sys

packages = [
    'streamlit', 'langchain', 'langchain_google_genai',
    'langchain_chroma', 'langchain_community', 'chromadb',
    'google.generativeai', 'dotenv', 'pypdf', 'docx2txt',
    'pandas', 'numpy', 'requests', 'bs4', 'validators',
    'sqlalchemy', 'loguru', 'tenacity', 'tqdm', 'rich', 'nltk'
]

failed = []
for pkg in packages:
    try:
        __import__(pkg.replace('-', '_'))
        print(f"[OK] {pkg}")
    except ImportError as e:
        print(f"[FAIL] {pkg} -- FAILED: {e}")
        failed.append(pkg)

if failed:
    print(f"\n[ERROR] Failed packages: {failed}")
    sys.exit(1)
else:
    print("\n[SUCCESS] ALL PACKAGES INSTALLED SUCCESSFULLY!")
    sys.exit(0)
