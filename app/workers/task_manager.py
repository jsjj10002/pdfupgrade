"""
작업 관리자

작업 생성, 상태 관리, 실행 관리
"""

import uuid
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict
from queue import Queue

from app.api.schemas import TaskStatus
from app.utils.config import get_settings
from app.utils.logger import get_logger
from app.pipeline.pipeline import Processor

settings = get_settings()
logger = get_logger("task_manager")


class TaskManager:
    """
    작업 관리자 (싱글톤)
    
    작업 생성, 큐 관리, 상태 추적을 담당한다.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, "_initialized"):
            self.tasks: Dict[str, TaskStatus] = {}
            self.task_queue: Queue = Queue()
            self.workers: list[threading.Thread] = []
            self._initialized = True
            
            # 워커 스레드 시작
            self._start_workers()
            
            logger.info("작업 관리자 초기화 완료")
    
    def _start_workers(self):
        """워커 스레드 시작"""
        num_workers = min(settings.MAX_CONCURRENCY, 4)
        
        for i in range(num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"Worker-{i}",
                daemon=True,
            )
            worker.start()
            self.workers.append(worker)
        
        logger.info(f"워커 {num_workers}개 시작")
    
    def _worker_loop(self):
        """워커 루프 (백그라운드 스레드)"""
        while True:
            try:
                # 큐에서 작업 가져오기
                task_id, input_file, options = self.task_queue.get()
                
                if task_id is None:
                    break
                
                logger.info(f"작업 시작: {task_id}")
                
                # 작업 실행
                self._execute_task(task_id, input_file, options)
                
                self.task_queue.task_done()
            
            except Exception as e:
                logger.exception(f"워커 오류: {e}")
    
    def _execute_task(self, task_id: str, input_file: str, options: dict):
        """작업 실행"""
        try:
            # 작업 상태 업데이트: 처리 중
            self._update_task_status(
                task_id,
                status="processing",
                progress=0.0,
                message="처리 시작...",
            )
            
            # 출력 디렉터리
            output_dir = Path(settings.STORAGE_DIR) / "results"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 출력 파일명
            input_path = Path(input_file)
            output_file = output_dir / f"{task_id}_{input_path.stem}_processed.pdf"
            
            # PDF 처리
            processor = Processor(options=options)
            
            # 진행률 콜백
            def progress_callback(step: str, progress: float):
                self._update_task_status(
                    task_id,
                    status="processing",
                    progress=progress,
                    message=f"{step} 중...",
                )
            
            # 실행
            processor.run(
                pdf_path=input_file,
                output_path=str(output_file),
                progress_callback=progress_callback,
            )
            
            # 완료
            file_size = output_file.stat().st_size
            
            self._update_task_status(
                task_id,
                status="completed",
                progress=100.0,
                message="처리 완료",
                result_file=str(output_file),
                file_size=file_size,
                completed_at=datetime.now(),
            )
            
            logger.info(f"작업 완료: {task_id}")
        
        except Exception as e:
            logger.exception(f"작업 실패: {task_id} - {e}")
            
            self._update_task_status(
                task_id,
                status="failed",
                message=f"처리 실패: {str(e)}",
                error=str(e),
                completed_at=datetime.now(),
            )
    
    def create_task(self, input_file: str, options: dict) -> str:
        """
        새 작업 생성
        
        Args:
            input_file: 입력 PDF 파일 경로
            options: 처리 옵션
        
        Returns:
            작업 ID
        """
        task_id = str(uuid.uuid4())
        
        # 작업 상태 초기화
        now = datetime.now()
        task_status = TaskStatus(
            task_id=task_id,
            status="pending",
            progress=0.0,
            message="대기 중...",
            created_at=now,
            updated_at=now,
        )
        
        self.tasks[task_id] = task_status
        
        # 큐에 추가
        self.task_queue.put((task_id, input_file, options))
        
        logger.info(f"작업 생성: {task_id}")
        
        return task_id
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """
        작업 상태 조회
        
        Args:
            task_id: 작업 ID
        
        Returns:
            작업 상태 (없으면 None)
        """
        return self.tasks.get(task_id)
    
    def _update_task_status(
        self,
        task_id: str,
        status: Optional[str] = None,
        progress: Optional[float] = None,
        message: Optional[str] = None,
        result_file: Optional[str] = None,
        file_size: Optional[int] = None,
        error: Optional[str] = None,
        completed_at: Optional[datetime] = None,
    ):
        """작업 상태 업데이트"""
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]
        
        if status is not None:
            task.status = status
        if progress is not None:
            task.progress = progress
        if message is not None:
            task.message = message
        if result_file is not None:
            task.result_file = result_file
        if file_size is not None:
            task.file_size = file_size
        if error is not None:
            task.error = error
        if completed_at is not None:
            task.completed_at = completed_at
        
        task.updated_at = datetime.now()
    
    def delete_task(self, task_id: str) -> bool:
        """
        작업 삭제
        
        Args:
            task_id: 작업 ID
        
        Returns:
            삭제 성공 여부
        """
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        
        # 결과 파일 삭제
        if task.result_file:
            try:
                Path(task.result_file).unlink(missing_ok=True)
            except Exception as e:
                logger.error(f"결과 파일 삭제 실패: {e}")
        
        # 작업 삭제
        del self.tasks[task_id]
        
        logger.info(f"작업 삭제: {task_id}")
        
        return True
    
    def shutdown(self):
        """워커 종료"""
        logger.info("작업 관리자 종료 중...")
        
        # 종료 신호 전송
        for _ in self.workers:
            self.task_queue.put((None, None, None))
        
        # 모든 워커 종료 대기
        for worker in self.workers:
            worker.join(timeout=5.0)
        
        logger.info("작업 관리자 종료 완료")


# 싱글톤 인스턴스
task_manager = TaskManager()

