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

On Apple Silicon macOS, Flame 2027.1 loaded the installed hook and a disposable
local project. Native tests created a timeline, imported a synthetic picture
clip, placed it on the timeline and read the focused shot's source and record
timecodes. The anchor report flagged the movie's unknown source origin. A
rename preview left the timeline unchanged. An altered fingerprint produced
`CONFLICT`, the original fingerprint applied the rename, and `journal.revert`
restored the original name. Local tracing correlated the rename and journal
group without recording object names or file paths.

The native test also reproduced intermittent queued main-thread timeouts.
Opening the floating assistant and keeping it active allowed the checks above
to complete and a native export to write one ProRes movie. An independent
decode of a reference frame and its exported counterpart measured a mean
luma difference of 1.469 on a 0–255 scale at 640 × 360. Reliable unattended
dispatch on 2027.1 remains unqualified.
