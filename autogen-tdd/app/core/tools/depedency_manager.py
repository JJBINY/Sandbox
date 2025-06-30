"""
TDD 시스템용 의존성 관리 모듈
app/core/tools/dependency_manager.py
"""
import subprocess
import sys
import os
import json
import re
import importlib.util
from typing import List, Dict, Optional, Tuple, Set
from pathlib import Path


class AutoDependencyInstaller:
    """
    TDD 시스템을 위한 자동 의존성 설치기
    """
    
    def __init__(self, project_path: str, auto_install: bool = True, 
                 ask_permission: bool = False, venv_path: Optional[str] = None):
        """
        Args:
            project_path: 프로젝트 루트 경로
            auto_install: 자동 설치 여부
            ask_permission: 설치 전 사용자 동의 확인 여부 (TDD에서는 False 권장)
            venv_path: 가상환경 경로 (None이면 자동 감지)
        """
        self.project_path = Path(project_path)
        self.auto_install = auto_install
        self.ask_permission = ask_permission
        self.venv_path = self._detect_venv(venv_path)
        self.requirements_file = self.project_path / "requirements.txt"
        
        # TDD에 안전한 패키지 목록 (확장 가능)
        self.safe_packages: Set[str] = {
            'pygame', 'numpy', 'pandas', 'matplotlib', 'seaborn',
            'requests', 'flask', 'django', 'fastapi', 'pytest',
            'black', 'flake8', 'mypy', 'click', 'rich', 'tqdm',
            'pillow', 'opencv-python', 'scikit-learn', 'tensorflow',
            'torch', 'transformers', 'beautifulsoup4', 'lxml',
            'sqlalchemy', 'redis', 'celery', 'gunicorn', 'uvicorn',
            'pydantic', 'typer', 'httpx', 'aiohttp', 'asyncio',
            'pytest-asyncio', 'pytest-cov', 'coverage'
        }
        
        # 설치된 패키지 캐시
        self._installed_packages_cache: Optional[Dict[str, str]] = None
        
        # 로깅을 위한 통계
        self.installation_history: List[Dict] = []
    
    def _detect_venv(self, venv_path: Optional[str]) -> Optional[str]:
        """가상환경 경로 자동 감지"""
        if venv_path:
            return venv_path
            
        # 일반적인 가상환경 경로들 확인
        possible_paths = [
            self.project_path / ".venv",
            self.project_path / "venv", 
            self.project_path / "env",
            Path(os.environ.get('VIRTUAL_ENV', '')) if 'VIRTUAL_ENV' in os.environ else None
        ]
        
        for path in possible_paths:
            if path and path.exists():
                return str(path)
        
        return None
    
    def _get_pip_command(self) -> List[str]:
        """적절한 pip 명령어 반환"""
        if self.venv_path:
            # 가상환경의 pip 사용
            if sys.platform == "win32":
                pip_path = Path(self.venv_path) / "Scripts" / "pip"
            else:
                pip_path = Path(self.venv_path) / "bin" / "pip"
            
            if pip_path.exists():
                return [str(pip_path)]
        
        # 시스템 pip 또는 현재 환경의 pip 사용
        return [sys.executable, "-m", "pip"]
    
    def _get_installed_packages(self) -> Dict[str, str]:
        """설치된 패키지 목록 조회 (캐시 포함)"""
        if self._installed_packages_cache is not None:
            return self._installed_packages_cache
            
        try:
            pip_cmd = self._get_pip_command()
            result = subprocess.run(
                pip_cmd + ["list", "--format=json"],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                packages = json.loads(result.stdout)
                self._installed_packages_cache = {
                    pkg['name'].lower(): pkg['version'] for pkg in packages
                }
            else:
                self._installed_packages_cache = {}
                
        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
            self._installed_packages_cache = {}
            
        return self._installed_packages_cache
    
    def is_package_installed(self, package_name: str) -> bool:
        """패키지 설치 여부 확인"""
        installed = self._get_installed_packages()
        return package_name.lower() in installed
    
    def clear_cache(self):
        """설치된 패키지 캐시 무효화"""
        self._installed_packages_cache = None
    
    def extract_imports_from_code(self, code: str) -> List[str]:
        """코드에서 import 구문 추출"""
        imports = []
        
        # import 패턴 매칭
        import_patterns = [
            r'^import\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'^from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import',
        ]
        
        for line in code.split('\n'):
            line = line.strip()
            if line.startswith('#'):  # 주석 제외
                continue
                
            for pattern in import_patterns:
                match = re.match(pattern, line)
                if match:
                    module_name = match.group(1)
                    # 표준 라이브러리가 아닌 경우만 추가
                    if not self._is_standard_library(module_name):
                        imports.append(module_name)
        
        return list(set(imports))
    
    def _is_standard_library(self, module_name: str) -> bool:
        """표준 라이브러리 여부 확인"""
        # 명확한 표준 라이브러리들
        standard_modules = {
            'os', 'sys', 'json', 're', 'math', 'random', 'datetime',
            'collections', 'itertools', 'functools', 'operator',
            'pathlib', 'typing', 'asyncio', 'threading', 'multiprocessing',
            'subprocess', 'io', 'csv', 'sqlite3', 'urllib', 'http',
            'logging', 'unittest', 'argparse', 'configparser'
        }
        
        if module_name in standard_modules:
            return True
        
        try:
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                return False
            
            # 표준 라이브러리는 보통 site-packages 외부에 있음
            if spec.origin:
                return 'site-packages' not in spec.origin
            return True
        except (ImportError, ModuleNotFoundError, ValueError):
            return False
    
    def install_package(self, package_name: str, version: Optional[str] = None) -> Tuple[bool, str]:
        """패키지 설치"""
        if not self._is_safe_package(package_name):
            message = f"패키지 '{package_name}'는 안전 목록에 없습니다."
            self._log_installation(package_name, False, message)
            return False, message
        
        if self.is_package_installed(package_name):
            message = f"패키지 '{package_name}'는 이미 설치되어 있습니다."
            return True, message
        
        # 사용자 동의 확인 (TDD 모드에서는 일반적으로 False)
        if self.ask_permission:
            response = input(f"패키지 '{package_name}' 설치를 진행하시겠습니까? (y/n): ")
            if response.lower() not in ['y', 'yes']:
                message = "사용자가 설치를 거부했습니다."
                self._log_installation(package_name, False, message)
                return False, message
        
        try:
            pip_cmd = self._get_pip_command()
            package_spec = f"{package_name}=={version}" if version else package_name
            
            result = subprocess.run(
                pip_cmd + ["install", package_spec],
                capture_output=True, text=True, timeout=300
            )
            
            if result.returncode == 0:
                # 캐시 무효화
                self.clear_cache()
                self._update_requirements_file(package_name, version)
                message = f"패키지 '{package_name}' 설치 완료"
                self._log_installation(package_name, True, message)
                return True, message
            else:
                message = f"설치 실패: {result.stderr}"
                self._log_installation(package_name, False, message)
                return False, message
                
        except subprocess.TimeoutExpired:
            message = "설치 시간 초과"
            self._log_installation(package_name, False, message)
            return False, message
        except Exception as e:
            message = f"설치 중 오류 발생: {str(e)}"
            self._log_installation(package_name, False, message)
            return False, message
    
    def _is_safe_package(self, package_name: str) -> bool:
        """안전한 패키지인지 확인"""
        return package_name.lower() in self.safe_packages
    
    def _log_installation(self, package_name: str, success: bool, message: str):
        """설치 기록 로깅"""
        self.installation_history.append({
            "package": package_name,
            "success": success,
            "message": message,
            "timestamp": str(Path.cwd())  # 간단한 타임스탬프 대신
        })
    
    def _update_requirements_file(self, package_name: str, version: Optional[str] = None):
        """requirements.txt 파일 업데이트"""
        try:
            # 기존 requirements 읽기
            existing_reqs = set()
            if self.requirements_file.exists():
                with open(self.requirements_file, 'r', encoding='utf-8') as f:
                    existing_reqs = {line.strip() for line in f if line.strip()}
            
            # 새 패키지 추가
            package_spec = f"{package_name}=={version}" if version else package_name
            existing_reqs.add(package_spec)
            
            # requirements.txt 쓰기
            with open(self.requirements_file, 'w', encoding='utf-8') as f:
                for req in sorted(existing_reqs):
                    f.write(f"{req}\n")
                    
        except Exception as e:
            # 조용히 실패 (TDD 프로세스 방해하지 않음)
            pass
    
    def handle_import_error(self, error_message: str) -> Tuple[bool, str]:
        """ImportError 또는 ModuleNotFoundError 처리"""
        # 오류 메시지에서 모듈명 추출
        module_match = re.search(r"No module named '([^']+)'", error_message)
        if not module_match:
            return False, "모듈명을 추출할 수 없습니다."
        
        module_name = module_match.group(1)
        
        if not self.auto_install:
            return False, f"자동 설치가 비활성화되어 있습니다. 수동으로 '{module_name}' 설치가 필요합니다."
        
        return self.install_package(module_name)
    
    def install_dependencies_from_code(self, code: str) -> Dict[str, Tuple[bool, str]]:
        """코드에서 추출한 의존성들 설치"""
        imports = self.extract_imports_from_code(code)
        results = {}
        
        for module_name in imports:
            if not self.is_package_installed(module_name):
                success, message = self.install_package(module_name)
                results[module_name] = (success, message)
        
        return results


class TDDDependencyManager:
    """TDD 시스템과 통합된 의존성 관리자"""
    
    def __init__(self, project_path: str, auto_install: bool = True):
        self.installer = AutoDependencyInstaller(
            project_path=project_path,
            auto_install=auto_install,
            ask_permission=False  # TDD 자동화에서는 자동 설치
        )
        self.error_resolution_count = 0
    
    def handle_test_failure(self, test_output: str) -> bool:
        """테스트 실패 출력을 분석하여 의존성 문제 해결"""
        dependency_errors = [
            "ModuleNotFoundError",
            "ImportError",
            "No module named"
        ]
        
        if any(error in test_output for error in dependency_errors):
            success, message = self.installer.handle_import_error(test_output)
            if success:
                self.error_resolution_count += 1
                return True
            
        return False
    
    def pre_install_dependencies(self, code: str) -> Dict[str, bool]:
        """코드 실행 전 미리 의존성 설치"""
        results = self.installer.install_dependencies_from_code(code)
        
        # 성공/실패만 반환 (간소화)
        return {
            module_name: success 
            for module_name, (success, _) in results.items()
        }
    
    def get_installation_history(self) -> List[Dict]:
        """설치 기록 반환"""
        return self.installer.installation_history.copy()
    
    def add_safe_package(self, package_name: str):
        """안전한 패키지 목록에 추가"""
        self.installer.safe_packages.add(package_name.lower())
    
    def get_stats(self) -> Dict:
        """통계 정보 반환"""
        history = self.installer.installation_history
        successful_installs = [h for h in history if h["success"]]
        
        return {
            "total_attempts": len(history),
            "successful_installs": len(successful_installs),
            "error_resolutions": self.error_resolution_count,
            "installed_packages": [h["package"] for h in successful_installs]
        }