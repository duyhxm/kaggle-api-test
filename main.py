# -*- coding: utf-8 -*-
import os
import subprocess
import sys
from datetime import datetime

from kaggle_secrets import UserSecretsClient

# --- Configuration ---
GITHUB_USERNAME = "duyhxm"
REPO_NAME = "kaggle-api-test"


def run_cmd(cmd):
    """Execute shell command and print result"""
    print(f"[EXEC] {cmd}")
    try:
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        print(result.decode("utf-8"))
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {e.output.decode('utf-8')}")
        return False


def list_files(startpath):
    """Print directory tree to verify uploaded files"""
    print("\n" + "=" * 60)
    print(f"[DIR] DIRECTORY STRUCTURE CHECK AT: {os.path.abspath(startpath)}")
    print("=" * 60)
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, "").count(os.sep)
        indent = " " * 4 * (level)
        print(f"{indent}[+] {os.path.basename(root)}/")
        subindent = " " * 4 * (level + 1)
        for f in files:
            print(f"{subindent}[-] {f}")
    print("=" * 60 + "\n")


def setup_and_push_git():
    print("[START] Starting Git workflow - Clone, Process, Push...")

    # --- 1. GET TOKEN ---
    github_token = None
    try:
        # Try Method 1: Read from attached dataset
        token_path = "/kaggle/input/github-credentials/github_token.txt"

        # Fallback check
        if not os.path.exists(token_path):
            token_path = "/kaggle/input/github_token.txt"

        if os.path.exists(token_path):
            with open(token_path, "r") as f:
                github_token = f.read().strip()
            print("[SUCCESS] GITHUB_TOKEN loaded from dataset")
    except Exception as e:
        print(f"[WARN] Could not read token from dataset: {e}")

    # Try Method 2: Kaggle Secrets
    if not github_token:
        try:
            user_secrets = UserSecretsClient()
            github_token = user_secrets.get_secret("GITHUB_TOKEN")
            print("[SUCCESS] GITHUB_TOKEN loaded from Secrets")
        except Exception as secret_error:
            print(
                f"[WARN] Could not retrieve GITHUB_TOKEN from Secrets: {secret_error}"
            )

    if not github_token:
        print("[CRITICAL] GITHUB_TOKEN not found! Process aborted.")
        return

    # --- 2. SETUP GIT CONFIG ---
    print("[GIT] Configuring Git identity...")
    run_cmd("git config --global user.email 'bot@kaggle.com'")
    run_cmd("git config --global user.name 'Kaggle Verify Bot'")

    # --- 3. CLONE REPO FROM GITHUB ---
    repo_url = f"https://{GITHUB_USERNAME}:{github_token}@github.com/{GITHUB_USERNAME}/{REPO_NAME}.git"
    work_dir = "/kaggle/working/repo"

    print(f"[GIT] Cloning repository from GitHub...")
    print(f"[INFO] Target directory: {work_dir}")

    # Remove if exists (for re-run scenarios)
    if os.path.exists(work_dir):
        run_cmd(f"rm -rf {work_dir}")

    # Clone the repository
    clone_success = run_cmd(f"git clone {repo_url} {work_dir}")
    if not clone_success:
        print("[CRITICAL] Failed to clone repository!")
        return

    # Change to repo directory
    os.chdir(work_dir)
    print(f"[INFO] Changed working directory to: {os.getcwd()}")

    # --- 4. GENERATE DYNAMIC BRANCH ---
    current_time_str = datetime.now().strftime("%Y%m%d-%H%M%S")
    branch_name = f"kaggle-run-{current_time_str}"
    print(f"[INFO] Creating new branch: {branch_name}")

    run_cmd(f"git checkout -b {branch_name}")

    # --- 5. CREATE OUTPUT FILES ---
    print("[PROCESS] Generating experiment outputs...")
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)

    timestamp_readable = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Create run log
    log_file = os.path.join(output_dir, f"run_{current_time_str}.txt")
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"=" * 60 + "\n")
        f.write(f"Kaggle Experiment Run Log\n")
        f.write(f"=" * 60 + "\n")
        f.write(f"Run ID: {branch_name}\n")
        f.write(f"Execution Time: {timestamp_readable}\n")
        f.write(f"Repository: {GITHUB_USERNAME}/{REPO_NAME}\n")
        f.write(f"Working Directory: {os.getcwd()}\n")
        f.write(f"Output File: {os.path.abspath(log_file)}\n")
        f.write(f"\n")
        f.write(f"Status: Successfully executed on Kaggle platform\n")
        f.write(f"=" * 60 + "\n")

    print(f"[SUCCESS] Created output file: {log_file}")

    # Create a summary file
    summary_file = os.path.join(output_dir, "latest_run.txt")
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write(f"Latest Run: {branch_name}\n")
        f.write(f"Time: {timestamp_readable}\n")

    print(f"[SUCCESS] Created summary file: {summary_file}")

    # --- 6. COMMIT AND PUSH ---
    print("[GIT] Staging changes...")
    run_cmd("git add .")

    print("[GIT] Committing changes...")
    commit_msg = f"Kaggle experiment run: {current_time_str}"
    run_cmd(f'git commit -m "{commit_msg}"')

    print(f"[GIT] Pushing to branch '{branch_name}'...")
    push_success = run_cmd(f"git push origin {branch_name}")

    # --- 7. FINAL REPORT ---
    if push_success:
        print("\n" + "=" * 60)
        print("[SUCCESS] Workflow completed successfully!")
        print("=" * 60)
        print(f"Branch created: {branch_name}")
        print(f"Repository: https://github.com/{GITHUB_USERNAME}/{REPO_NAME}")
        print(
            f"View branch: https://github.com/{GITHUB_USERNAME}/{REPO_NAME}/tree/{branch_name}"
        )
        print(f"Output files created in 'data/' directory")
        print("=" * 60)
    else:
        print("\n[FAILED] Push failed. Check the error log above.")


if __name__ == "__main__":
    # Step 1: Check directory structure
    list_files(".")

    # Step 2: Run Git Push process
    setup_and_push_git()
