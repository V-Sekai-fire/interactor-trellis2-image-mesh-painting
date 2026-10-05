# interactor-trellis2-image-mesh-painting

A model image that paints an existing mesh from a reference image and returns the textured mesh.

## Use

The image serves one prediction endpoint over HTTP. It carries no weights of its own and builds on the base image of `interactor-trellis2-image-to-textured-mesh`, so the two share one copy. [RFD 1039](https://github.com/V-Sekai-fire/manuals-weftspun/tree/main/rfd/1039-trellis2-image-mesh-painting) owns its interface, including the UV layout a caller supplies, and [RFD 1036](https://github.com/V-Sekai-fire/manuals-weftspun/tree/main/rfd/1036-packaging-convention) its packaging.

## Build and run

The `contract` stage builds a stub server that answers with the interface's shape and needs no GPU:

```sh
docker build --target contract -t interactor-trellis2-image-mesh-painting:contract .
docker run --rm -p 8000:8000 interactor-trellis2-image-mesh-painting:contract
```

The server listens on the port `PORT` names.

The worker stage needs the base image built first.

## Licence

This repository states no licence. The upstream model is MIT.
