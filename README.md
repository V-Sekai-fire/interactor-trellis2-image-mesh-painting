# interactor-trellis2-image-mesh-painting

Model image for `trellis2_image_mesh_painting`, per
[weftspun's RFD 0036](https://github.com/weftspun/request-for-discussion/tree/main/0036-packaging-convention)
packaging convention. Facts from
[RFD 0039](https://github.com/weftspun/request-for-discussion/tree/main/0039-trellis2-image-mesh-painting).

## Model

| Property   | Value                                                                                                                                                  |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Upstream   | [microsoft/TRELLIS.2](https://github.com/microsoft/TRELLIS.2), `Trellis2TexturingPipeline`                                                             |
| License    | MIT                                                                                                                                                    |
| Parameters | 0 — shares [`interactor-trellis2-image-to-textured-mesh`](https://github.com/weftspun/interactor-trellis2-image-to-textured-mesh)'s weights (RFD 0038) |
| bf16       | 8.0 GB, and that is the RFD 0038 cost, not a second copy                                                                                               |

## Interface

`POST /predict`:

| Input                | Type                  | Default  | Note |
| -------------------- | --------------------- | -------- | ---- |
| `mesh`               | Path/URL/base64 (GLB) | required |      |
| `image`              | Path/URL/base64       | required |      |
| `texture_resolution` | int                   | 1024     |      |
| `seed`               | int                   | -1       |      |

Returns `{glb, layer, seed, stub}`.

## The one hard part (RFD 0039)

The mesh arrives with its own UV layout, or with none. Painting needs a layout — when the mesh
has no UV set, run `xatlas` first (RFD 0033 records it, no weights). **Do not unwrap inside this
model image** — a hidden unwrap makes the output depend on a step the caller can't see or
repeat. This server does not implement that pre-check yet; see "Status".

## Build

Builds `FROM` `weftspun/trellis2-base`'s worker stage — the base image must be built first. No
weights of its own, so the delta image is small (~40 MB).

```sh
docker build --target contract -t interactor-trellis2-image-mesh-painting:contract .
docker run --rm -p 8000:8000 interactor-trellis2-image-mesh-painting:contract
curl -X POST localhost:8000/predict -d @test_input.json -H 'Content-Type: application/json'
```

## Status

**Scaffolded from the RFD, not yet built or run.** `_run_upstream()` calls
`Trellis2TexturingPipeline`, TRELLIS.2's own real texturing entry point (`app_texturing.py`'s
Gradio demo calls the same class) — checked against the upstream repo, not invented. **Not
implemented**: the `xatlas` UV pre-check RFD 0039 requires when the input mesh has no UV
layout. Add it before this image handles a real UV-less mesh.
