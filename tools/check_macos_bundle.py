#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnose why a built .app will not start on a Mac.

    python3 tools/check_macos_bundle.py "dist/PDCU MOD.app"

Walks the bundle, reports the architecture of every Mach-O binary and whether
the code is signed, then compares that with the machine it runs on and prints
the concrete next step (install Rosetta, rebuild for arm64, sign the bundle).

Only the scan needs macOS; the decision logic in `evaluate()` is plain data so
it can be tested on any host (see tests/test_macos_bundle_check.py).
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Thin-ish Mach-O magics; FAT magics carry the same information via lipo.
MACHO_MAGICS = {
    b"\xfe\xed\xfa\xce", b"\xce\xfa\xed\xfe",     # 32-bit BE/LE
    b"\xfe\xed\xfa\xcf", b"\xcf\xfa\xed\xfe",     # 64-bit BE/LE
    b"\xca\xfe\xba\xbe", b"\xbe\xba\xfe\xca",     # FAT
    b"\xca\xfe\xba\xbf", b"\xbf\xba\xfe\xca",     # FAT64
}

ARM64 = "arm64"


# ---------------------------------------------------------------- pure logic

def parse_archs(text: str) -> set[str]:
    """'x86_64 arm64' / 'Non-fat file: ... is architecture: arm64' -> set."""
    tokens = set()
    for word in (text or "").replace(":", " ").split():
        if word in ("x86_64", "arm64", "arm64e", "i386", "ppc", "ppc64"):
            tokens.add("arm64" if word == "arm64e" else word)
    return tokens


def parse_version(text: str) -> tuple[int, int]:
    """'10.13.6' -> (10, 13); unparsable -> (0, 0)."""
    parts = []
    for chunk in (text or "").strip().split(".")[:2]:
        digits = "".join(ch for ch in chunk if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    while len(parts) < 2:
        parts.append(0)
    return parts[0], parts[1]


def evaluate(host_arch: str, host_os: str, bundle_archs: set[str],
             signed: bool, min_os: str | None,
             rosetta: bool | None = None) -> list[dict]:
    """Return findings; each is {'level': 'block'|'warn'|'note', 'text': str}."""
    findings: list[dict] = []
    archs = set(bundle_archs)

    if not archs:
        findings.append({"level": "warn",
                         "text": "bundle 里没找到可识别的 Mach-O，"
                                 "可能不是 .app 或打包失败"})
        return findings

    if host_arch == ARM64 and ARM64 not in archs:
        if "x86_64" in archs:
            if rosetta is False:
                findings.append({
                    "level": "block",
                    "text": "这个 .app 只有 x86_64，本机是 Apple Silicon 且未装 "
                            "Rosetta 2：先在终端跑 "
                            "`softwareupdate --install-rosetta --agree-to-license`，"
                            "或者在 Apple Silicon 机器上重新打包（会得到 arm64）"})
            elif rosetta is True:
                findings.append({
                    "level": "warn",
                    "text": "这个 .app 只有 x86_64，靠 Rosetta 2 运行；"
                            "要原生速度就在 Apple Silicon 机器上重新打包"})
            else:
                findings.append({
                    "level": "warn",
                    "text": "这个 .app 只有 x86_64，在 Apple Silicon 上需要 "
                            "Rosetta 2（系统首次运行时会提示安装）"})
        else:
            findings.append({"level": "block",
                             "text": "bundle 二进制不含 arm64 / x86_64：%s"
                                     % sorted(archs)})

    if host_arch == ARM64 and not signed:
        findings.append({
            "level": "block",
            "text": "Apple Silicon 要求所有可执行代码至少 ad-hoc 签名；"
                    "未签名会被系统直接终止（Killed: 9）。运行："
                    "codesign --deep --force --sign - \"dist/PDCU MOD.app\""})

    if min_os:
        if parse_version(min_os) > parse_version(host_os):
            findings.append({
                "level": "block",
                "text": "Info.plist 的 LSMinimumSystemVersion=%s 高于本机 %s"
                        % (min_os, host_os)})

    if not findings:
        findings.append({"level": "note", "text": "架构与签名对得上，应该能启动"})
    return findings


def verdict(findings: list[dict]) -> str:
    levels = {item["level"] for item in findings}
    if "block" in levels:
        return "blocked"
    if "warn" in levels:
        return "warning"
    return "ok"


# ---------------------------------------------------------------- macOS scan

def _run(args: list[str]) -> tuple[int, str]:
    try:
        done = subprocess.run(args, capture_output=True, text=True, timeout=60)
        return done.returncode, (done.stdout + done.stderr).strip()
    except (OSError, subprocess.SubprocessError) as exc:
        return 1, str(exc)


def is_macho(path: Path) -> bool:
    try:
        with open(path, "rb") as handle:
            return handle.read(4) in MACHO_MAGICS
    except OSError:
        return False


def find_binaries(app: Path) -> list[Path]:
    found = []
    for root, _dirs, files in os.walk(app):
        for name in files:
            candidate = Path(root) / name
            if os.path.islink(candidate):
                continue
            if is_macho(candidate):
                found.append(candidate)
    return sorted(found)


def binary_archs(path: Path) -> set[str]:
    code, out = _run(["lipo", "-archs", str(path)])
    if code == 0:
        return parse_archs(out)
    code, out = _run(["file", "-b", str(path)])
    return parse_archs(out) if code == 0 else set()


def is_signed(path: Path) -> bool:
    code, _out = _run(["codesign", "-dv", str(path)])
    return code == 0


def plist_min_os(app: Path) -> str | None:
    plist = app / "Contents" / "Info.plist"
    if not plist.is_file():
        return None
    try:
        import plistlib
        with open(plist, "rb") as handle:
            data = plistlib.load(handle)
    except Exception:
        return None
    value = data.get("LSMinimumSystemVersion")
    return str(value) if value else None


def rosetta_installed() -> bool | None:
    if not os.path.exists("/Library/Apple/usr/libexec/oah"):
        return False
    return True


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("app", nargs="?",
                        default=os.path.join("dist", "PDCU MOD.app"))
    args = parser.parse_args(argv)

    if sys.platform != "darwin":
        print("这个脚本要在 macOS 上跑；在 Windows 上只能跑 "
              "tests/test_macos_bundle_check.py")
        return 2

    app = Path(args.app).expanduser()
    if not app.is_dir():
        print("找不到 .app：%s" % app)
        return 2

    host_arch = _run(["uname", "-m"])[1] or "unknown"
    host_os = (_run(["sw_vers", "-productVersion"])[1] or "0").strip()
    min_os = plist_min_os(app)
    binaries = find_binaries(app)
    signed = is_signed(app)

    print("app      %s" % app)
    print("host     %s  macOS %s  Rosetta %s"
          % (host_arch, host_os,
             {True: "已安装", False: "未安装", None: "未知"}[rosetta_installed()]))
    print("min OS   %s" % (min_os or "未声明"))
    print("signed   %s" % ("是" if signed else "否"))
    print()
    print("%-6s %s" % ("archs", "binary"))
    combined: set[str] = set()
    for path in binaries:
        archs = binary_archs(path)
        combined |= archs
        print("%-6s %s" % ("+".join(sorted(archs)) or "?",
                           path.relative_to(app)))
    print()

    findings = evaluate(host_arch, host_os, combined, signed, min_os,
                        rosetta_installed())
    for item in findings:
        print("[%s] %s" % (item["level"], item["text"]))

    state = verdict(findings)
    print()
    print("结论：%s" % {"ok": "能启动", "warning": "能启动，但有隐患",
                       "blocked": "启动不了，按上面的命令修"}[state])
    return 0 if state != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
