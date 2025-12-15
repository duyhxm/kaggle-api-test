import os
import subprocess
import sys
from datetime import datetime

from kaggle_secrets import UserSecretsClient

# --- Configuration ---
GITHUB_USERNAME = "duyhxm"
REPO_NAME = "kaggle-api-test"
BRANCH_NAME = "verify-kaggle-push"


def run_cmd(cmd):
    """Execute shell command and print result"""
    print(f"Exec: {cmd}")
    try:
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        print(result.decode("utf-8", errors="replace"))
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e.output.decode('utf-8', errors='replace')}")
        return False


def list_files(startpath):
    """Print directory tree to verify uploaded files"""
    print("\n" + "=" * 40)
    print(f"📂 DIRECTORY STRUCTURE CHECK AT: {os.path.abspath(startpath)}")
    print("=" * 40)
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, "").count(os.sep)
        indent = " " * 4 * (level)
        print(f"{indent}📁 {os.path.basename(root)}/")
        subindent = " " * 4 * (level + 1)
        for f in files:
            print(f"{subindent}📄 {f}")
    print("=" * 40 + "\n")


def setup_and_push_git():
    print("🚀 Starting Git Push test process...")

    try:
        user_secrets = UserSecretsClient()
        github_token = user_secrets.get_secret("GITHUB_TOKEN")
    except Exception as e:
        print(
            "❌ ERROR: Could not retrieve GITHUB_TOKEN from Secrets. Did you set it in Add-ons -> Secrets?"
        )
        print(f"Details: {e}")
        return

    # Configure Git User
    run_cmd("git config --global user.email 'bot@kaggle.com'")
    run_cmd("git config --global user.name 'Kaggle Verify Bot'")

    # Initialize Git
    if not os.path.exists(".git"):
        run_cmd("git init")

    # Configure Remote
    remote_url = f"https://{GITHUB_USERNAME}:{github_token}@github.com/{GITHUB_USERNAME}/{REPO_NAME}.git"
    run_cmd("git remote remove origin")
    run_cmd(f"git remote add origin {remote_url}")

    # Create Proof File
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    proof_file = "kaggle_proof.txt"
    with open(proof_file, "w", encoding="utf-8") as f:
        f.write(f"Verified from Kaggle at {timestamp}\n")
        f.write("If you are reading this on Github, it means: \n")
        f.write("1. All code has been successfully uploaded to Kaggle.\n")
        f.write("2. Kaggle has successfully pushed back to GitHub.")

    # Commit and Push
    run_cmd(f"git checkout -b {BRANCH_NAME}")
    run_cmd("git add .")
    run_cmd(f"git commit -m 'Test push from Kaggle API at {timestamp}'")

    print(f"📡 Pushing code to branch '{BRANCH_NAME}'...")
    success = run_cmd(f"git push -f origin {BRANCH_NAME}")

    if success:
        print("\n✅ SUCCESS! Check your GitHub immediately.")
    else:
        print("\n❌ FAILED. Check the error log above.")


if __name__ == "__main__":
    # Step 1: Check if local files were uploaded correctly
    list_files(".")

    # Step 2: Test push back to Github
    setup_and_push_git()
