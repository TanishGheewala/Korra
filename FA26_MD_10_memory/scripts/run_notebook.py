"""Execute a notebook with real provider calls, preserving partial output on failure."""
import os
from pathlib import Path
import sys
import nbformat
from nbclient import NotebookClient

root = Path(__file__).resolve().parents[1]
source = root / (sys.argv[1] if len(sys.argv) > 1 else "S1/Persistence_Streaming_Demo.ipynb")
notebook = nbformat.read(source, as_version=4)
destination = source.with_name(source.stem + "_Completed.ipynb")
os.chdir(root)
try:
    NotebookClient(notebook, timeout=180, kernel_name="python3", resources={"metadata": {"path": str(root)}}).execute()
finally:
    nbformat.write(notebook, destination)
print(f"Executed notebook saved to {destination}")
