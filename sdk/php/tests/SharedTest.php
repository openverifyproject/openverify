<?php
declare(strict_types=1);
require __DIR__.'/../vendor/autoload.php';
use OpenVerify\{Sdk,ProtocolError};
use PHPUnit\Framework\TestCase;
final class SharedTest extends TestCase {
    public function testShared(): void {
        $root=__DIR__.'/../../../conformance/sdk/';$manifest=json_decode(file_get_contents($root.'manifest.json'));
        foreach($manifest->cases as $path) {
            $c=json_decode(file_get_contents($root.$path));$error=null;$result=null;
            try {if($c->operation==='data'){Sdk::validateData($c->schema,$c->input);$result=$c->input;}else{$result=Sdk::parse($c->contract,$c->type,json_encode($c->input));$result=json_decode(Sdk::serialize($result));}}catch(ProtocolError $e){$error=$e;}
            if($c->expected->accepted){self::assertNull($error,$c->id.': '.($error?->getMessage()??''));self::assertEquals($c->expected->normalized,$result,$c->id);}else{self::assertInstanceOf(ProtocolError::class,$error,$c->id);if($c->expected->error!=='*')self::assertSame($c->expected->error,$error->errorCode,$c->id);}
        }
    }
    public function testDuplicate():void{$this->expectException(ProtocolError::class);Sdk::parse('vcp','result','{"protocol":"draft","protocol":"draft"}');}
    public function testNumericOverflow():void{$this->expectException(ProtocolError::class);Sdk::parse('provider','outcome','{"invocation_id":"i","state":"COMPLETED","output":1e400}');}
}
