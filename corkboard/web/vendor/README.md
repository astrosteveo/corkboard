# Vendored libraries

Committed as single files so the web app works offline with no build step. Each came from its npm tarball, checked against the registry's sha512 integrity.

| File | Package | License |
| --- | --- | --- |
| `preact.module.js` | preact 10.29.8, `dist/preact.module.js` | MIT, `preact.LICENSE` |
| `hooks.module.js` | preact 10.29.8, `hooks/dist/hooks.module.js` | MIT, `preact.LICENSE` |
| `htm.module.js` | htm 3.1.1, `dist/htm.module.js` | Apache-2.0, `htm.LICENSE` |
| `marked.esm.js` | marked 18.1.2, `lib/marked.esm.js` | MIT, `marked.LICENSE` |

Two changes from the published files:

- `hooks.module.js` imports `./preact.module.js` instead of the bare name `preact`, so the browser can load it without an import map. An inline import map would need an exception in the page's Content-Security-Policy.
- The `//# sourceMappingURL=` lines are removed, since the maps aren't committed.

To update one, download the new tarball from `https://registry.npmjs.org/<name>/-/<name>-<version>.tgz`, check it against `dist.integrity` from `https://registry.npmjs.org/<name>/<version>`, copy the same file, and make the same changes.
