import os
import subprocess
import sys
from datetime import datetime

from kaggle_secrets import UserSecretsClient

# --- Cấu hình GitHub của bạn ---
GITHUB_USERNAME = "duyhxm"
REPO_NAME = "kaggle-api-test"  # Đổi tên repo nếu bạn dùng repo khác
BRANCH_NAME = "verify-kaggle-push"  # Tên nhánh test sẽ được tạo


def run_cmd(cmd):
    """Hàm chạy lệnh shell và in kết quả"""
    print(f"Exec: {cmd}")
    try:
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        print(result.decode("utf-8"))
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e.output.decode('utf-8')}")
        return False


def list_files(startpath):
    """In ra cây thư mục để kiểm chứng file đã được upload lên chưa"""
    print("\n" + "=" * 40)
    print(f"📂 KIỂM TRA CẤU TRÚC THƯ MỤC TẠI: {os.path.abspath(startpath)}")
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
    print("🚀 Bắt đầu quy trình test Git Push...")

    # 1. Lấy Token (Bắt buộc phải set trong Kaggle Secrets trước)
    try:
        user_secrets = UserSecretsClient()
        # Lưu ý: Bạn phải chắc chắn tên Secret trên Web là 'GITHUB_TOKEN'
        github_token = user_secrets.get_secret("GITHUB_TOKEN")
    except Exception as e:
        print(
            "❌ LỖI: Không lấy được GITHUB_TOKEN từ Secrets. Bạn đã Add-ons -> Secrets chưa?"
        )
        print(f"Chi tiết: {e}")
        return

    # 2. Setup Git User
    run_cmd("git config --global user.email 'bot@kaggle.com'")
    run_cmd("git config --global user.name 'Kaggle Verify Bot'")

    # 3. Khởi tạo Git (Vì .git không được push lên, ta phải init lại)
    if not os.path.exists(".git"):
        run_cmd("git init")

    # 4. Thêm Remote (Có chứa Token để xác thực)
    remote_url = f"https://{GITHUB_USERNAME}:{github_token}@github.com/{GITHUB_USERNAME}/{REPO_NAME}.git"
    # Xóa remote cũ nếu có để tránh lỗi
    run_cmd("git remote remove origin")
    run_cmd(f"git remote add origin {remote_url}")

    # 5. Tạo file bằng chứng (Proof)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    proof_file = "kaggle_proof.txt"
    with open(proof_file, "w") as f:
        f.write(f"Verified from Kaggle at {timestamp}\n")
        f.write("Nếu bạn đọc được dòng này trên Github nghĩa là: \n")
        f.write("1. Toàn bộ code đã lên Kaggle.\n")
        f.write("2. Kaggle đã push ngược lại thành công.")

    # 6. Commit và Push
    run_cmd(f"git checkout -b {BRANCH_NAME}")
    run_cmd("git add .")
    run_cmd(f"git commit -m 'Test push from Kaggle API at {timestamp}'")

    print(f"📡 Đang đẩy code lên branch '{BRANCH_NAME}'...")
    success = run_cmd(f"git push -f origin {BRANCH_NAME}")

    if success:
        print("\n✅ THÀNH CÔNG! Hãy kiểm tra GitHub của bạn ngay.")
    else:
        print("\n❌ THẤT BẠI. Hãy xem log lỗi ở trên.")


if __name__ == "__main__":
    # Bước 1: Kiểm tra xem file local có lên đây đủ không
    list_files(".")

    # Bước 2: Test bắn ngược về Github
    setup_and_push_git()
