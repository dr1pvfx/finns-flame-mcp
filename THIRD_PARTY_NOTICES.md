# Third-party notices

## mcp-aftereffects

flame-mcp adapts the design and control flow of
[mcp-aftereffects](https://github.com/kumoproductions/mcp-aftereffects) by kumo.productions, Inc.
The following modules are Python ports of its TypeScript sources:

- `src/flame_mcp/registry.py` (from `src/registry.ts`)
- `src/flame_mcp/opschema.py` (from `src/opschema.ts`)
- `src/flame_mcp/policy.py` (from `src/policy.ts`)

mcp-aftereffects is distributed under the MIT License:

```
MIT License

Copyright (c) 2026 kumo.productions, Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Flame MCP upstreams

- [mnt0414/flame-mcp](https://github.com/mnt0414/flame-mcp/tree/8b07868c258e5f704639403499236771f9bc8d39)
  supplies the MCP server, operation registry, journal, local bridge, and their original tests.
  Its MIT text is preserved in [licenses/mnt0414-MIT.txt](licenses/mnt0414-MIT.txt).
- [abrahamADSK/flame-mcp](https://github.com/abrahamADSK/flame-mcp/tree/64472299292f3d165289ceaa9033970959ce72a5)
  supplies the source anchor diagnostic pattern and Flame delivery findings. Its MIT text
  is at [licenses/abrahamADSK-MIT.txt](licenses/abrahamADSK-MIT.txt).
- [Chris Nollert's forge-bridge](https://github.com/cnoellert/forge-bridge/tree/96312adf9f3b10a4c82f5c5cfca221feab35f24b)
  supplies the canonical fingerprint function and the propose, confirm, verify-before-apply
  design. The pinned project's package metadata declares GPL-3.0. The combined distribution is
  GPL-3.0-only.
- [djlevi/flame-mcp](https://github.com/djlevi/flame-mcp/commit/9e133d7014)
  supplied the system-library filtering idea, already present in Abraham's latest server.
  The two other public forks, iflow-mcp and internet-dot, had no commits ahead of the parent
  on their default branches at review. The separate internet-dot branch added a
  skill-publication CI workflow. No fork configuration, logs or generated indexes
  were imported.
