// Project-owned diagnostic Mod. No gameplay commands, patches, or scenario setup.
using System;
using System.IO;
using System.Net;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Godot;
using MegaCrit.Sts2.Core.Modding;
using MegaCrit.Sts2.Core.Runs;
using MegaCrit.Sts2.Core.Saves;

namespace Spire2Lab.Probe;

[ModInitializer("Initialize")]
public static class RuntimeProbe
{
    private static HttpListener? listener;
    private static string snapshot = "{\"status\":\"initializing\",\"read_only\":true}";
    private static string gameSha = "";
    private static string modSha = "";
    private static readonly string instance = Guid.NewGuid().ToString("N");
    private static long samples;
    private static long lastSample;

    public static void Initialize()
    {
        try
        {
            gameSha = Hash(typeof(RunManager).Assembly.Location);
            if (gameSha != ProbeBuild.ExpectedGameSha)
                throw new InvalidOperationException("Game fingerprint differs from the probe build");
            var modPath = Assembly.GetExecutingAssembly().Location;
            modSha = Hash(modPath);
            int port = 21526;
            var conf = Path.Combine(Path.GetDirectoryName(modPath)!, "STS2_MCP.conf");
            if (File.Exists(conf))
            {
                using var doc = JsonDocument.Parse(File.ReadAllText(conf));
                port = doc.RootElement.GetProperty("port").GetInt32();
            }
            if (port < 1 || port > 65535) throw new InvalidOperationException("Invalid probe port");
            listener = new HttpListener();
            listener.Prefixes.Add($"http://127.0.0.1:{port}/");
            listener.Start();
            var tree = (SceneTree)Engine.GetMainLoop();
            tree.Connect(SceneTree.SignalName.ProcessFrame, Callable.From(SampleOnGameThread));
            _ = Task.Run(Serve);
            GD.Print($"[Spire2Lab Probe] READ ONLY listening on 127.0.0.1:{port}");
        }
        catch (Exception ex)
        {
            listener?.Close();
            GD.PrintErr($"[Spire2Lab Probe] Failed to start: {ex}");
        }
    }

    private static string Hash(string path) => Convert.ToHexString(
        SHA256.HashData(File.ReadAllBytes(path))).ToLowerInvariant();

    // Game objects are read only on Godot's main thread; HTTP reads a cached string.
    private static void SampleOnGameThread()
    {
        long now = System.Environment.TickCount64;
        if (now - lastSample < 500) return;
        lastSample = now;
        string next;
        try
        {
            next = JsonSerializer.Serialize(new {
                status = "ok", probe_protocol = 1, lab_protocol = 0,
                read_only = true, control_supported = false,
                lab_capabilities = Array.Empty<string>(),
                expected_game_version = ProbeBuild.ExpectedVersion,
                game_assembly_sha256 = gameSha, lab_mod_sha256 = modSha,
                lab_instance_id = instance,
                lab_profile_id = SaveManager.Instance.CurrentProfileId,
                run_in_progress = RunManager.Instance.IsInProgress,
                sampled_at_utc = DateTime.UtcNow.ToString("O"), sample_number = ++samples
            });
        }
        catch (Exception ex)
        {
            next = JsonSerializer.Serialize(new { status = "unavailable", read_only = true,
                error_type = ex.GetType().Name, sampled_at_utc = DateTime.UtcNow.ToString("O") });
        }
        Volatile.Write(ref snapshot, next);
    }

    private static async Task Serve()
    {
        while (listener?.IsListening == true)
        {
            HttpListenerContext context;
            try { context = await listener.GetContextAsync(); }
            catch (Exception ex) when (ex is HttpListenerException or ObjectDisposedException) { return; }
            try
            {
                var response = context.Response;
                string body;
                if (context.Request.HttpMethod != "GET")
                {
                    response.StatusCode = 405;
                    response.Headers["Allow"] = "GET";
                    body = "{\"error\":\"read_only_probe\"}";
                }
                else if (context.Request.Url?.AbsolutePath is "/" or "/probe" or "/api/v1/singleplayer")
                    body = Volatile.Read(ref snapshot);
                else
                {
                    response.StatusCode = 404;
                    body = "{\"error\":\"unknown_probe_endpoint\"}";
                }
                var bytes = Encoding.UTF8.GetBytes(body);
                response.ContentType = "application/json; charset=utf-8";
                response.ContentLength64 = bytes.Length;
                await response.OutputStream.WriteAsync(bytes);
            }
            catch (Exception ex) { GD.PrintErr($"[Spire2Lab Probe] HTTP response failed: {ex.GetType().Name}"); }
            finally { context.Response.Close(); }
        }
    }
}
