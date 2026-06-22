"""调用 Inno Setup 编译器(ISCC)打包安装程序。

独立脚本，避免 Git Bash 内联 -c 的参数/编码问题。
用法：python tools/build_installer.py

注意：Inno Setup 的 SetupIconFile 读取器不支持 PNG 压缩的 ICO 条目，
而 Pillow 默认导出 PNG 编码的 ICO，故本脚本在临时目录生成一份 BMP
编码的同款图标供安装包使用，不改动仓库内的 src/assets/app.ico。
"""

import importlib.util
import os
import subprocess
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.join(PROJECT_DIR, "tools")

ISCC_CANDIDATES = [
    r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    r"C:\Program Files\Inno Setup 6\ISCC.exe",
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Inno Setup 6", "ISCC.exe"),
]


def find_iscc():
    for p in ISCC_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


def find_iss():
    """扫描目录取真实文件名，避免硬编码中文名的字节匹配问题。"""
    for f in os.listdir(PROJECT_DIR):
        if f.endswith(".iss"):
            return f
    return None


def make_bmp_icon():
    """用 make_icon.py 的绘制逻辑生成 BMP 编码图标到临时路径，返回绝对路径。"""
    spec = importlib.util.spec_from_file_location(
        "make_icon", os.path.join(TOOLS_DIR, "make_icon.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    out = os.path.join(TOOLS_DIR, "_installer_icon.ico")
    img = mod.build()
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(out, format="ICO", sizes=sizes, bitmap_format="bmp")
    return out


def safe_print(text=""):
    encoding = sys.stdout.encoding or "utf-8"
    print(str(text).encode(encoding, errors="replace").decode(encoding))


def main():
    iscc = find_iscc()
    if not iscc:
        print("找不到 ISCC.exe，请确认 Inno Setup 6 已安装")
        return 2

    iss_name = find_iss()
    if not iss_name:
        print("目录下找不到 .iss 脚本:", PROJECT_DIR)
        return 2

    bmp_icon = make_bmp_icon()

    # 读取原 iss，把 SetupIconFile 指向 BMP 图标（绝对路径），写入临时 iss
    src_iss = os.path.join(PROJECT_DIR, iss_name)
    with open(src_iss, "r", encoding="utf-8") as f:
        lines = f.readlines()
    new_lines = []
    for ln in lines:
        if ln.strip().startswith("SetupIconFile="):
            new_lines.append("SetupIconFile=" + bmp_icon + "\n")
        else:
            new_lines.append(ln)
    tmp_iss = os.path.join(PROJECT_DIR, "_build_tmp.iss")
    with open(tmp_iss, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    safe_print(f"ISCC : {iscc}")
    safe_print(f"脚本 : {iss_name} (临时副本 _build_tmp.iss)")
    safe_print(f"图标 : BMP 编码临时图标 {bmp_icon}")
    safe_print("-" * 50)

    try:
        # 经 cmd.exe 启动 ISCC：本机直接 CreateProcess 该 exe 间歇 WinError 2，
        # 而 cmd.exe 在 system32，作启动器可稳定拉起 ISCC
        result = subprocess.run(
            ["cmd", "/c", iscc, "_build_tmp.iss"],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            encoding="mbcs",
            errors="replace",
        )
        safe_print(result.stdout or "")
        if result.stderr:
            safe_print("--- STDERR ---")
            safe_print(result.stderr)
    finally:
        for p in (tmp_iss, bmp_icon):
            try:
                os.remove(p)
            except OSError:
                pass

    safe_print("-" * 50)
    safe_print(f"返回码: {result.returncode}")
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
