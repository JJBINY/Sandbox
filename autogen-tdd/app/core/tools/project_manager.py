"""
프로젝트 디렉토리 및 파일 관리
"""
from pathlib import Path
from datetime import datetime
from app.config.settings import AppConfig


class ProjectManager:
    """프로젝트 관리자"""

    def __init__(self, config: AppConfig = None):
        self.config = config or AppConfig()

    def setup_work_directory(self, project_name: str) -> Path:
        """작업 디렉토리 설정"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        work_dir = Path(f"{self.config.GENERATED_PROJECTS_DIR}/{project_name}_{timestamp}")
        work_dir.mkdir(parents=True, exist_ok=True)

        # 기본 구조 생성
        (work_dir / "src").mkdir(exist_ok=True)
        (work_dir / "tests").mkdir(exist_ok=True)
        (work_dir / "docs").mkdir(exist_ok=True)

        # __init__.py 파일들 생성
        (work_dir / "src" / "__init__.py").touch()
        (work_dir / "tests" / "__init__.py").touch()

        return work_dir

    def read_current_code(self, work_dir: Path) -> str:
        """현재 작업 디렉토리의 코드 읽기"""
        code_content = []

        src_dir = work_dir / "src"
        for py_file in src_dir.glob("*.py"):
            if py_file.name != "__init__.py":
                with open(py_file, 'r', encoding='utf-8') as f:
                    code_content.append(f"# {py_file.name}\n{f.read()}")

        return "\n\n".join(code_content)