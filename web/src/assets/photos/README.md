# Photos

Photos shown in the image of `full` and `banner` tiles, bundled by
Vite at build time (hashed file names, no runtime lookup).

```
photos/
├── credits.yaml                     # author and licence of every photo
└── <massif_id>/                     # e.g. pyrenees
    └── <station_id>/                # one folder per station, e.g. cauterets
        ├── <station_id>_1.jpg       # photos named <station_id>_<n>, n = 1, 2, 3…
        └── <station_id>_2.webp
```

| Tile field (`config/tiles.yaml`) | Photo used |
|---|---|
| `visual: photo` | a random `<massif_id>/<station_id>/<station_id>_<n>.*` of the station ranked first (drawn once per page load), else the illustration |
| `visual: scene` (default) | none: the tile shows its illustration (option `scene`) |

Webcam images are never bundled nor shown: a tile with a `webcam` rule only
links the webcam's official page from a LIVE badge.

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

## Where photos come from

Photos are found with [Openverse](https://openverse.org/fr), the search
engine of openly licensed images (Wikimedia Commons, Flickr…), and are free
to reuse under their licence. Openverse lists several licences, so check
each image:

| Licence | Use it? |
|---|---|
| CC0, Public Domain Mark | Yes, no credit required (credit it anyway in `credits.yaml`). |
| CC BY, CC BY-SA | Yes, with the author, licence and source in `credits.yaml` (BY-SA: the resized image stays under BY-SA). |
| CC BY-NC (-SA) | Only while the site stays non-commercial; prefer another image. |
| Any ND licence (BY-ND, BY-NC-ND) | No: resizing or cropping is a modification. |

Open the source page (the "Source" link of Openverse, often Wikimedia
Commons) to confirm the licence and the author before adding the photo, and
prefer winter photos with snow. Keep the source URL in `credits.yaml`, and
note any change you made (resized, converted to WebP) in a comment above the
entry.
- When you add a station, create its folder (with a `.gitkeep` until it has a photo).
