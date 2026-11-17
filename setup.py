# -*- coding: utf-8 -*-
"""py2app build script for macOS.

    pip install -U py2app pillow
    python3 setup.py py2app              # 发布用 .app（dist/PDCU MOD.app）
    python3 setup.py py2app -A           # 别名包，直接引用源码，用于对照排查

Windows 打包仍用仓库根目录的 PDCU-Season-Params.spec（PyInstaller）。
"""
import os
import shutil
import subprocess
import sys

if sys.platform != "darwin":
    raise SystemExit(
        "setup.py 只用于 macOS（py2app）；Windows 请用 "
        "python -m PyInstaller --noconfirm --clean PDCU-Season-Params.spec")

from setuptools import setup  # noqa: E402


def _detect_tcltk_dirs():
    """Return (tcl_dir, tk_dir, extra_dirs) from the active _tkinter runtime.

    py2app's built-in tkinter recipe only looks in ``<sys.prefix>/lib``, which
    misses Tcl/Tk when building from a Python 3 venv or when Tcl/Tk comes from
    a separate Homebrew keg (e.g. ``tcl-tk`` 9.x / 8.6 on Apple Silicon).
    """
    try:
        import tkinter as _tk
        interp = _tk.Tcl()
        tcl_dir = os.path.realpath(interp.eval("info library"))
    except Exception:
        return None, None, []

    if not os.path.isdir(tcl_dir):
        return None, None, []

    lib_root = os.path.dirname(tcl_dir)
    tcl_name = os.path.basename(tcl_dir)          # e.g. "tcl9.1" or "tcl8.6"
    ver = tcl_name[3:] if tcl_name.startswith("tcl") else ""
    major = tcl_name.split(".")[0]                # e.g. "tcl9" or "tcl8"
    tk_dir = os.path.join(lib_root, f"tk{ver}") if ver else ""
    if not (tk_dir and os.path.isdir(tk_dir)):
        tk_dir = None

    extras = []
    major_dir = os.path.join(lib_root, major)
    if os.path.isdir(major_dir) and major_dir != tcl_dir:
        extras.append(major_dir)
    return tcl_dir, tk_dir, extras


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
        "CFBundleShortVersionString": "2.14",
        "CFBundleVersion": "2.14.0",
        "LSMinimumSystemVersion": "10.13",
        "NSHighResolutionCapable": True,
        # 自绘深色界面：固定 Aqua 观感，避免 10.14+ 深色模式下 Tk 控件变色。
        "NSRequiresAquaSystemAppearance": True,
        "LSApplicationCategoryType": "public.app-category.photography",
    },
}

_TCL_DIR, _TK_DIR, _TCL_EXTRAS = _detect_tcltk_dirs()

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


def _make_writable(root_dir: str) -> None:
    for root, dirs, files in os.walk(root_dir):
        for name in dirs:
            p = os.path.join(root, name)
            os.chmod(p, os.stat(p).st_mode | 0o700)
        for name in files:
            p = os.path.join(root, name)
            os.chmod(p, os.stat(p).st_mode | 0o600)


def _copy_writable(src: str, dst: str) -> None:
    """Copy a directory tree (resolving symlinks) and ensure owner write bits."""
    if os.path.exists(dst):
        _make_writable(dst)
        shutil.rmtree(dst)
    shutil.copytree(src, dst, symlinks=False)
    _make_writable(dst)


def _postprocess_bundle():
    """Ensure Tcl/Tk script directories are bundled and ad-hoc sign on arm64."""
    args = set(sys.argv[1:])
    if ("py2app" not in args
            or bool(args & {"-A", "--alias", "-h", "--help", "--help-commands"})):
        return
    app_dir = os.path.join(HERE, "dist", "PDCU MOD.app")
    if not os.path.isdir(app_dir):
        return

    res_lib = os.path.join(app_dir, "Contents", "Resources", "lib")
    os.makedirs(res_lib, exist_ok=True)
    for src in [d for d in (_TCL_DIR, _TK_DIR, *_TCL_EXTRAS) if d]:
        dst = os.path.join(res_lib, os.path.basename(src))
        _copy_writable(src, dst)

    boot_py = os.path.join(app_dir, "Contents", "Resources", "__boot__.py")
    if _TCL_DIR and _TK_DIR and os.path.isfile(boot_py):
        tcl_name = os.path.basename(_TCL_DIR)
        tk_name = os.path.basename(_TK_DIR)
        with open(boot_py, "r", encoding="utf-8") as handle:
            content = handle.read()
        if "_boot_pdcu_tkinter" not in content:
            snippet = (
                "\ndef _boot_pdcu_tkinter():\n"
                "    import os\n"
                "    res = os.environ.get('RESOURCEPATH', '')\n"
                f"    tcl = os.path.join(res, 'lib', {tcl_name!r})\n"
                f"    tk = os.path.join(res, 'lib', {tk_name!r})\n"
                "    if os.path.isdir(tcl):\n"
                "        os.environ['TCL_LIBRARY'] = tcl\n"
                "    if os.path.isdir(tk):\n"
                "        os.environ['TK_LIBRARY'] = tk\n"
                "_boot_pdcu_tkinter()\n\n"
            )
            marker = "DEFAULT_SCRIPT="
            if marker in content:
                content = content.replace(marker, snippet + marker, 1)
            else:
                content += snippet
            with open(boot_py, "w", encoding="utf-8") as handle:
                handle.write(content)

    # py2app's strip step invalidates existing Mach-O signatures; Apple Silicon
    # kills unsigned/invalid-signature bundles with SIGKILL (Killed: 9).
    identity = os.environ.get("CODESIGN_IDENTITY", "-").strip() or "-"
    subprocess.run(
        ["codesign", "--deep", "--force", "--sign", identity, app_dir],
        check=True,
    )


_postprocess_bundle()
