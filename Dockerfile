# interactor-trellis2-image-mesh-painting -- vast.ai worker, RFD 0036/0039.
#
# Derives from interactor-trellis2-image-to-textured-mesh (RFD 0038). Adds no
# weights -- RFD 0039's whole reason for existing: a second copy of TRELLIS.2's
# 8.0 GB costs disk and buys nothing. This image is ~40 MB on top of the base.
#
# Build the base image first (weftspun/trellis2-base), then:
#   docker build -t weftspun/trellis2-painting .
# Test the handler contract with no GPU:
#   docker build --target contract -t weftspun/trellis2-painting:contract .
#   docker run --rm -p 8000:8000 weftspun/trellis2-painting:contract

FROM python:3.11-slim AS contract
WORKDIR /app
RUN pip install --no-cache-dir usd-core==25.5 fastapi==0.115.5 uvicorn==0.32.1 pydantic==2.10.3
COPY server.py /app/server.py
COPY test_input.json /app/test_input.json
ENV WEFTSPUN_STUB=1 PORT=8000
EXPOSE 8000
CMD ["python", "/app/server.py"]

# The worker stage builds FROM the base image's worker stage, not from a bare
# CUDA image -- it needs TRELLIS.2's Python package and weights already
# present, and re-downloading them here would be exactly the duplication
# RFD 0039 exists to avoid.
FROM weftspun/trellis2-base AS worker

WORKDIR /app
COPY server.py /app/server.py

ENV PORT=8000
EXPOSE 8000

CMD ["python3", "-u", "/app/server.py"]
