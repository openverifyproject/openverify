<?php
declare(strict_types=1);
namespace OpenVerify;
final class ProtocolError extends \RuntimeException {
    public function __construct(public readonly string $errorCode, string $message = '', public readonly string $path = '') { parent::__construct($message ?: $errorCode); }
}
