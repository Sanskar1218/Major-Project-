"""Upload this project to a Hugging Face Space (handles the large model files for you, no git-lfs needed).

Usage (Windows / Mac / Linux):
    pip install -U huggingface_hub
    python deploy_to_hf.py YOUR_HF_USERNAME/ivf-embryo-predictor

Create a token at https://huggingface.co/settings/tokens (role: Write) and either run `hf auth login`
first or set the environment variable HF_TOKEN. Never paste the token into a file or a chat.
"""
import sys
from pathlib import Path
from huggingface_hub import HfApi

if len(sys.argv) != 2 or "/" not in sys.argv[1]:
    sys.exit("Usage: python deploy_to_hf.py <hf-username>/<space-name>")
repo_id = sys.argv[1]

# Only what the Gradio app needs. Old Flask files, tests, the raw dataset and training figures are left out.
IGNORE = [".git/*", ".gitignore", ".dockerignore", "Dockerfile", "run.bat", "test_server.py", "validate_app.py",
          "verify_predictions.py", "deploy_to_hf.py", "dataset.xlsx", "templates/*", "static/*", "__pycache__/*", "*.pyc",
          "outputs/outputs/figures/*", "outputs/outputs/cache/*", "outputs/outputs/*.csv", "outputs/outputs/*.zip", "*.npy", "*.npz"]

api = HfApi()
api.create_repo(repo_id, repo_type="space", space_sdk="gradio", private=False, exist_ok=True)
api.upload_folder(folder_path=str(Path(__file__).parent), repo_id=repo_id, repo_type="space",
                  ignore_patterns=IGNORE, commit_message="Deploy IVF embryo predictor")
print(f"Done. Your Space will build for a few minutes: https://huggingface.co/spaces/{repo_id}")
