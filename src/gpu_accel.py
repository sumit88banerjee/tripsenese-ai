import os


def install_gpu_acceleration() -> str:
    """
    Enables NVIDIA RAPIDS cudf.pandas only when requested.

    """
    use_gpu = os.getenv("TRIPSENSE_USE_GPU", "false").lower() in {
        "1", "true", "yes", "gpu", "rapids"
    }

    if not use_gpu:
        return "cpu-pandas"

    try:
        import cudf.pandas
        cudf.pandas.install()
        return "gpu-rapids-cudf-pandas"
    except Exception as exc:
        print(f"[TripSenseAI] RAPIDS unavailable, falling back to CPU pandas: {exc}")
        return "cpu-pandas-fallback"