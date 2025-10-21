"""
API 서버 테스트 스크립트

FastAPI 서버의 주요 기능을 테스트한다.
"""

import requests
import time
from pathlib import Path


BASE_URL = "http://localhost:8000"


def test_health():
    """헬스 체크 테스트"""
    print("=== 헬스 체크 ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"상태 코드: {response.status_code}")
    print(f"응답: {response.json()}")
    print()


def test_upload(file_path: str):
    """파일 업로드 테스트"""
    print("=== 파일 업로드 ===")
    
    with open(file_path, "rb") as f:
        files = {"file": (Path(file_path).name, f, "application/pdf")}
        response = requests.post(f"{BASE_URL}/api/upload", files=files)
    
    print(f"상태 코드: {response.status_code}")
    print(f"응답: {response.json()}")
    print()
    
    if response.status_code == 200:
        return response.json()["filename"]
    return None


def test_process(filename: str):
    """PDF 처리 작업 생성 테스트"""
    print("=== 처리 작업 생성 ===")
    
    payload = {
        "options": {
            "dpi": 300,
            "preprocess": True,
            "deskew": True,
            "white_balance": True,
            "enhance_contrast": True,
            "upscale": False,  # 빠른 테스트를 위해 비활성화
            "watermark": False,
            "ocr": True,
            "ocr_engine": "paddle",
            "ocr_langs": "kor+eng",
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/process/{filename}",
        json=payload,
    )
    
    print(f"상태 코드: {response.status_code}")
    print(f"응답: {response.json()}")
    print()
    
    if response.status_code == 200:
        return response.json()["task_id"]
    return None


def test_task_status(task_id: str):
    """작업 상태 조회 테스트"""
    print("=== 작업 상태 조회 ===")
    
    while True:
        response = requests.get(f"{BASE_URL}/api/tasks/{task_id}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"상태: {data['status']}")
            print(f"진행률: {data['progress']:.1f}%")
            print(f"메시지: {data.get('message', 'N/A')}")
            
            if data["status"] in ["completed", "failed"]:
                print(f"\n최종 응답: {data}")
                break
        else:
            print(f"오류: {response.status_code}")
            break
        
        time.sleep(2)
    
    print()


def test_download(task_id: str):
    """결과 다운로드 테스트"""
    print("=== 결과 다운로드 ===")
    
    response = requests.get(f"{BASE_URL}/api/tasks/{task_id}/download")
    
    if response.status_code == 200:
        output_path = f"test_result_{task_id[:8]}.pdf"
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"결과 저장: {output_path}")
    else:
        print(f"다운로드 실패: {response.status_code}")
    
    print()


def main():
    """전체 테스트 실행"""
    print("====================================")
    print("   PDF Upgrade API 테스트")
    print("====================================\n")
    
    # 1. 헬스 체크
    test_health()
    
    # 2. 파일 업로드
    test_file = "test.pdf"  # 테스트할 PDF 파일 경로
    
    if not Path(test_file).exists():
        print(f"오류: 테스트 파일이 없습니다: {test_file}")
        print("test.pdf 파일을 준비하고 다시 실행하세요.")
        return
    
    filename = test_upload(test_file)
    
    if not filename:
        print("파일 업로드 실패")
        return
    
    # 3. 처리 작업 생성
    task_id = test_process(filename)
    
    if not task_id:
        print("작업 생성 실패")
        return
    
    # 4. 작업 상태 폴링
    test_task_status(task_id)
    
    # 5. 결과 다운로드
    test_download(task_id)
    
    print("====================================")
    print("   테스트 완료!")
    print("====================================")


if __name__ == "__main__":
    main()

