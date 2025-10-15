import os
import shutil
import json
import re
from pathlib import Path
import subprocess

# === 配置路径 ===
input_dir = Path("input")
output_dir = Path("output")
temp_dir = Path("temp")

output_dir.mkdir(exist_ok=True)
temp_dir.mkdir(exist_ok=True)

# 用于记录失败项
failed_items = []

def sanitize_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', ' ', name)
    name = name.strip().strip('.')
    if len(name) > 100:
        name = name[:100]
    return name or "unnamed"

def remove_header_in_place(file_path: Path, header_size=9):
    with open(file_path, 'rb') as f:
        f.seek(header_size)
        data = f.read()
    with open(file_path, 'wb') as f:
        f.write(data)

def get_m4s_files(folder: Path):
    m4s_files = list(folder.glob("*.m4s"))
    if len(m4s_files) != 2:
        return None, None
    m4s_files.sort(key=lambda x: x.stat().st_size, reverse=True)
    return m4s_files[0], m4s_files[1]

def run_ffmpeg(cmd):
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def merge_videos_in_folder(original_folder: Path):
    folder_name = original_folder.name
    print(f"📦 处理: {folder_name}")

    # === 读取标题 ===
    video_info_path = original_folder / 'videoInfo.json'
    if video_info_path.exists():
        try:
            with open(video_info_path, 'r', encoding='utf-8') as f:
                info = json.load(f)
                group_title = info.get('groupTitle', '')
                title = info.get('title', '')
        except Exception as e:
            print(f"⚠️ JSON 解析失败: {e}")
            group_title, title = "", folder_name
    else:
        group_title, title = "", folder_name

    group_title = sanitize_filename(group_title)
    title = sanitize_filename(title)
    if group_title == title:
        base_name = title
    else:
        base_name = f"{group_title}-{title}" if group_title and title else (title or group_title or folder_name)
    output_file = output_dir / f"{base_name}.mp4"

    # === 创建临时副本 ===
    work_folder = temp_dir / folder_name
    if work_folder.exists():
        shutil.rmtree(work_folder)
    shutil.copytree(original_folder, work_folder)

    # === 获取 m4s 文件 ===
    video_m4s, audio_m4s = get_m4s_files(work_folder)
    if not video_m4s or not audio_m4s:
        print(f"⚠️ 跳过 {folder_name}：非标准 .m4s 结构")
        failed_items.append(f"{base_name}（结构异常）")
        shutil.rmtree(work_folder, ignore_errors=True)
        return

    # === 去头 ===
    remove_header_in_place(video_m4s, 9)
    remove_header_in_place(audio_m4s, 9)

    # === 合并 ===
    cmd = [
        "ffmpeg", "-i", str(video_m4s),
        "-i", str(audio_m4s),
        "-c", "copy",
        "-y",
        str(output_file)
    ]

    if run_ffmpeg(cmd):
        print(f"✅ 成功: {output_file.name}")
    else:
        print(f"❌ 合并失败: {base_name}")
        failed_items.append(base_name)

    # === 清理 ===
    shutil.rmtree(work_folder, ignore_errors=True)

# === 主程序 ===
if __name__ == "__main__":
    if not input_dir.exists():
        print(f"❌ input 目录不存在: {input_dir}")
        exit(1)

    folders = [f for f in input_dir.iterdir() if f.name.isdigit() and f.is_dir()]
    print(f"🔍 找到 {len(folders)} 个待处理文件夹")

    for folder in sorted(folders, key=lambda x: int(x.name)):
        merge_videos_in_folder(folder)

    # === 最终汇总 ===
    print("\n" + "="*50)
    if failed_items:
        print(f"⚠️  共有 {len(failed_items)} 个视频未成功转换：")
        for item in failed_items:
            print(f"  • {item}")
    else:
        print("🎉 所有视频均已成功转换！")

    print("="*50)