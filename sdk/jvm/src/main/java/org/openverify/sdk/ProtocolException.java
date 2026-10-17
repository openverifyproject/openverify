package org.openverify.sdk;
/** Protocol error with a stable code independent of diagnostic text. */
public final class ProtocolException extends RuntimeException {
 private final String code;
 /** Construct a protocol failure. @param code stable classification */
 public ProtocolException(String code) { super(code); this.code=code; }
 /** @return protocol code; SDK_UNSUPPORTED is a local SDK diagnostic */
 public String code(){return code;}
 /** @return JSON Pointer when available */
 public String path(){return "";}
}
