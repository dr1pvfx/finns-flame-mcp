# Qualification

The inherited native regression suite reports author tests on Flame 2025.2.4
and 2026.2.3. These are upstream results. Re-run native scene tests on your
installed Flame release before making timeline writes in live work.

The release-specific tests in `tests/test_finns_extensions.py` verify stale
approval, journaled rename readback, source anchor diagnosis, and trace redaction.
`scripts/qt_bridge_probe.py` uses the native Qt event loop and the real stdio and
Unix socket transports with synthetic objects outside Flame. Use Flame's bundled
PySide6 for the latter:

```sh
python -m pytest -q tests/test_finns_extensions.py
/path/to/python-with-pyside6 scripts/qt_bridge_probe.py
```

For native checks, install the hook, open a disposable Flame project with synthetic
media, and use `flame_version_info` to confirm bridge version and project. Verify
the focused shot against the saved source and record timecodes. Rename a timeline
through the preview and application operations, verify the new name in Flame,
revert the resulting journal group, and confirm the old name. Verify that a
changed target or altered fingerprint is rejected before a write. Retain the
local trace and compare the journal group shown in the apply result.

## 0.5.0 preview

On Apple Silicon macOS, Flame 2027.1 registered the installed hook. Using
Flame's bundled Python 3.13 and Qt 6.8.3 outside the application, synthetic
focused-shot and anchor calls passed through the stdio client, Unix socket,
and Qt main-thread dispatcher. The trace recorded outcomes without shot names.
The real Flame project chooser rejected the restored synthetic project on the
test station. Live scene writes and render comparisons remain unqualified
for 2027.1 in this distribution.
