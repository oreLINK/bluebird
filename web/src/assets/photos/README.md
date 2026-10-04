# Photos

Photos shown in the banner of `banner` and `banner_full` tiles, bundled by
Vite at build time (hashed file names, no runtime lookup).

```
photos/
├── credits.yaml                     # author and licence of every photo
└── <massif_id>/                     # e.g. pyrenees
    └── <station_id>/                # one folder per station, e.g. cauterets
        ├── <station_id>_1.jpg       # photos named <station_id>_<n>, n = 1, 2, 3…
        └── <station_id>_2.webp
```

| Tile option (`config/tiles.yaml`) | Photo used |
|---|---|
| `photo: leader` | a random `<massif_id>/<station_id>/<station_id>_<n>.*` of the station ranked first (drawn once per page load) |
| `photo: <path>` | the file at `<path>.*` (path relative to this folder, no extension) |
| `photo: none` (default) | none: the tile shows its illustration |

- Formats: `.webp` (preferred), `.jpg`, `.jpeg`, `.png`, `.avif`.
- Size: landscape, at least 1200 × 600 px, ideally under 300 KB.
- `<station_id>` is the `id` in `config/stations/<massif>.yaml`; `<n>` is any
  number (no gaps required). A test checks that every station has its folder
  and that every photo in it is named `<station_id>_<n>`.
- Every photo needs publication rights and an entry in `credits.yaml`
  (key: path without extension, e.g. `pyrenees/cauterets/cauterets_1`). The
  credit is shown on the tile back and on the legal notice page, not on the
  banner. A credit line does not give the right to publish: photos from
  resort, tourism or review sites are usually all rights reserved.
- A missing photo is not an error: the tile shows its illustration instead.
- When you add a station, create its folder (with a `.gitkeep` until it has a photo).
