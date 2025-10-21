"""
워터마크 제거 기능 테스트 스크립트

워터마크 탐지 및 제거 기능을 테스트한다.
"""

from PIL import Image, ImageDraw, ImageFont
import numpy as np

from app.pipeline.watermark import remove_watermark_simple


def create_test_image_with_watermark():
    """워터마크가 있는 테스트 이미지 생성"""
    # 흰색 배경 이미지
    img = Image.new("RGB", (800, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # 본문 텍스트 추가 (검은색)
    texts = [
        "This is a sample document.",
        "It contains some text content.",
        "And we will add a watermark to it.",
    ]
    
    y_pos = 50
    for text in texts:
        draw.text((50, y_pos), text, fill=(0, 0, 0))
        y_pos += 100
    
    # 워터마크 추가 (반투명 회색, 대각선)
    watermark = Image.new("RGBA", img.size, (0, 0, 0, 0))
    wm_draw = ImageDraw.Draw(watermark)
    
    # 큰 텍스트로 워터마크 (반투명)
    wm_text = "WATERMARK"
    # 시스템 기본 폰트 사용
    wm_draw.text((300, 250), wm_text, fill=(128, 128, 128, 128))
    
    # 회전
    watermark = watermark.rotate(30, expand=False)
    
    # 원본 이미지와 합성
    img = Image.alpha_composite(img.convert("RGBA"), watermark).convert("RGB")
    
    return img


def test_watermark_removal():
    """워터마크 제거 테스트"""
    print("워터마크 제거 테스트 시작...")
    
    # 테스트 이미지 생성
    test_img = create_test_image_with_watermark()
    print(f"테스트 이미지 생성: {test_img.size}")
    
    # 원본 저장 (선택적)
    test_img.save("test_watermark_before.png")
    print("원본 이미지 저장: test_watermark_before.png")
    
    # 워터마크 제거
    print("\n워터마크 제거 중...")
    result = remove_watermark_simple(test_img, method="auto")
    
    # 결과 저장
    result.save("test_watermark_after.png")
    print("결과 이미지 저장: test_watermark_after.png")
    
    print("\n테스트 완료!")
    print("before와 after 이미지를 비교해보세요.")


if __name__ == "__main__":
    test_watermark_removal()

