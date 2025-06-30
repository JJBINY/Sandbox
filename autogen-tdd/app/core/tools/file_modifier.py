import os
import tempfile
import shutil
from contextlib import contextmanager
import git

class SafeFileModifier:
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.repo = git.Repo(project_path)
        self.backup_manager = BackupManager(project_path)
        
    @contextmanager
    def atomic_modify(self, file_path: str):
        """원자적 파일 수정을 위한 컨텍스트 매니저"""
        # 백업 생성
        backup_path = self.backup_manager.create_backup(file_path)
        
        try:
            # 임시 파일에서 작업
            temp_dir = os.path.dirname(file_path)
            with tempfile.NamedTemporaryFile(
                mode='w', 
                dir=temp_dir, 
                delete=False,
                suffix='.tmp'
            ) as tmp_file:
                yield tmp_file
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
                
            # 원자적 교체
            os.replace(tmp_file.name, file_path)
            
        except Exception as e:
            # 오류 시 백업에서 복구
            shutil.copy2(backup_path, file_path)
            raise e
        finally:
            # 정리
            if os.path.exists(tmp_file.name):
                os.unlink(tmp_file.name)
                
    async def apply_code_changes(self, file_path: str, changes: Dict):
        """에이전트가 제안한 코드 변경사항 적용"""
        with self.atomic_modify(file_path) as tmp_file:
            # 기존 코드 읽기
            with open(file_path, 'r') as original:
                content = original.read()
                
            # 변경사항 적용
            modified_content = self.apply_changes(content, changes)
            
            # 임시 파일에 쓰기
            tmp_file.write(modified_content)
            
        # Git 커밋으로 변경사항 추적
        self.repo.git.add(file_path)
        self.repo.index.commit(f"Agent modification: {changes.get('description', 'Auto commit')}")