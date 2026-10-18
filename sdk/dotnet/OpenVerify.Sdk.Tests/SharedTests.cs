using System.Text.Json.Nodes;
using Xunit;
namespace OpenVerify.Tests;
public class SharedTests
{
 public static IEnumerable<object[]> Cases(){var dir=new DirectoryInfo(AppContext.BaseDirectory);while(dir is not null && !File.Exists(Path.Combine(dir.FullName,"conformance/sdk/manifest.json")))dir=dir.Parent;var root=Path.Combine(dir!.FullName,"conformance/sdk");var m=JsonNode.Parse(File.ReadAllText(Path.Combine(root,"manifest.json")))!;foreach(var p in m["cases"]!.AsArray())yield return [File.ReadAllText(Path.Combine(root,p!.GetValue<string>()))];}
 [Theory][MemberData(nameof(Cases))] public void Shared(string text){var c=JsonNode.Parse(text)!;JsonNode? result=null;ProtocolException? error=null;try{if(c["operation"]!.GetValue<string>()=="data"){Sdk.ValidateData(c["schema"],c["input"]);result=c["input"];}else{var v=Sdk.Parse(c["contract"]!.GetValue<string>(),c["type"]!.GetValue<string>(),c["input"]!.ToJsonString());result=JsonNode.Parse(Sdk.Serialize(v));}}catch(ProtocolException e){error=e;}if(c["expected"]!["accepted"]!.GetValue<bool>()){Assert.Null(error);Assert.True(JsonNode.DeepEquals(result,c["expected"]!["normalized"]),c["id"]!.ToString());}else{Assert.NotNull(error);var code=c["expected"]!["error"]!.GetValue<string>();if(code!="*")Assert.Equal(code,error.Code);}}
 [Fact]public void Duplicate(){Assert.Equal("PROTOCOL_JSON",Assert.Throws<ProtocolException>(()=>Sdk.Parse("vcp","result","{\"protocol\":\"draft\",\"protocol\":\"draft\"}")).Code);}
}
