from dataclasses import dataclass


@dataclass(frozen=True)
class CudaStatus:
    available: bool
    device_name: str = "CPU only"
    message: str = ""


def detect_cuda_status(torch_module=None) -> CudaStatus:
    try:
        torch = torch_module
        if torch is None:
            import torch  # noqa: PLC0415

        if torch.cuda.is_available():
            return CudaStatus(
                available=True,
                device_name=torch.cuda.get_device_name(0),
                message="CUDA detected. Object detection will use GPU acceleration.",
            )
    except Exception as exc:  # noqa: BLE001 - startup should not fail on GPU probing.
        return CudaStatus(
            available=False,
            message=f"CUDA check failed ({exc}). CPU inference will be used.",
        )

    return CudaStatus(
        available=False,
        message="CUDA was not detected. CPU inference will be used; CUDA is recommended for a good experience.",
    )
