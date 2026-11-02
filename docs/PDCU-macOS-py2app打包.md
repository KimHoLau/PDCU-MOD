# macOS（10.13 High Sierra）用 py2app 打包

本工具原本按 Windows + PyInstaller 维护。在 macOS 上打出来的 `.app` 能启动、
主窗口正常，但文件选择器里的 DNG 预览出问题：预览区只露出图片的左下角，
之后列表就点不动了（取消/打开按钮仍可用）。这一页记录环境、打包命令，
以及这条预览链路现在的兜底方式和排查步骤。

## 1. 结论：是布局把预览挤扁了，不是读图挂了

`tools/dng_season_gui.py` 的预览是「后台线程读图 + 主线程 80 ms 轮询取结果」。
旧代码有三处会各自造成一种「像卡死」的现象：

| 洞 | 触发条件 | 旧行为 |
|---|---|---|
| 预览尺寸写死 | 缩略图固定 `248×190`，但预览列没有最小宽度 | 面板被挤到比图窄时，Tk 只画出位图的左下角 → 「图只显示左侧一点点」 |
| 出图引发整窗重排 | Label 从文字宽度（约 90 px）换成 248 px 位图 | 出图瞬间列表从 707 缩到 569、预览列从 132 弹到 268，点完整片区域在重排中失效 |
| 列表被挤没 | 预览列按内容撑开、列表列 `weight=1` | 窗口一变窄，列表被压成十几像素宽，点不中任何行 → 「再也无法选择其他 DNG」 |
| 主线程取结果时抛异常 | `ImageTk.PhotoImage()` 在打包环境里失败（Tk/Pillow 桥接断了） | 异常在 Tk 回调里被吞掉，`after(80, ...)` 不再续约，预览定格在「正在加载预览…」 |
| 后台线程不返回 | 读取被系统拦下（10.13 的 TCC 授权）、大文件、C 解码异常 | 没有超时，`_preview_busy` 永远是 `True`，后续选择也不会重试 |

其中「出图引发整窗重排」是「中间整片（列表 + 上面 5 个快捷按钮）点不动、
底部取消/打开却正常」的直接来源：重排发生在点击手势过程中，Aqua 上
`overrideredirect` 窗口的事件区域没跟着更新，于是那一整片区域的点击被丢掉；
底部按钮在重排之外，所以照常响应。

## 2. 现在的兜底（v2.7 之后）

- **出图不再重排**：预览用固定尺寸的 `tk.Canvas`，信息条预留两行，出图前后
  每一列的宽高逐像素相同（回归脚本 `case_no_layout_jump` 守着这条）。
- **按实际尺寸适配**：每次绘制都量当前画布大小再 `thumbnail`，窗口缩放时
  120 ms 防抖重绘。画布没有固有尺寸，不会再出现「位图比容器大、被裁到一角」。
- **列表有下限**：列表列 `minsize=320`，空间不够时先让预览列让位，列表始终可点。
- **macOS 不用无边框窗**：`overrideredirect(True)` 的窗口在 Aqua 上无法成为
  key window，点击原生 Listbox 与重绘都会出问题。macOS 上改用带标题栏的普通
  窗口（隐式模态），Windows 仍保留自绘深色边框。想在同一份构建里 A/B：

  ```bash
  PDCU_BORDERLESS_WINDOW=1 "dist/PDCU MOD.app/Contents/MacOS/PDCU MOD"   # 复现旧样式
  PDCU_TITLED_WINDOW=1     "dist/PDCU MOD.app/Contents/MacOS/PDCU MOD"   # 强制普通窗口
  ```
- **不会无限等**：`PREVIEW_TIMEOUT`（默认 8 秒）到点就复位状态、显示
  「预览超时，点此重试」，点预览区即可重试。
- **异常不再打断轮询**：`_poll_preview` 整体加保护，取结果、建图各自
  `try/except`，一条失败只影响这一张图。
- **建图有第二通道**：`ImageTk.PhotoImage` 失败时，改用 Pillow 编码 PNG +
  `tk.PhotoImage(data=..., format="png")`，绕开 Pillow 与 Tk 的 ABI/Tk 解释器
  绑定；Tk 8.5（无 PNG 解码）再退到逐像素 `put()`。
- **悬停提示不被 Aqua 吞掉**：季节来源那 4 行的机型清单是个独立 Toplevel。
  macOS 上无边框窗会被主窗口盖住，装饰调用也可能被拒绝；现在 `-topmost` +
  `lift()` 一定浮在最上面，`overrideredirect` 失败就退回普通小窗，整段失败会
  写进日志（`tooltip failed` / `override-redirect refused`）而不是无声消失。
- **有日志**：打包版没有控制台，异常现在写文件
  `~/Library/Logs/PDCU MOD/pdcu-mod.log`（含 Tk/Pillow 版本、每个失败原因的
  完整 traceback，`faulthandler` 还会在真卡死时把 Python 栈刷进同一个文件）。

## 3. 环境

macOS 10.13 上能用的组合很窄，先确认下面两条再打包：

```bash
python3 -V                              # 建议 python.org 的 3.9.x（Tk 8.6）
python3 -c "import tkinter as tk; print(tk.TkVersion)"     # 必须是 8.6
python3 -c "from PIL import Image; Image.new('RGB',(8,8)).save('/tmp/x.png'); print('pillow ok')"
```

- **Tk**：Apple 自带的 Tk 8.5 缺 PNG 解码、字体与 Retina 支持也差，务必用
  python.org 安装包自带的 Tk 8.6。
- **Pillow**：官方平台支持表里，macOS 10.13 最后有记录的版本只到 Pillow 4.2.1
  （见 [Pillow Platform support](https://pillow.readthedocs.io/en/stable/installation/platform-support.html)），
  新 wheel 的部署目标不保证兼容 10.13。上面那条 `pillow ok` 跑不过就换版本或
  源码编译，**不要**带着坏掉的 Pillow 去打包——那时预览会显示「预览需要 Pillow」
  或「无法读取预览」，是另一类问题。

## 4. 打包

```bash
pip install -U py2app pillow
python3 setup.py py2app           # 产物：dist/PDCU MOD.app
python3 setup.py py2app -A        # 别名包：引用源码、秒级重建，用于对照
```

`setup.py` 已带入 `PIL` 整包、排除 numpy、写好 `LSMinimumSystemVersion=10.13`，
并自动使用 `tools/season.icns` 作为 App 图标。

图标由仓库里的 logo 生成，改动 logo 后重跑即可（Windows 上也能跑，不依赖
`iconutil`/`sips`）：

```bash
python tools/make_icns.py tools/assets/pdcu_mod_logo_96.png tools/season.icns
```

它写出 16/32/64/128/256/512 六个 PNG 槽位及对应 @2x 槽位（与 `iconutil` 的
输出集合一致），并在写完后逐个 chunk 解析回读校验。源图只有 96 px 时不生成
1024 px 槽位——那是纯放大，模糊图反而会被 Finder 优先选用。

## 5. 打包后先做这三步

**① 从终端启动 bundle 里的可执行文件**——这样 stderr 可见，异常不再凭空消失：

```bash
"dist/PDCU MOD.app/Contents/MacOS/PDCU MOD"
```

**② 跑预览自检**，它会一路报告到 Tk 建图这一步，直接指出哪一环在 bundle 里坏了：

```bash
"dist/PDCU MOD.app/Contents/MacOS/PDCU MOD" --preview-selftest sample/645D.DNG
```

正常输出形如（Windows 参考值）：

```
python 3.14.3
platform win32
frozen False
tk 8.6
pillow 12.1.1
model 'PENTAX 645D'
preview bytes 40478
decoded 640x480 RGB
imagetk ok 248x186
png photo ok 248x186
```

`imagetk FAILED` 就是第 1 节表格里的第一行；此时界面仍应正常出图（走 PNG 兜底）。

**③ 看日志**：

```bash
tail -n 100 ~/Library/Logs/PDCU\ MOD/pdcu-mod.log
```

真卡成彩球时再抓一份栈：

```bash
sample "PDCU MOD" 5 -file /tmp/pdcu-sample.txt
```

## 6. 首选的排查顺序

1. `python3 setup.py py2app -A` 的别名包预览是否正常？正常 → 问题在打包
   （PIL/Tk 没带全），对照 `dist/PDCU MOD.app/Contents/Resources/lib/` 下有没有
   `PIL` 和 `PIL/_imaging*.so`。
2. 源码运行是否正常？别把「没装 Pillow」当成对照结论（那会显示
   「预览需要 Pillow」，本来就不走这条链路）。
3. 还是卡 → 看日志里 `preview timed out` 之前最后一行；若是 `ImageTk.PhotoImage
   failed`，说明 PNG 兜底也没成，把该段 traceback 贴回来。

## 7. 已知 10.13 限制

- **TCC 授权**：10.13 起访问「桌面/文稿/下载/外置卷」需要用户授权。未签名的
  `.app` 首次读取会弹系统授权框；如果框被自绘的 `overrideredirect` 窗口挡住，
  读取会一直挂着——现在会超时报错而不是永久卡住，授权一次后即正常。
- **签名**：分发给别人时 `codesign --deep --force --sign - "dist/PDCU MOD.app"`
  做 ad-hoc 签名，可减少 Gatekeeper 与 TCC 的反复提示。
- 本工具不写 raw 像素，macOS 侧只影响「文件选择器预览」这一处；转换结果与
  Windows 版逐字节一致（见 readme 的自检哈希）。

## 8. 在 Apple Silicon（M 系列）上无法运行

在 10.13 的 Intel 机器上打的包，拿到 M 系列笔记本上双击很可能什么都不发生。
两条独立原因，都很常见：

1. **架构**：10.13 上的 Python 是 x86_64，py2app 打出来的所有 Mach-O 都是
   x86_64。M 系列需要 Rosetta 2 才能跑；没装（或装不上）就是直接不启动。
2. **签名**：Apple Silicon 要求所有可执行代码至少有 ad-hoc 签名，从别处拷来的
   未签名二进制会被系统直接终止（`Killed: 9`），日志里常见的
   `code signature invalid` 就是这个。

先跑一条诊断命令，它会逐个子二进制打印架构、签名状态，并给出下一步：

```bash
python3 tools/check_macos_bundle.py "dist/PDCU MOD.app"
```

输出形如：

```
host     arm64  macOS 14.5  Rosetta 未安装
signed   否
archs  binary
x86_64 Contents/MacOS/PDCU MOD
x86_64 Contents/Frameworks/Python.framework/Versions/3.9/Python
[block] 这个 .app 只有 x86_64，本机是 Apple Silicon 且未装 Rosetta 2 ...
[block] Apple Silicon 要求所有可执行代码至少 ad-hoc 签名 ...
结论：启动不了，按上面的命令修
```

三条路，按推荐顺序：

1. **在 Apple Silicon 机器上重新打包**（最稳）。装 arm64 版 Python 3.9+ 与
   Pillow，`python3 setup.py py2app`，产出的就是 arm64；打包后照样跑一次上面的
   诊断命令确认 `archs` 是 arm64。
2. **让 Intel 包在 M 系列上跑**：先
   `softwareupdate --install-rosetta --agree-to-license`，再
   `codesign --deep --force --sign - "dist/PDCU MOD.app"`。能跑，但慢且有后续
   兼容风险。
3. **一份 universal2 包**：需要 Python、Tcl/Tk、Pillow 全是 universal2，
   `PDCU_ARCH=universal2 python3 setup.py py2app`，最后仍以诊断命令打印的
   `lipo` 结果为准——任何一环不是 universal2，产出就还是单架构。

签名与分发：

```bash
codesign --deep --force --sign - "dist/PDCU MOD.app"      # ad-hoc，仅本机/小范围
codesign --deep --force --sign "Developer ID Application: ..." "dist/PDCU MOD.app"
```

要发给别人还得 `notarytool` 公证，本仓库没有自动化这一步。另外，从网上下载的
包会带 quarantine 属性，首次打开被拦时用「系统设置 → 隐私与安全性 → 仍要打开」，
或 `xattr -dr com.apple.quarantine "dist/PDCU MOD.app"`。

如果诊断命令说「能启动」却仍然打不开，那就是启动期崩溃（不是架构/签名）：

```bash
"dist/PDCU MOD.app/Contents/MacOS/PDCU MOD"     # 终端里直接跑，看 stderr
ls -t ~/Library/Logs/DiagnosticReports/ | head  # 找 PDCU MOD 开头的 .ips
```
