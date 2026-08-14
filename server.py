"""TRELLIS.2 mesh painting: an existing mesh + a reference image -> a
textured mesh. RFD 0039.

Shares microsoft/TRELLIS.2-4B's weights with interactor-trellis2-image-to-
textured-mesh (RFD 0038) -- no weights of its own, RFD 0039's whole reason
for existing ("a second copy of those weights costs 8.0 GB and buys
nothing"). The image build FROM's the base image and adds no weights.

`_run_upstream` is `Trellis2TexturingPipeline`, TRELLIS.2's own texturing
entry point (`app_texturing.py`'s Gradio app calls the same class) -- checked
against the real upstream repo, not invented.
"""

import base64
import os
import tempfile
import urllib.request
from pathlib import Path

WEIGHTS = os.environ.get("TRELLIS2_WEIGHTS", "microsoft/TRELLIS.2-4B")

STUB = os.environ.get("WEFTSPUN_STUB") == "1"

_READY = {"loaded": False}
_PIPELINE = {"pipeline": None}


class InputError(ValueError):
    """The request is wrong. This is the caller's fault, and not ours."""


def _fetch(value: str, work: Path, name: str) -> Path:
    target = work / name
    if value.startswith(("http://", "https://")):
        urllib.request.urlretrieve(value, target)
        return target
    if value.startswith("data:"):
        value = value.split(",", 1)[1]
    target.write_bytes(base64.b64decode(value))
    return target


def _validate(job_input: dict) -> dict:
    if not job_input.get("mesh"):
        raise InputError("mesh is required: a URL, a data URI, or base64 GLB bytes")
    if not job_input.get("image"):
        raise InputError("image is required: a URL, a data URI, or base64")

    texture_resolution = int(job_input.get("texture_resolution", 1024))
    if texture_resolution not in (512, 1024, 2048, 4096):
        raise InputError("texture_resolution must be 512, 1024, 2048, or 4096")

    return {
        "mesh": job_input["mesh"],
        "image": job_input["image"],
        "texture_resolution": texture_resolution,
        "seed": int(job_input.get("seed", -1)),
    }


def _run_upstream(mesh_path: Path, image_path: Path, glb: Path, args: dict) -> None:
    """The real TRELLIS.2 texturing API (`app_texturing.py`'s
    `Trellis2TexturingPipeline`, the class its own Gradio demo calls):

        pipeline = Trellis2TexturingPipeline.from_pretrained(
            "microsoft/TRELLIS.2-4B", config_file="texturing_pipeline.json")
        output = pipeline.run(mesh, image, seed=..., preprocess_image=False,
                               resolution=..., texture_size=...)
        output.export(path, extension_webp=True)
    """
    import trimesh
    from PIL import Image
    from trellis2.pipelines import Trellis2TexturingPipeline

    if _PIPELINE["pipeline"] is None:
        _PIPELINE["pipeline"] = Trellis2TexturingPipeline.from_pretrained(
            WEIGHTS, config_file="texturing_pipeline.json"
        )
    pipeline = _PIPELINE["pipeline"]

    mesh = trimesh.load(str(mesh_path))
    if isinstance(mesh, trimesh.Scene):
        mesh = mesh.to_mesh()
    image = Image.open(image_path)

    output = pipeline.run(
        mesh,
        image,
        seed=args["seed"],
        preprocess_image=False,
        resolution=1024,
        texture_size=args["texture_resolution"],
    )
    output.export(str(glb), extension_webp=True)


def _to_usd(glb: Path, work: Path) -> Path:
    """RFD 0053. Records the GLB as an asset path -- plain usd-core has no
    glTF file-format plugin (RFD 0040's finding)."""
    from pxr import Sdf, Usd, UsdGeom

    layer = work / "layer.usda"
    stage = Usd.Stage.CreateNew(str(layer))
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    root = UsdGeom.Xform.Define(stage, "/Asset")
    stage.SetDefaultPrim(root.GetPrim())
    geometry = stage.DefinePrim("/Asset/Geometry")
    geometry.CreateAttribute("weftspun:sourceAsset", Sdf.ValueTypeNames.Asset).Set(
        Sdf.AssetPath(glb.name)
    )
    geometry.CreateAttribute("weftspun:sourceFormat", Sdf.ValueTypeNames.Token).Set("gltf")
    geometry.CreateAttribute("weftspun:stage", Sdf.ValueTypeNames.Token).Set(
        "trellis2_image_mesh_painting"
    )
    stage.GetRootLayer().Save()
    return layer


def _encode(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def predict(job_input: dict) -> dict:
    args = _validate(job_input)
    work = Path(tempfile.mkdtemp())
    mesh_path = _fetch(args["mesh"], work, "input.glb")
    image_path = _fetch(args["image"], work, "input.png")
    glb = work / "output.glb"

    if STUB:
        glb.write_bytes(bytes([0x67, 0x6C, 0x54, 0x46, 0x02]) + b"stub")
    else:
        _run_upstream(mesh_path, image_path, glb, args)

    layer = _to_usd(glb, work)

    return {
        "glb": _encode(glb),
        "layer": _encode(layer),
        "seed": args["seed"],
        "stub": STUB,
    }


def load() -> None:
    _READY["loaded"] = True


def build_app():
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel

    app = FastAPI(title="trellis2_image_mesh_painting", version="0.1.0")

    class PredictRequest(BaseModel):
        mesh: str
        image: str
        texture_resolution: int = 1024
        seed: int = -1

    @app.get("/health")
    def health():
        return {"status": "ok", "ready": _READY["loaded"], "stub": STUB}

    @app.post("/predict")
    def run(request: PredictRequest):
        try:
            return predict(request.model_dump())
        except InputError as error:
            return JSONResponse(status_code=400, content={"error": str(error)})

    return app


if __name__ == "__main__":
    import uvicorn

    load()
    uvicorn.run(build_app(), host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
