"""Package Windows onboarding scripts; contains no proprietary assemblies or game saves."""

from pathlib import Path
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
output = ROOT / "artifacts/installers/sts2-lab-windows.zip"
output.parent.mkdir(parents=True, exist_ok=True)
files = {
    name: (ROOT / "scripts" / name).read_bytes()
    for name in ("Connect-Windows.ps1", "Install-Windows-Mod.ps1")
}
files["START-HERE.txt"] = """STS2 Lab Windows 接入包

此包只有接入/安装脚本，不包含游戏、游戏 DLL 或实验用 Mod 二进制。
第一阶段仍待你的 Windows 实机验证。

1. 解压后，在此目录打开 PowerShell。
2. 使用你平时从 Windows 登录 Linux 的 SSH 目标与端口运行：
   powershell -ExecutionPolicy Bypass -File .\\Connect-Windows.ps1 -Server 用户@服务器 -SshPort 端口
   若 SSH 使用 22 端口，可省略 -SshPort。
   若 SSH 目标是配置文件中的别名，仍须提供其实际端口；当前脚本显式使用端口参数。
   不需要在聊天中提供密码或私钥。首次 SSH 信任与登录由本机 OpenSSH 处理。
   若无法发现游戏，追加 -GameDir "D:\\SteamLibrary\\steamapps\\common\\Slay the Spire 2"。
3. 脚本读取 Steam 构建信息和文件指纹，把三个编译引用 DLL 传到你的 Linux 服务器。
   它不会安装 Mod，也不会修改存档。保持窗口打开以维持 SSH 隧道。
4. Linux 端收到文件后，由构建流程核对实际版本并生成桥接 Mod。
   编译成功后另开 PowerShell，运行：
   powershell -ExecutionPolicy Bypass -File .\\Install-Windows-Mod.ps1 -Server 用户@服务器 -SshPort 端口
   安装前关闭游戏。脚本会检查文件指纹、备份旧文件并通过 Steam 启动游戏。
5. Linux 启动 bash scripts/start.sh 后，在 Windows 浏览器打开 http://127.0.0.1:8765。
   原版接入和参考战斗仍需在桥接成功运行后验收。

Linux 项目位置：/user/chenzk/sts2-lab
完整说明：README.txt；验收状态：PHASE1-STATUS.json。
两个脚本必须使用同一个服务器与端口。SSH 隧道只监听两台电脑的 loopback 地址。
""".encode("utf-8-sig")
manifest = {
    "scope": "windows_onboarding_scripts_only",
    "contains_game_files": False,
    "windows_execution_verified": False,
    "sha256": {name: hashlib.sha256(blob).hexdigest() for name, blob in files.items()},
}
files["package.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
    for name, blob in files.items():
        archive.writestr(name, blob)
with zipfile.ZipFile(output) as archive:
    assert archive.testzip() is None
    assert set(archive.namelist()) == set(files)
    for name, blob in files.items():
        assert archive.read(name) == blob
print(
    json.dumps(
        {
            "package": str(output),
            "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            "files": list(files),
            "windows_execution_verified": False,
        },
        indent=2,
    )
)
