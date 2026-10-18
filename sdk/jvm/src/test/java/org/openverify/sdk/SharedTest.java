package org.openverify.sdk;
import org.junit.jupiter.api.*;
import org.junit.jupiter.api.DynamicTest;
import com.fasterxml.jackson.databind.*;
import java.nio.file.*;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;
class SharedTest {
 @TestFactory List<DynamicTest> shared()throws Exception{
  Path root=Path.of("../../conformance/sdk");ObjectMapper mapper=new ObjectMapper();JsonNode manifest=mapper.readTree(Files.readString(root.resolve("manifest.json")));List<DynamicTest> tests=new ArrayList<>();
  for(JsonNode path:manifest.path("cases")){JsonNode c=mapper.readTree(Files.readString(root.resolve(path.asText())));tests.add(DynamicTest.dynamicTest(c.path("id").asText(),()->{
   JsonNode result=null;ProtocolException error=null;try{if(c.path("operation").asText().equals("data")){Sdk.validateData(c.path("schema"),c.path("input"),"INVALID_INPUT");result=c.path("input");}else{WireObject v=Sdk.parse(c.path("contract").asText(),c.path("type").asText(),c.path("input").toString());result=mapper.readTree(Sdk.serialize(v));}}catch(ProtocolException e){error=e;}
   if(c.path("expected").path("accepted").asBoolean()){assertNull(error);assertEquals(c.path("expected").path("normalized"),result);}else{assertNotNull(error);if(!c.path("expected").path("error").asText().equals("*"))assertEquals(c.path("expected").path("error").asText(),error.code());}
  }));}return tests;
 }
 @Test void duplicate(){assertEquals("PROTOCOL_JSON",assertThrows(ProtocolException.class,()->Sdk.parse("vcp","result","{\"protocol\":\"draft\",\"protocol\":\"draft\"}")).code());}
}
