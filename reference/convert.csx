using System;
using System.IO;
using System.Collections.Generic;
using LibreLancer;
using LibreLancer.Data.IO;
using LibreLancer.Resources;
using LibreLancer.Utf;
using LibreLancer.Utf.Cmp;
using LibreLancer.Utf.Mat;
using LibreLancer.Utf.Vms;
using LibreLancer.ContentEdit.Model;
using LibreLancer.Sur;
using LibreLancer.Graphics;
using SimpleMesh;
class CpuResources : ServerResourceManager {
 public Dictionary<uint,LibreLancer.Utf.Mat.Material> mats = new();
 public Dictionary<uint,VMeshData> mesh = new();
 public Dictionary<string,ImageResource> images = new(StringComparer.OrdinalIgnoreCase);
 public CpuResources(FileSystem fs) : base(null,fs) {}
 public override LibreLancer.Utf.Mat.Material FindMaterial(uint id) => mats.TryGetValue(id,out var m)?m:null;
 public override VMeshData FindMeshData(uint id) => mesh.TryGetValue(id,out var m)?m:null;
 public override ImageResource FindImage(string name) => images.TryGetValue(name,out var m)?m:null;
 public override void LoadResourceFile(string path, MeshLoadMode mode=MeshLoadMode.CPU) {
  using var stream=VFS.Open(path);
  UtfLoader.LoadResourceFile(stream,path,this,out var mat,out var txm,out var vms);
  if(mat!=null)foreach(var p in mat.Materials)mats[p.Key]=p.Value;
  if(txm!=null)foreach(var p in txm.Textures){var image=p.Value.GetImageResource();if(image!=null) images[p.Key]=image;}
  if(vms!=null)foreach(var p in vms.Meshes)mesh[p.Key]=p.Value;
 }
}
var data=@"C:\Program Files (x86)\Microsoft Games\Freelancer\DATA";
var output=@"C:\Users\igfi\Documents\Codex\2026-09-08\i\work\converted";
Directory.CreateDirectory(output);
var map=new MaterialMap(); map.AddMap("EcEtOcOt","DcDtOcOt"); map.AddMap("DcDtEcEt","DcDtEt"); var fs=FileSystem.FromPath(data);
var assets=new[]{
 @"equipment\models\weapons\li_heavy_ion_blaster.cmp",
 @"equipment\models\weapons\li_smlturret.cmp",
 @"equipment\models\weapons\li_rad_launcher.cmp",
 @"equipment\models\weapons\li_cm_dropper01.cmp",
 @"equipment\models\st\ku_thruster.3db",
 @"equipment\models\pilot\ship_pilot.3db",
 @"ships\liberty\li_elite\li_elite.cmp",
 @"ships\liberty\li_elite\li_elite_dmg_starboardwing.3db",
 @"ships\liberty\li_elite\li_elite_dmg_portwing.3db",
 @"ships\liberty\li_elite\li_elite_dmg_spoiler.3db"
};
foreach(var path in assets){
 var r=new CpuResources(fs);
 foreach(var lib in new[]{@"equipment\models\li_equip.mat",@"equipment\models\ku_equip.mat",@"equipment\models\pilots.mat",@"ships\liberty\li_playerships.mat",@"fx\envmapbasic.mat"})r.LoadResourceFile(lib);
 r.LoadResourceFile(path);
 using var input=fs.Open(path);
 var drawable=UtfLoader.LoadDrawable(input,path,r);
 SurFile sur=null;
 var sp=Path.ChangeExtension(path,"sur");if(fs.FileExists(sp)){using var ss=fs.Open(sp);sur=SurFile.Read(ss);}
 var settings=new ModelExporterSettings(){IncludeLods=true,IncludeHulls=true,IncludeHardpoints=true,IncludeTextures=true,IncludeWireframes=false,IncludeAnimations=true};
 var result=drawable is CmpFile c?ModelExporter.Export(c,sur,settings,r):ModelExporter.Export((ModelFile)drawable,sur,settings,r);
 PrintMessages(result);
 if(result.IsError)throw new Exception("Export failed: "+path);
 using var file=File.Create(Path.Combine(output,Path.GetFileNameWithoutExtension(path)+".glb"));
 result.Data.SaveTo(file,ModelSaveFormat.GLB);
 Console.WriteLine("Converted "+path);
}


