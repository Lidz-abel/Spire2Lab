// Project-authored read-only viewport capture. No game action or rule is changed.
// API guidance: Godot Viewport.get_texture / RenderingServer.frame_post_draw.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Net;
using System.Security.Cryptography;
using System.Threading;
using System.Threading.Tasks;
using Godot;

namespace STS2_MCP;

public static partial class McpMod
{
    private static readonly SemaphoreSlim LabImageHttpGate = new(1, 1);
    private static Action? LabImageCancel;

    private static void HandleLabImage(HttpListenerRequest request, HttpListenerResponse response)
    {
        if (request.HttpMethod != "GET") { SendError(response, 405, "GET required"); return; }
        string instance = request.QueryString["instance"] ?? "";
        string token = request.QueryString["token"] ?? "";
        string mode = request.QueryString["mode"] ?? "combat";
        if (mode is not ("combat" or "act")) { SendError(response, 400, "Unknown image boundary mode"); return; }
        if (instance.Length != 32 || token.Length != 64)
        { SendError(response, 400, "Expected instance and token are required"); return; }
        if (!LabImageHttpGate.Wait(0)) { SendError(response, 409, "image_capture_busy"); return; }
        using var cancelled = new CancellationTokenSource(TimeSpan.FromSeconds(5));
        try
        {
            var task = RunOnMainThread(() => BeginLabImage(instance, token, cancelled.Token, mode == "act")).Unwrap();
            var image = task.WaitAsync(cancelled.Token).GetAwaiter().GetResult();
            response.Headers["Cache-Control"] = "no-store";
            SendJson(response, image);
        }
        catch (Exception ex)
        {
            SendError(response, 409, "image_capture_unavailable: " + ex.Message);
        }
        finally
        {
            cancelled.Cancel();
            // Event removal must run on the game thread, including timeouts when
            // rendering was suspended. A late queued request checks cancellation.
            _ = RunOnMainThread(() => { LabImageCancel?.Invoke(); });
            LabImageHttpGate.Release();
        }
    }

    private static Task<Dictionary<string, object?>> BeginLabImage(string instance, string token, CancellationToken cancelled, bool act)
    {
        cancelled.ThrowIfCancellationRequested();
        if (LabImageCancel != null) throw new InvalidOperationException("image_capture_pending");
        var initial = BuildLabGameState();
        var boundary = new DecisionImageBoundary(instance, token,
            (string)initial["game_assembly_sha256"]!, (string)initial["lab_mod_sha256"]!, act);
        bool Pending() => LabPendingFrom != null || (act && LabActPendingFrom != null);
        boundary.Validate(initial, Pending());
        ulong frameBefore = (ulong)Engine.GetFramesDrawn();
        var completion = new TaskCompletionSource<Dictionary<string, object?>>(TaskCreationOptions.RunContinuationsAsynchronously);
        Action? onFrame = null;
        void Cleanup()
        {
            RenderingServer.FramePostDraw -= onFrame;
            LabImageCancel = null;
        }
        onFrame = () =>
        {
            try
            {
                cancelled.ThrowIfCancellationRequested();
                ulong frame = (ulong)Engine.GetFramesDrawn();
                // Some renderers increment their counter after the signal. In
                // that case wait for the following signal, within the same limit.
                if (frame <= frameBefore) return;
                boundary.Validate(BuildLabGameState(), Pending());
                DecisionImageBoundary.ValidateFrame(frameBefore, frame);
                var tree = Engine.GetMainLoop() as SceneTree ?? throw new InvalidOperationException("image_no_scene_tree");
                var viewport = tree.Root;
                if (!viewport.IsVisible() || viewport.Mode == Window.ModeEnum.Minimized)
                    throw new InvalidOperationException("image_window_not_visible");
                using var pixels = viewport.GetTexture().GetImage();
                if (pixels == null || pixels.IsEmpty()) throw new InvalidOperationException("image_empty_viewport");
                int width = pixels.GetWidth(), height = pixels.GetHeight();
                if (width <= 0 || height <= 0 || width > 8192 || height > 8192 || (long)width * height > 16777216)
                    throw new InvalidOperationException("image_dimensions_out_of_range");
                bool linear = viewport.UseHdr2D;
                pixels.Convert(Image.Format.Rgb8);
                if (linear) pixels.LinearToSrgb();
                byte[] png = pixels.SavePngToBuffer();
                if (png.Length == 0 || png.Length > 16 * 1024 * 1024)
                    throw new InvalidOperationException("image_size_out_of_range");
                boundary.Validate(BuildLabGameState(), Pending());
                Cleanup();
                completion.TrySetResult(new Dictionary<string, object?> {
                    ["schema"] = "decision-image-v1", ["mime_type"] = "image/png",
                    ["lab_instance_id"] = instance, ["lab_state_token"] = token,
                    ["game_assembly_sha256"] = initial["game_assembly_sha256"],
                    ["lab_mod_sha256"] = initial["lab_mod_sha256"],
                    ["width"] = width, ["height"] = height, ["frame_before"] = frameBefore,
                    ["frame_drawn"] = frame, ["captured_at"] = DateTime.UtcNow.ToString("O"),
                    ["sha256"] = Convert.ToHexString(SHA256.HashData(png)).ToLowerInvariant(),
                    ["png_base64"] = Convert.ToBase64String(png),
                    ["source"] = "godot_root_viewport", ["linear_to_srgb"] = linear
                });
            }
            catch (Exception ex) { Cleanup(); completion.TrySetException(ex); }
        };
        LabImageCancel = () => { Cleanup(); completion.TrySetCanceled(); };
        RenderingServer.FramePostDraw += onFrame;
        return completion.Task;
    }
}
