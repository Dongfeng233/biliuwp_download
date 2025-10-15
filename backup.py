import os
import shutil
from pathlib import Path

# 配置路径
input_dir = Path("bilibili")           # 被污染的目录（将被覆盖恢复）
backup_dir = Path("output")  # 干净的备份源

def is_digit_folder(path: Path) -> bool:
    """判断是否为纯数字命名的文件夹"""
    return path.is_dir() and path.name.isdigit()

def restore_folders():
    if not backup_dir.exists():
        print(f"❌ 备份目录 '{backup_dir}' 不存在！")
        return

    input_dir.mkdir(exist_ok=True)  # 确保 input 存在

    # 获取 input 中所有数字文件夹的名字（作为“要恢复的列表”）
    target_names = {
        item.name for item in input_dir.iterdir()
        if is_digit_folder(item)
    }

    if not target_names:
        print("⚠️ input 目录中没有找到任何纯数字命名的文件夹，无内容可恢复。")
        return

    print(f"🔍 找到 {len(target_names)} 个需要恢复的文件夹: {sorted(target_names)}")

    restored = 0
    for name in sorted(target_names):
        src = backup_dir / name
        dst = input_dir / name

        if not src.exists():
            print(f"⚠️ 跳过 {name}：backup 中不存在")
            continue

        # 删除 input 中旧的（被污染的）文件夹
        if dst.exists():
            shutil.rmtree(dst)

        # 从 backup 拷贝完整文件夹过来
        shutil.copytree(src, dst)
        print(f"✅ 已恢复: {name}")
        restored += 1

    print(f"\n🎉 共成功恢复 {restored} 个文件夹。")

if __name__ == "__main__":
    restore_folders()