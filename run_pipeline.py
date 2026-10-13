"""Run preprocessing and model training in the correct order."""
from pathlib import Path
import subprocess
import sys

PROJECT_DIR = Path(__file__).resolve().parent
for script in ("preprocess.py", "train_model.py"):
    print(f"\n=== Running {script} ===", flush=True)
    subprocess.run([sys.executable, str(PROJECT_DIR / script)], cwd=PROJECT_DIR, check=True)
print("\nPipeline complete. Start the app with: streamlit run app.py")
