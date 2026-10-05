# Native snapshot fixtures

These fictional examples are copied from the owning tools to exercise the native
snapshot profile. They are not historical research evidence.

- `bridgekeeper.json`: `examples/demo.json` at Bridgekeeper commit
  `91395c8b3e7c3ed58808faa23b81649b3f3f50b1`.
- `hingecheck.json`: `examples/demo.json` at Hingecheck commit
  `fc8d239636fcba6525c3d322316b45a9f467d42e`.

The tests exercise exact native JSON value preservation, changes versus corrections,
unresolved and superseded state, challenged assumptions and their dependents, unknown
extension fields, independent copies, mixed-origin merging, incompatible snapshot
collisions, namespace escaping, CLI round trips, and output overwrite refusal.

Run the commands in the main README from the repository root. Native validity stays
with the owning tool; Tracebridge transports the snapshot without interpreting it.
