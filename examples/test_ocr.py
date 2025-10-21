"""
OCR 기능 테스트 스크립트

PaddleOCR 텍스트 인식 기능을 테스트한다.
"""

from PIL import Image, ImageDraw, ImageFont

from app.pipeline.ocr import ocr_image_simple


def create_test_image_with_text():
    """테스트용 텍스트 이미지 생성"""
    # 흰색 배경 이미지
    img = Image.new("RGB", (800, 400), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # 텍스트 추가 (시스템 기본 폰트 사용)
    texts = [
        "안녕하세요, PDF Upgrade입니다.",
        "Hello, this is a test image.",
        "한글과 English를 함께 인식합니다.",
    ]
    
    y_pos = 50
    for text in texts:
        draw.text((50, y_pos), text, fill=(0, 0, 0))
        y_pos += 100
    
    return img


def test_ocr():
    """OCR 테스트"""
    print("OCR 테스트 시작...")
    
    # 테스트 이미지 생성
    test_img = create_test_image_with_text()
    print(f"테스트 이미지 생성: {test_img.size}")
    
    # OCR 실행
    print("\nPaddleOCR 실행 중...")
    results = ocr_image_simple(test_img, engine="paddle", langs="kor+eng")
    
    # 결과 출력
    print(f"\n인식된 텍스트: {len(results)}개")
    print("-" * 60)
    
    for idx, item in enumerate(results, 1):
        print(f"{idx}. 텍스트: {item['text']}")
        print(f"   신뢰도: {item['confidence']:.2f}")
        print(f"   위치: {item['bbox']}")
        print()
    
    print("테스트 완료!")
    
    # 이미지 저장 (선택적)
    # test_img.save("test_ocr_input.png")


if __name__ == "__main__":
    test_ocr()

