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
files["START-HERE.txt"] = """Spire2Lab Windows 接入包

此包只有接入/安装脚本，不包含游戏、游戏 DLL 或实验用 Mod 二进制。
每台电脑的版本和桥接都须单独核验；项目验收进度见 PHASE1-STATUS.json。

1. 解压后，在此目录打开 PowerShell。
2. 使用你平时从 Windows 登录 Linux 的 SSH 目标与端口运行：
   Set-ExecutionPolicy -Scope Process Bypass -Force
   .\\Connect-Windows.ps1 -Server 用户@服务器 -RemoteRoot /srv/Spire2Lab -SshPort 端口
   将 /srv/Spire2Lab 换成服务器上实际的项目绝对路径（可在 Linux 项目目录执行 pwd 查看）。
   当前路径支持英文字母、数字、下划线、点、斜线和短横线，不支持空格。
   若 SSH 使用 22 端口，可省略 -SshPort。
   若 SSH 目标是配置文件中的别名，仍须提供其实际端口；当前脚本显式使用端口参数。
   不需要在聊天中提供密码或私钥。首次 SSH 信任与登录由本机 OpenSSH 处理。
   若无法发现游戏，追加 -GameDir "D:\\SteamLibrary\\steamapps\\common\\Slay the Spire 2"。
   若已将 Mod 的 STS2_MCP.conf 中 port 改成 21526，追加 -GameBridgePort 21526。
   此参数只调整隧道目标，不替你修改 Mod 配置；默认仍为 15526，Linux 入口仍为 18526。
3. 脚本读取 Steam 构建信息和文件指纹，把三个编译引用 DLL 传到你的 Linux 服务器。
   它不会安装 Mod，也不会修改存档。保持窗口打开以维持 SSH 隧道。
4. Linux 端收到文件后，由构建流程核对实际版本并生成桥接 Mod。
   编译成功后另开 PowerShell，进入解压目录后运行：
   Set-ExecutionPolicy -Scope Process Bypass -Force
   .\\Install-Windows-Mod.ps1 -Server 用户@服务器 -RemoteRoot /srv/Spire2Lab -SshPort 端口
   直接使用当前 PowerShell 会话，无需再次调用 powershell 启动命令。
   安装前关闭游戏。脚本会检查文件指纹、备份旧文件并安装 Mod。
   安装成功后，请通过 Steam 启动游戏。
   若首次同意加载 Mod 后游戏退出，从 Steam 再启动一次，先停留主菜单核对版本和接口。
   若再次退出，保留启动日志供诊断，无需反复重装。
5. Linux 启动 bash scripts/start.sh 后，在 Windows 浏览器打开 http://127.0.0.1:8765。
   原版接入和参考战斗仍需在桥接成功运行后验收。

SSH 连接失败时：
   ssh -vvv -E .\\spire2lab-ssh.log -T -p 端口 用户@服务器 "echo SPIRE2LAB_SSH_OK"
   Get-Content .\\spire2lab-ssh.log -Tail 70
   使用与接入脚本相同的 SSH 目标与端口。密码由 OpenSSH 交互读取，不写入命令。
   没有出现 SPIRE2LAB_SSH_OK 时，先检查日志中的认证和会话错误。
   出现该标记表示本次 SSH 命令成功，不代表文件传输或端口转发已经可用。
   exit 255 是 SSH 失败；exit 20 是远程项目文件缺失；exit 21 是远程目录创建失败。
   本地版本报告保存在 $env:TEMP\\sts2-lab-windows-report.json，失败时仍保留。

已安装的 Mod 改用其他端口（例如 21526）：
   先关闭游戏，在旧接入窗口按 Ctrl+C 关闭隧道；检查 Windows 新端口没有监听者。
   备份游戏目录 mods\\STS2_MCP\\STS2_MCP.conf，将 JSON 中整数 port 改成 21526，保留其他属性。
   若没有配置文件，在上述已安装 Mod 目录创建 UTF-8 JSON 文件，内容为 {"port":21526}。
   从 Steam 重启，先验证 http://127.0.0.1:21526/ 和 /api/v1/singleplayer。
   已完成上传/安装时，可直接重建隧道，避免再次上传版本报告：
   ssh -N -p 端口 -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -L 127.0.0.1:8765:127.0.0.1:8765 -R 127.0.0.1:18526:127.0.0.1:21526 用户@服务器
   后续使用此版 Connect-Windows.ps1 时须传 -GameBridgePort 21526；旧版脚本不支持该参数。
   修改配置无需重编译 Mod，实际连通性仍需本机和服务器 HTTP 验证。

默认端口 15526 超时且监听者为 Code.exe 时（也可按上面的方法换端口）：
   Windows 15526 供游戏桥接使用；Linux 18526 通过独立 SSH 隧道指向它。
   在退出游戏前保留 godot.log 中的 [STS2 MCP] 启动成功/失败信息。
   日志位于 $env:APPDATA\\SlayTheSpire2\\logs\\godot.log，启动信息可能不在文件末尾。
   正常退出游戏，在 VS Code 的“端口 / Ports”面板停止本地转发地址为 127.0.0.1:15526 的条目。
   注意远程端口列可能是另一个号码；其他远程窗口也可能持有该转发。
   保留 Connect-Windows.ps1 窗口；确认 Windows 15526 已释放后，从 Steam 再启动游戏。
   不要将 Linux 18526 再转发到 Windows 15526。无需终止整个 VS Code 或反复重装 Mod。
   若没有找到对应转发，保留进程拥有者和启动日志继续定位。
   仓库 .vscode/settings.json 为本项目工作区关闭自动/恢复/点击链接转发，不删除已有条目。
   若 15526 和新端口都被 Code.exe 占用，在实际远程窗口的工作区设置中关闭
   remote.autoForwardPorts、remote.restoreForwardedPorts、remote.forwardOnOpen，
   然后在 Ports 面板停止冲突的本地转发；若打开的不是项目目录，仓库设置未必生效。
   关闭自动转发不删除已有条目，也不阻止扩展显式转发。独立 SSH 隧道不受这些设置控制。

完整说明：README.txt；验收状态：PHASE1-STATUS.json。
两个脚本必须使用同一个服务器、项目绝对路径与端口。SSH 隧道只监听两台电脑的 loopback 地址。
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
