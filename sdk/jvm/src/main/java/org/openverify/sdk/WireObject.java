package org.openverify.sdk;
import com.fasterxml.jackson.databind.node.ObjectNode;
/** JSON object model preserving absent properties, explicit null and extensions.
 * @param data object data; callers validate again after mutation */
public record WireObject(ObjectNode data) {}
