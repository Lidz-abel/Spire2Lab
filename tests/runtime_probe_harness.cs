// Synthetic Godot/game classes; exercises the real probe's HTTP server on Linux.
using System;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Net.Sockets;
using System.Reflection;
using System.Security.Cryptography;
using System.Text.Json;
using System.Threading.Tasks;
namespace Godot {
 public sealed class Environment { }
 public sealed class Callable { public Action Action = null!; public static Callable From(Action a) => new(){Action=a}; }
 public sealed class SceneTree { public static class SignalName { public const string ProcessFrame="frame"; }
  public Action? Tick; public void Connect(string name, Callable call) {Tick=call.Action;} }
 public static class Engine { public static readonly SceneTree Tree=new(); public static object GetMainLoop()=>Tree; }
 public static class GD { public static void Print(string s)=>Console.WriteLine(s); public static void PrintErr(string s)=>Console.Error.WriteLine(s); }
}
namespace MegaCrit.Sts2.Core.Modding { public sealed class ModInitializerAttribute(string method) : Attribute {} }
namespace MegaCrit.Sts2.Core.Runs { public sealed class RunManager {
 public static readonly RunManager Instance = new(); public bool IsInProgress {get;set;} = true; } }
namespace MegaCrit.Sts2.Core.Saves { public sealed class SaveManager {
 public static readonly SaveManager Instance = new(); public bool Fail;
 public int CurrentProfileId => Fail ? throw new InvalidOperationException("synthetic failure") : 3; } }
namespace Spire2Lab.Probe { internal static class ProbeBuild {
 public static string ExpectedGameSha=Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(Assembly.GetExecutingAssembly().Location))).ToLowerInvariant();
 public const string ExpectedVersion="synthetic"; } }
public static class Test {
 static void Check(bool ok,string message) {if(!ok)throw new Exception(message);}
 public static async Task Main() {
  var reserve=new TcpListener(IPAddress.Loopback,0);reserve.Start();int port=((IPEndPoint)reserve.LocalEndpoint).Port;reserve.Stop();
  var dir=Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location)!;
  File.WriteAllText(Path.Combine(dir,"STS2_MCP.conf"),"{\"port\":"+port+"}");
  Spire2Lab.Probe.RuntimeProbe.Initialize();
  Godot.Engine.Tree.Tick!();
  using var client=new HttpClient(new HttpClientHandler{UseProxy=false}) {BaseAddress=new Uri($"http://127.0.0.1:{port}"),Timeout=TimeSpan.FromSeconds(5)};
  foreach(var path in new[]{"/","/probe","/api/v1/singleplayer"}) {
   using var r=await client.GetAsync(path);Check(r.StatusCode==HttpStatusCode.OK,"GET failed");
   using var d=JsonDocument.Parse(await r.Content.ReadAsStringAsync());var x=d.RootElement;
   Check(x.GetProperty("read_only").GetBoolean()&&!x.GetProperty("control_supported").GetBoolean(),"Control advertised");
   Check(x.GetProperty("lab_protocol").GetInt32()==0&&x.GetProperty("lab_capabilities").GetArrayLength()==0,"Production protocol advertised");
   Check(x.GetProperty("lab_profile_id").GetInt32()==3&&x.GetProperty("run_in_progress").GetBoolean(),"Snapshot differs from synthetic game");
  }
  foreach(var method in new[]{HttpMethod.Post,HttpMethod.Put,HttpMethod.Delete})
   foreach(var path in new[]{"/","/probe","/api/v1/singleplayer","/api/v1/multiplayer","/api/v1/profiles"}) {
    using var req=new HttpRequestMessage(method,path);using var r=await client.SendAsync(req);
    Check(r.StatusCode==HttpStatusCode.MethodNotAllowed,"Mutation was not refused");
   }
  using(var r=await client.GetAsync("/api/v1/profiles"))Check(r.StatusCode==HttpStatusCode.NotFound,"Unexpected route");
  MegaCrit.Sts2.Core.Saves.SaveManager.Instance.Fail=true;
  await Task.Delay(550);Godot.Engine.Tree.Tick!();
  using(var r=await client.GetAsync("/probe")){
   using var d=JsonDocument.Parse(await r.Content.ReadAsStringAsync());
   Check(d.RootElement.GetProperty("status").GetString()=="unavailable","Read failure left stale success");
  }
  Console.WriteLine("PASS: real HTTP read-only routing, protocol isolation, snapshot, and failed read invalidation; synthetic game only");
 }
}
