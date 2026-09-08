#r "C:\Users\igfi\Downloads\librelancer-sdk-2025.11-win64\librelancer-2025.11-win-x64\lib\System.Text.Json.dll"
using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;
using LibreLancer.Utf.Ale;
var root=@"C:\Program Files (x86)\Microsoft Games\Freelancer\DATA";
var output=@"C:\Users\igfi\Documents\Codex\2026-09-08\i\work\ale";
Directory.CreateDirectory(output);
var opts=new JsonSerializerOptions{IncludeFields=true,WriteIndented=true};opts.Converters.Add(new JsonStringEnumConverter());
foreach(var p in new[]{@"fx\engines\gf_li_smallengine02_fire.ale",@"fx\engines\gf_li_smallengine02_trail.ale",@"fx\equipment\gf_ge_s_thruster_01.ale",@"fx\misc\li_contrail.ale",@"fx\weapons\li_laser_03.ale",@"fx\weapons\li_laser_01.ale"}){
 using var stream=File.OpenRead(Path.Combine(root,p));var ale=new AleFile(p,stream);
 File.WriteAllText(Path.Combine(output,Path.GetFileNameWithoutExtension(p)+".json"),JsonSerializer.Serialize(ale,opts));
  var sampleNodes = new List<object>();
 foreach(var node in ale.NodeLib.Nodes) {
  var samples=new List<object>();
  foreach(float sp in new float[]{0,0.5f,0.85f,0.9f,0.95f,1}) {
   var pars=new Dictionary<string,object>();
   foreach(var par in node.Parameters) {
    if(par.Value is AlchemyTransform tr) pars[par.Name.ToString()]=new {Translation=tr.GetTranslation(sp,0),Rotation=tr.GetRotation(sp,0)};
    else if(par.Value is AlchemyCurveAnimation ca) pars[par.Name.ToString()]=Enumerable.Range(0,33).Select(i=>ca.GetValue(sp,i/32f)).ToArray();
    else if(par.Value is AlchemyFloatAnimation fa) pars[par.Name.ToString()]=Enumerable.Range(0,33).Select(i=>fa.GetValue(sp,i/32f)).ToArray();
    else if(par.Value is AlchemyColorAnimation co) pars[par.Name.ToString()]=Enumerable.Range(0,33).Select(i=>co.GetValue(sp,i/32f)).ToArray();
    else pars[par.Name.ToString()]=par.Value;
   }
   samples.Add(new {SParam=sp,Parameters=pars});
  }
  sampleNodes.Add(new {node.Name,node.CRC,Samples=samples});
 }
 File.WriteAllText(Path.Combine(output,Path.GetFileNameWithoutExtension(p)+"_sampled.json"),JsonSerializer.Serialize(new {Effects=ale.FxLib.Effects,Nodes=sampleNodes},opts));
 Console.WriteLine(p+" sampled");
}

