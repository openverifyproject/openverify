<?php
declare(strict_types=1);
namespace OpenVerify;
/** JSON object model preserving absent properties, null payloads and extensions. */
final class WireObject implements \JsonSerializable {
    public function __construct(public readonly \stdClass $data) {}
    public function jsonSerialize(): \stdClass { return $this->data; }
}
