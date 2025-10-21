"""
업스케일 기능 테스트 스크립트

Real-ESRGAN 업스케일 기능을 테스트한다.
"""

from pathlib import Path
from PIL import Image

from app.pipeline.upscale import upscale_image_simple


def test_upscale():
    """업스케일 테스트"""
    # 테스트 이미지 생성 (또는 기존 이미지 로드)
    test_img = Image.new("RGB", (256, 256), color=(73, 109, 137))
    
    print("업스케일 테스트 시작...")
    print(f"원본 크기: {test_img.size}")
    
    # x2 업스케일
    upscaled_x2 = upscale_image_simple(test_img, scale=2)
    print(f"x2 업스케일 완료: {upscaled_x2.size}")
    
    # x4 업스케일
    upscaled_x4 = upscale_image_simple(test_img, scale=4)
    print(f"x4 업스케일 완료: {upscaled_x4.size}")
    
    print("테스트 완료!")


if __name__ == "__main__":
    test_upscale()

