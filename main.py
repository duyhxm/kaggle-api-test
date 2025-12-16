# -*- coding: utf-8 -*-
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
        print(result.decode("utf-8"))
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.output.decode('utf-8')}")
        return False


def list_files(startpath):
    """Print directory tree to verify uploaded files"""
    print("\n" + "=" * 40)
    print(f"[DIR] DIRECTORY STRUCTURE CHECK AT: {os.path.abspath(startpath)}")
    print("=" * 40)
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, "").count(os.sep)
        indent = " " * 4 * (level)
        print(f"{indent}[+] {os.path.basename(root)}/")
        subindent = " " * 4 * (level + 1)
        for f in files:
            print(f"{subindent}[-] {f}")
    print("=" * 40 + "\n")


def setup_and_push_git():
    print("[START] Starting Git Push test process...")

    github_token = None

    # Try Method 1: Read from attached dataset (Best practice for API)
    try:
        # Lưu ý: Tên thư mục trong /kaggle/input thường thay dấu '-' thành '_'
        # Hãy kiểm tra kỹ đường dẫn thực tế bằng lệnh ls nếu cần
        token_path = "/kaggle/input/github-credentials/github_token.txt"

        # Fallback check nếu người dùng đặt tên khác
        if not os.path.exists(token_path):
            # Thử tìm trong thư mục gốc input nếu dataset cấu trúc phẳng
            token_path = "/kaggle/input/github_token.txt"

        if os.path.exists(token_path):
            with open(token_path, "r") as f:
                github_token = f.read().strip()
            print("[SUCCESS] GITHUB_TOKEN loaded from dataset")
    except Exception as e:
        print(f"[WARN] Could not read token from dataset: {e}")

    # Try Method 2: Kaggle Secrets (Fallback for Web UI)
    if not github_token:
        try:
            user_secrets = UserSecretsClient()
            github_token = user_secrets.get_secret("GITHUB_TOKEN")
            print("[SUCCESS] GITHUB_TOKEN loaded from Secrets")
        except Exception as secret_error:
            print(
                f"[ERROR] Could not retrieve GITHUB_TOKEN from Secrets: {secret_error}"
            )

    if not github_token:
        print("[CRITICAL] GITHUB_TOKEN not found! Process aborted.")
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

    # --- NEW: SYNC HISTORY (Quan trọng để không mất commit cũ) ---
    print("[GIT] Fetching history to preserve local commits...")
    run_cmd("git fetch origin main")
    # Reset mixed giúp Git nhận diện code hiện tại là sự tiếp nối của main
    run_cmd("git reset --mixed origin/main")

    # --- NEW: VERIFY OUTPUT LOCATION (data/) ---
    print("[TEST] Creating proof file inside 'data/' directory...")
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    proof_file = os.path.join(output_dir, "kaggle_proof.txt")

    with open(proof_file, "w", encoding="utf-8") as f:
        f.write(f"Verified output location control at {timestamp}\n")
        f.write(f"This file is located at: {os.path.abspath(proof_file)}\n")
        f.write("Status: SUCCESS. You can now point DVC to this folder.")

    # Commit and Push
    run_cmd(f"git checkout -b {BRANCH_NAME}")
    run_cmd("git add .")
    run_cmd(
        f"git commit -m 'Verify output path control: data/kaggle_proof.txt at {timestamp}'"
    )

    print(f"[PUSH] Pushing code to branch '{BRANCH_NAME}'...")
    # Bỏ cờ -f (force) vì lịch sử đã được sync
    success = run_cmd(f"git push origin {BRANCH_NAME}")

    if success:
        print("\n[SUCCESS] Check GitHub! Look for 'data/kaggle_proof.txt'.")
    else:
        print("\n[FAILED] Check the error log above.")


if __name__ == "__main__":
    # Step 1: Check if local files were uploaded correctly
    list_files(".")

    # Step 2: Test push back to Github with History & Output verification
    setup_and_push_git()
