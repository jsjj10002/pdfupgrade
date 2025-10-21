"""
GPU/CPU 장치 관리 모듈

CUDA 가용성을 확인하고 최적의 디바이스를 선택한다.
"""

import subprocess
from typing import Optional

import torch

from .config import settings
from .logger import get_logger

logger = get_logger("device")


def check_nvidia_smi() -> bool:
    """
    nvidia-smi 명령어 실행 가능 여부 확인
    
    Returns:
        nvidia-smi 실행 가능하면 True, 아니면 False
    """
    try:
        result = subprocess.run(
            ["nvidia-smi"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_gpu_memory_info() -> Optional[dict]:
    """
    GPU 메모리 정보 조회
    
    Returns:
        GPU 메모리 정보 딕셔너리 또는 None
        {
            'total': 전체 메모리 (bytes),
            'used': 사용 중 메모리 (bytes),
            'free': 여유 메모리 (bytes)
        }
    """
    if not torch.cuda.is_available():
        return None
    
    try:
        device_id = int(settings.cuda_visible_devices.split(",")[0])
        total = torch.cuda.get_device_properties(device_id).total_memory
        reserved = torch.cuda.memory_reserved(device_id)
        allocated = torch.cuda.memory_allocated(device_id)
        free = total - reserved
        
        return {
            "total": total,
            "used": allocated,
            "free": free,
            "reserved": reserved,
        }
    except Exception as e:
        logger.warning(f"GPU 메모리 정보 조회 실패: {e}")
        return None


def get_device() -> torch.device:
    """
    최적의 디바이스 선택
    
    환경 변수 USE_GPU 값에 따라 결정:
    - 'true': 강제로 GPU 사용 (CUDA 없으면 CPU로 폴백)
    - 'false': 강제로 CPU 사용
    - 'auto': 자동 감지 (CUDA + nvidia-smi 있으면 GPU, 아니면 CPU)
    
    Returns:
        torch.device ('cuda:0' 또는 'cpu')
    """
    use_gpu = settings.use_gpu.lower()
    
    # 강제 CPU 모드
    if use_gpu == "false":
        logger.info("USE_GPU=false로 설정되어 CPU 사용")
        return torch.device("cpu")
    
    # 강제 GPU 모드
    if use_gpu == "true":
        if not torch.cuda.is_available():
            logger.warning("USE_GPU=true이지만 CUDA를 사용할 수 없어 CPU로 폴백")
            return torch.device("cpu")
        
        device_id = int(settings.cuda_visible_devices.split(",")[0])
        logger.info(f"USE_GPU=true로 설정되어 GPU 사용 (cuda:{device_id})")
        return torch.device(f"cuda:{device_id}")
    
    # 자동 감지 모드
    if not torch.cuda.is_available():
        logger.info("CUDA를 사용할 수 없어 CPU 사용")
        return torch.device("cpu")
    
    if not check_nvidia_smi():
        logger.warning("nvidia-smi를 실행할 수 없어 CPU 사용")
        return torch.device("cpu")
    
    device_id = int(settings.cuda_visible_devices.split(",")[0])
    
    # GPU 메모리 확인
    mem_info = get_gpu_memory_info()
    if mem_info:
        free_gb = mem_info["free"] / (1024**3)
        logger.info(f"GPU 감지됨 - 여유 메모리: {free_gb:.2f}GB")
        
        if free_gb < 1.0:
            logger.warning("GPU 여유 메모리가 1GB 미만이므로 CPU 사용")
            return torch.device("cpu")
    
    logger.info(f"GPU 사용 (cuda:{device_id})")
    return torch.device(f"cuda:{device_id}")


def clear_gpu_cache() -> None:
    """GPU 캐시 메모리 정리"""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        logger.debug("GPU 캐시 메모리 정리 완료")


def get_device_info() -> dict:
    """
    현재 디바이스 정보 반환
    
    Returns:
        디바이스 정보 딕셔너리
    """
    device = get_device()
    info = {
        "device": str(device),
        "cuda_available": torch.cuda.is_available(),
        "cuda_version": torch.version.cuda if torch.cuda.is_available() else None,
        "pytorch_version": torch.__version__,
    }
    
    if torch.cuda.is_available():
        device_id = device.index if device.type == "cuda" else 0
        props = torch.cuda.get_device_properties(device_id)
        info.update({
            "gpu_name": props.name,
            "gpu_memory_total_gb": props.total_memory / (1024**3),
            "gpu_compute_capability": f"{props.major}.{props.minor}",
        })
        
        mem_info = get_gpu_memory_info()
        if mem_info:
            info["gpu_memory_free_gb"] = mem_info["free"] / (1024**3)
    
    return info

