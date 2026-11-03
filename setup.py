# -*- coding: utf-8 -*-
"""py2app build script for macOS.

    pip install -U py2app pillow
    python3 setup.py py2app              # 发布用 .app（dist/PDCU MOD.app）
    python3 setup.py py2app -A           # 别名包，直接引用源码，用于对照排查

Windows 打包仍用仓库根目录的 PDCU-Season-Params.spec（PyInstaller）。
"""
import os
import sys

if sys.platform != "darwin":
    raise SystemExit(
        "setup.py 只用于 macOS（py2app）；Windows 请用 "
        "python -m PyInstaller --noconfirm --clean PDCU-Season-Params.spec")

from setuptools import setup  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = ("pdcu_mod_logo_96.png", "spring.png", "summer.png",
          "autumn.png", "winter.png")
DATA_FILES = [
    ("assets", [os.path.join("tools", "assets", name) for name in ASSETS]),
    ("", ["tools/season.ico"]),
]

OPTIONS = {
    # 本工具不用 Apple Event 打开文件，别名包也用不到它。
    "argv_emulation": False,
    # Pillow 是预览的唯一硬依赖：整包带入，别让 modulegraph 猜。
    "packages": ["PIL"],
    "includes": ["PIL.Image", "PIL.ImageTk", "PIL.JpegImagePlugin",
                 "PIL.PngImagePlugin"],
    "excludes": ["numpy", "scipy", "matplotlib", "tkinter.test", "test"],
    "plist": {
        "CFBundleName": "PDCU MOD",
        "CFBundleDisplayName": "PDCU MOD",
        "CFBundleShortVersionString": "2.12",
        "CFBundleVersion": "2.12.0",
        "LSMinimumSystemVersion": "10.13",
        "NSHighResolutionCapable": True,
        # 自绘深色界面：固定 Aqua 观感，避免 10.14+ 深色模式下 Tk 控件变色。
        "NSRequiresAquaSystemAppearance": True,
        "LSApplicationCategoryType": "public.app-category.photography",
    },
}

# 图标必须是 .icns：tools/season.icns 由 tools/make_icns.py 从 logo 生成。
ICON = os.path.join(HERE, "tools", "season.icns")
if os.path.exists(ICON):
    OPTIONS["iconfile"] = ICON

# 目标架构。默认跟随当前 Python 解释器（在 Apple Silicon 上打包就是 arm64，
# 在 Intel 上打包就是 x86_64）。也可以显式指定：
#     PDCU_ARCH=arm64 python3 setup.py py2app
#     PDCU_ARCH=universal2 python3 setup.py py2app
# 注意：universal2 要求 Python、Tcl/Tk、Pillow 本身都是 universal2，
# 否则 py2app 会失败或产出仍是单架构——以 tools/check_macos_bundle.py
# 打印的 lipo 结果为准。
ARCH = os.environ.get("PDCU_ARCH", "").strip()
if ARCH:
    OPTIONS["arch"] = ARCH

setup(
    name="PDCU MOD",
    app=["tools/dng_season_gui.py"],
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
)
