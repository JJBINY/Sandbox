# enhanced_project_creator.py - 완전한 프로젝트 생성 시스템
import asyncio
import os
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from autogen_agentchat.agents import AssistantAgent, CodeExecutorAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor
from autogen_core.models import ModelInfo

# .env 파일 로드
load_dotenv()

class Config:
    """환경 설정 관리"""
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
    GEMINI_BASE_URL = os.getenv('GEMINI_BASE_URL', 'https://generativelanguage.googleapis.com/v1beta/openai/')
    
    @classmethod
    def validate_config(cls):
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")
        print("✅ 설정이 유효합니다.")
        return True

class DependencyManager:
    """의존성 자동 관리 시스템"""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.safe_packages = {
            'flask', 'fastapi', 'django', 'requests', 'pandas', 'numpy',
            'matplotlib', 'seaborn', 'click', 'rich', 'tqdm', 'pytest',
            'pytest-cov', 'black', 'flake8', 'mypy', 'pydantic',
            'sqlalchemy', 'pillow', 'opencv-python', 'scikit-learn'
        }
        self.installed_packages = []
    
    def extract_imports_from_code(self, code: str) -> List[str]:
        """코드에서 import 구문 추출"""
        import re
        imports = []
        
        # import 패턴 매칭
        patterns = [
            r'^import\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'^from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import',
        ]
        
        for line in code.split('\n'):
            line = line.strip()
            if line.startswith('#'):
                continue
                
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    module_name = match.group(1)
                    if not self._is_standard_library(module_name):
                        imports.append(module_name)
        
        return list(set(imports))
    
    def _is_standard_library(self, module_name: str) -> bool:
        """표준 라이브러리 여부 확인"""
        standard_modules = {
            'os', 'sys', 'json', 're', 'math', 'random', 'datetime',
            'collections', 'itertools', 'functools', 'operator',
            'pathlib', 'typing', 'asyncio', 'threading', 'multiprocessing',
            'subprocess', 'io', 'csv', 'sqlite3', 'urllib', 'http',
            'logging', 'unittest', 'argparse', 'configparser', 'tempfile'
        }
        return module_name in standard_modules
    
    def install_dependencies(self, imports: List[str]) -> Dict[str, bool]:
        """의존성 자동 설치"""
        results = {}
        
        for module in imports:
            if module in self.safe_packages:
                try:
                    print(f"📦 {module} 설치 중...")
                    result = subprocess.run(
                        [sys.executable, '-m', 'pip', 'install', module],
                        capture_output=True, text=True, timeout=60
                    )
                    
                    if result.returncode == 0:
                        print(f"✅ {module} 설치 완료")
                        self.installed_packages.append(module)
                        results[module] = True
                    else:
                        print(f"❌ {module} 설치 실패")
                        results[module] = False
                        
                except subprocess.TimeoutExpired:
                    print(f"⏰ {module} 설치 시간 초과")
                    results[module] = False
                except Exception as e:
                    print(f"❌ {module} 설치 중 오류: {e}")
                    results[module] = False
            else:
                print(f"⚠️ {module}는 안전 목록에 없어 설치하지 않습니다")
                results[module] = False
        
        return results
    
    def update_requirements_file(self):
        """requirements.txt 업데이트"""
        req_file = self.project_path / "requirements.txt"
        
        # 기존 requirements 읽기
        existing_reqs = set()
        if req_file.exists():
            with open(req_file, 'r') as f:
                existing_reqs = {line.strip() for line in f if line.strip() and not line.startswith('#')}
        
        # 설치된 패키지 추가
        for package in self.installed_packages:
            existing_reqs.add(package)
        
        # requirements.txt 업데이트
        with open(req_file, 'w') as f:
            f.write("# 자동 생성된 의존성 목록\n")
            for req in sorted(existing_reqs):
                f.write(f"{req}\n")
        
        print(f"📝 requirements.txt 업데이트 완료 ({len(existing_reqs)}개 패키지)")

class ProjectFileManager:
    """프로젝트 파일 관리 클래스 (개선된 버전)"""
    
    def __init__(self, base_dir: str = "generated_projects"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        self.current_project_path = None
        self.dependency_manager = None
    
    def create_project_directory(self, project_name: str) -> Path:
        """프로젝트 디렉토리 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_dir = self.base_dir / f"{project_name}_{timestamp}"
        project_dir.mkdir(parents=True, exist_ok=True)
        self.current_project_path = project_dir
        
        # 의존성 관리자 초기화
        self.dependency_manager = DependencyManager(project_dir)
        
        return project_dir
    
    def write_file(self, relative_path: str, content: str) -> Path:
        """파일 작성 (의존성 자동 분석 포함)"""
        if not self.current_project_path:
            raise ValueError("프로젝트 디렉토리가 설정되지 않았습니다.")
        
        file_path = self.current_project_path / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"📝 파일 생성: {relative_path}")
        
        # Python 파일인 경우 의존성 분석
        if relative_path.endswith('.py') and self.dependency_manager:
            imports = self.dependency_manager.extract_imports_from_code(content)
            if imports:
                print(f"🔍 {relative_path}에서 발견된 의존성: {', '.join(imports)}")
                self.dependency_manager.install_dependencies(imports)
        
        return file_path
    
    def create_directory(self, relative_path: str) -> Path:
        """디렉토리 생성"""
        if not self.current_project_path:
            raise ValueError("프로젝트 디렉토리가 설정되지 않았습니다.")
        
        dir_path = self.current_project_path / relative_path
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"📁 디렉토리 생성: {relative_path}")
        return dir_path
    
    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """포괄적인 테스트 실행"""
        if not self.current_project_path:
            return {"error": "프로젝트 디렉토리가 설정되지 않았습니다."}
        
        results = {}
        
        try:
            # 1. 문법 검사
            print("🔍 Python 파일 문법 검사 중...")
            syntax_results = self._check_syntax()
            results['syntax_check'] = syntax_results
            
            # 2. 의존성 업데이트
            if self.dependency_manager:
                self.dependency_manager.update_requirements_file()
            
            # 3. pytest 실행 (테스트 파일이 있는 경우)
            test_dir = self.current_project_path / "tests"
            if test_dir.exists():
                print("🧪 pytest 실행 중...")
                test_results = self._run_pytest()
                results['pytest'] = test_results
            
            # 4. 메인 파일 실행 테스트
            print("🚀 메인 파일 실행 테스트 중...")
            execution_results = self._test_main_execution()
            results['execution_test'] = execution_results
            
            return results
            
        except Exception as e:
            return {"error": f"테스트 실행 중 오류: {e}"}
    
    def _check_syntax(self) -> Dict[str, Any]:
        """Python 파일 문법 검사"""
        results = {"passed": [], "failed": []}
        
        for py_file in self.current_project_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    code = f.read()
                
                compile(code, str(py_file), 'exec')
                results["passed"].append(str(py_file.relative_to(self.current_project_path)))
                
            except SyntaxError as e:
                results["failed"].append({
                    "file": str(py_file.relative_to(self.current_project_path)),
                    "error": f"Line {e.lineno}: {e.msg}"
                })
        
        return results
    
    def _run_pytest(self) -> Dict[str, Any]:
        """pytest 실행"""
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pytest', 'tests/', '-v', '--tb=short'],
                cwd=self.current_project_path,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "passed": result.returncode == 0
            }
            
        except subprocess.TimeoutExpired:
            return {"error": "pytest 실행 시간 초과"}
        except Exception as e:
            return {"error": f"pytest 실행 실패: {e}"}
    
    def _test_main_execution(self) -> Dict[str, Any]:
        """메인 파일 실행 테스트"""
        main_files = ['main.py', 'app.py', 'run.py']
        
        for main_file in main_files:
            file_path = self.current_project_path / main_file
            if file_path.exists():
                try:
                    # --help 옵션으로 실행 테스트
                    result = subprocess.run(
                        [sys.executable, str(file_path), '--help'],
                        cwd=self.current_project_path,
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    return {
                        "file": main_file,
                        "returncode": result.returncode,
                        "stdout": result.stdout[:500],  # 처음 500자만
                        "stderr": result.stderr[:500],
                        "passed": result.returncode in [0, 2]  # 0: 성공, 2: 도움말 표시
                    }
                    
                except subprocess.TimeoutExpired:
                    return {"file": main_file, "error": "실행 시간 초과"}
                except Exception as e:
                    return {"file": main_file, "error": f"실행 실패: {e}"}
        
        return {"error": "실행 가능한 메인 파일을 찾을 수 없습니다"}

class EnhancedProjectCreatorSystem:
    """향상된 프로젝트 생성 시스템 (모든 Agent 통합)"""
    
    def __init__(self):
        Config.validate_config()
        self.file_manager = ProjectFileManager()
        self.setup_agents()
    
    def create_model_client(self):
        """Gemini 모델 클라이언트 생성"""
        return OpenAIChatCompletionClient(
            model=Config.GEMINI_MODEL,
            api_key=Config.GEMINI_API_KEY,
            base_url=Config.GEMINI_BASE_URL,
            model_info=ModelInfo(
                vision=True,
                function_calling=True,
                json_output=True,
                family="gemini",
                structured_output=True
            )
        )
    
    def setup_agents(self):
        """모든 Agent 설정 (6개 Agent)"""
        
        # 1. 프로젝트 설계자
        self.architect = AssistantAgent(
            name="ProjectArchitect",
            model_client=self.create_model_client(),
            system_message=self._get_architect_prompt()
        )
        
        # 2. 코드 생성자
        self.code_generator = AssistantAgent(
            name="CodeGenerator", 
            model_client=self.create_model_client(),
            system_message=self._get_code_generator_prompt()
        )
        
        # 3. 테스트 코드 생성자 (NEW!)
        self.test_generator = AssistantAgent(
            name="TestGenerator",
            model_client=self.create_model_client(),
            system_message=self._get_test_generator_prompt()
        )
        
        # 4. 품질 보증 전문가 (개선됨)
        self.qa_specialist = AssistantAgent(
            name="QASpecialist",
            model_client=self.create_model_client(), 
            system_message=self._get_qa_specialist_prompt()
        )
        
        # 5. 테스트 실행자 (NEW!)
        self.test_executor = AssistantAgent(
            name="TestExecutor",
            model_client=self.create_model_client(),
            system_message=self._get_test_executor_prompt()
        )
        
        # 6. 실행 검증자 (개선됨)
        try:
            self.code_executor = LocalCommandLineCodeExecutor(
                timeout=30,
                work_dir="temp_execution"
            )
            
            self.execution_tester = CodeExecutorAgent(
                name="ExecutionTester",
                code_executor=self.code_executor,
                model_client=self.create_model_client(),
                system_message=self._get_execution_tester_prompt()
            )
            
            print("✅ 모든 Agent (6개) 초기화 완료")
            
        except Exception as e:
            print(f"⚠️ ExecutionTester 초기화 실패: {e}")
            self.execution_tester = None
    
    def _get_architect_prompt(self) -> str:
        """ProjectArchitect 프롬프트"""
        return """당신은 **프로젝트 아키텍트**입니다.

🎯 **주요 역할:**
1. 프로젝트 전체 구조 설계
2. 필요한 파일/디렉토리 목록 작성  
3. 의존성 분석 및 기술 스택 선정
4. 프로젝트 실행 방법 정의
5. 확장성과 유지보수성 고려

📋 **응답 형식:**

## 🏗️ 프로젝트 구조
```
project_name/
├── main.py                 # 메인 실행 파일
├── requirements.txt        # 의존성 목록
├── README.md              # 프로젝트 문서
├── src/                   # 소스 코드
│   ├── __init__.py
│   ├── core/             # 핵심 로직
│   └── utils/            # 유틸리티
├── tests/                # 테스트 코드
│   ├── __init__.py
│   ├── unit/            # 단위 테스트
│   └── conftest.py      # pytest 설정
└── .env.example         # 환경 변수 예제
```

## 📁 **핵심 파일 설명**
- **main.py**: 애플리케이션 진입점
- **src/core/**: 비즈니스 로직 구현
- **tests/**: 포괄적인 테스트 코드

## 🔧 **기술 스택 선정**  
## 📦 **의존성 분석**
## 🚀 **실행 방법**

구체적이고 실용적인 프로젝트 구조를 제안하세요!"""
    
    def _get_code_generator_prompt(self) -> str:
        """CodeGenerator 프롬프트"""
        return """당신은 **코드 생성 전문가**입니다.

⚠️ **중요: 반드시 완전하고 실행 가능한 Python 코드를 생성해야 합니다!**

📝 **코딩 원칙:**
- **완전성**: 모든 함수와 클래스는 완전히 구현
- **실행성**: 즉시 실행 가능한 코드만 생성
- **견고성**: 예외 처리 및 검증 로직 포함

⚠️ **응답 형식:**

FILE:main.py
```python
#!/usr/bin/env python3
import os
import sys
import logging

class MainApplication:
    def __init__(self, config=None):
        self.config = config or {}
        self.logger = self._setup_logging()
    
    def _setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)
    
    def run(self):
        # 실제 구현
        return 0

def main():
    app = MainApplication()
    return app.run()

if __name__ == "__main__":
    sys.exit(main())
```

FILE:requirements.txt
```
# 실제 필요한 패키지들만
requests>=2.25.0
```

**각 파일마다 FILE:파일명으로 시작하고 완전한 코드 작성!**"""
    
    def _get_test_generator_prompt(self) -> str:
        """TestGenerator 프롬프트"""  
        return """당신은 **테스트 코드 생성 전문가**입니다.

🧪 **주요 역할:**
1. 포괄적인 단위 테스트 작성
2. 통합 테스트 시나리오 설계
3. pytest 픽스처 및 모킹 적용

📝 **응답 형식:**

FILE:tests/conftest.py
```python
import pytest
from src.main import MainApplication

@pytest.fixture
def app():
    return MainApplication()

@pytest.fixture  
def sample_data():
    return {"test": "data"}
```

FILE:tests/test_main.py
```python
import pytest
from src.main import MainApplication

class TestMainApplication:
    def test_init(self, app):
        assert app is not None
        
    def test_run(self, app):
        result = app.run()
        assert result == 0
```

**실제 작동하는 완전한 테스트 코드를 생성하세요!**"""
    
    def _get_qa_specialist_prompt(self) -> str:
        """QASpecialist 프롬프트"""
        return """당신은 **품질 보증 전문가**입니다.

🔍 **검토 항목:**
- 코드 품질 (가독성, 복잡도, 중복)
- 보안 취약점 (하드코딩된 비밀번호, 입력 검증)  
- 성능 이슈 (알고리즘, 메모리)
- 아키텍처 (모듈화, 의존성)

**검토 결과 형식:**

## 🔍 코드 품질 검토 보고서

### ✅ 우수한 점
- [구체적인 우수 사항들]

### ⚠️ 개선 필요 사항

#### 🚨 긴급 (Critical)
FILE:filename.py
```python
# 개선된 코드 제공
```

### 📊 품질 메트릭
- 보안 점수: [평가]
- 성능 지표: [분석]

실제 문제 발견 시 수정된 코드를 제공하세요!"""
    
    def _get_test_executor_prompt(self) -> str:
        """TestExecutor 프롬프트"""
        return """당신은 **테스트 실행 및 검증 전문가**입니다.

🧪 **주요 역할:**
1. pytest 실행 및 결과 분석
2. 코드 커버리지 측정
3. 성능 벤치마크 실행

📊 **실행 전략:**
```bash
# 기본 테스트
pytest tests/ -v

# 커버리지
pytest tests/ --cov=src --cov-report=term-missing

# 성능 테스트
pytest tests/ -m "performance" --durations=10
```

**테스트 결과 분석:**

```python
def analyze_test_results():
    # 테스트 결과 종합 분석
    print("📊 테스트 결과 분석")
    # 통과율, 커버리지, 성능 분석
    return results
```

실제 테스트를 실행하고 상세한 분석을 제공하세요!"""
    
    def _get_execution_tester_prompt(self) -> str:
        """ExecutionTester 프롬프트"""
        return """당신은 **코드 실행 테스트 전문가**입니다.

🧪 **테스트 절차:**
1. 환경 검증 (Python 버전, 파일 존재)
2. 의존성 검증 (requirements.txt)
3. 문법 검사 (Python 파일들)
4. 실행 테스트 (main.py 등)

```python
def verify_environment():
    print("🔍 환경 검증 시작...")
    # Python 버전, 파일 존재 확인
    
def check_dependencies():
    print("📦 의존성 검증...")
    # requirements.txt 검증
    
def execute_main_files():
    print("🚀 실행 테스트...")
    # 메인 파일 실행 테스트
```

실제 코드를 실행하여 문제점을 발견하고 해결책을 제시하세요!"""
    
    def create_team(self, workflow_type: str = "full"):
        """워크플로우 타입에 따른 팀 구성"""
        
        if workflow_type == "full":
            # 전체 워크플로우 (6개 Agent 모두 사용)
            participants = [
                self.architect,
                self.code_generator,
                self.test_generator,  # NEW!
                self.qa_specialist,
                self.test_executor,   # NEW!
            ]
            if self.execution_tester:
                participants.append(self.execution_tester)
                
        elif workflow_type == "code_only":
            # 코드 생성만
            participants = [
                self.architect,
                self.code_generator
            ]
            if self.execution_tester:
                participants.append(self.execution_tester)
                
        elif workflow_type == "test_focused":
            # 테스트 중심
            participants = [
                self.code_generator,
                self.test_generator,
                self.test_executor,
                self.qa_specialist
            ]
            
        else:
            # 기본 워크플로우
            participants = [
                self.architect,
                self.code_generator,
                self.qa_specialist
            ]
        
        max_turns = len(participants) * 2 + 2
        return RoundRobinGroupChat(
            participants=participants,
            termination_condition=MaxMessageTermination(max_turns)
        )
    
    async def create_project(self, project_request: str, project_name: str = None, workflow_type: str = "full"):
        """프로젝트 생성 메인 함수 (6 Agent 워크플로우)"""
        print("🏗️ 향상된 프로젝트 생성 시스템 시작!")
        print(f"📋 요청사항: {project_request}")
        print(f"🔄 워크플로우: {workflow_type}")
        print("-" * 60)
        
        try:
            # 프로젝트명 설정
            if not project_name:
                project_name = input("프로젝트명을 입력하세요 (기본값: my_project): ").strip() or "my_project"
            
            # 프로젝트 디렉토리 생성
            project_dir = self.file_manager.create_project_directory(project_name)
            print(f"📁 프로젝트 디렉토리: {project_dir}")
            
            # Agent 팀 구성
            team = self.create_team(workflow_type)
            
            enhanced_request = f"""다음 요청에 따라 완전히 실행 가능한 Python 프로젝트를 설계하고 구현해주세요:

📋 **요청사항**: {project_request}
📁 **프로젝트명**: {project_name}  
🔄 **워크플로우**: {workflow_type}

🎯 **필수 요구사항:**
1. 즉시 실행 가능한 완전한 Python 코드 (주석만 말고!)
2. 포괄적인 테스트 코드 (단위 + 통합 테스트)
3. 완전한 파일 구조 (폴더 포함)
4. 실제 작동하는 의존성 (requirements.txt)
5. 상세한 실행 방법 (README.md)
6. 에러 처리 및 로깅 포함
7. 품질 검토 및 최적화

⚠️ **Agent별 역할:**
- **ProjectArchitect**: 프로젝트 구조 설계
- **CodeGenerator**: 완전한 실행 코드 생성  
- **TestGenerator**: 포괄적 테스트 코드 작성
- **QASpecialist**: 코드 품질 검토 및 개선
- **TestExecutor**: 테스트 실행 및 결과 분석
- **ExecutionTester**: 실제 코드 실행 검증

🔥 **파일 형식 예시:**
FILE:main.py
```python
# 실제 작동하는 완전한 코드
```

각 Agent는 자신의 역할에 맞게 완전한 결과물을 제공해주세요!"""
            
            # Agent 협업 실행
            print("🤖 Agent 협업 시작...")
            response = await team.run(task=enhanced_request)
            
            # 협업 결과에서 파일 추출 및 생성
            print("\n🔄 파일 추출 및 생성...")
            files_created = await self.extract_and_create_files(response, project_name)
            
            # 포괄적인 테스트 실행
            print("\n🧪 포괄적인 테스트 실행...")
            test_results = self.file_manager.run_comprehensive_tests()
            
            # 최종 결과 출력
            await self.show_final_results(project_dir, files_created, test_results)
            
            return project_dir
            
        except Exception as e:
            print(f"❌ 프로젝트 생성 중 오류: {e}")
            return None
        finally:
            await self.cleanup()
    
    async def extract_and_create_files(self, response, project_name: str):
        """협업 결과에서 파일 추출 및 생성 (개선된 버전)"""
        print("🔍 Agent 응답에서 파일 추출 중...")
        
        files_created = {}
        
        # 모든 메시지에서 코드 블록 찾기
        for message in response.messages:
            content = message.content
            print(f"\n🤖 {message.source}의 응답 분석 중...")
            
            import re
            
            # FILE: 패턴으로 파일 추출
            pattern_matches = re.findall(r'FILE:([^\n]+)\s*```[a-zA-Z]*\s*\n(.*?)```', content, re.DOTALL)
            for filename, code_content in pattern_matches:
                filename = filename.strip()
                code_content = code_content.strip()
                if filename and code_content and len(code_content) > 10:
                    try:
                        self.file_manager.write_file(filename, code_content)
                        files_created[filename] = True
                        print(f"✅ {filename} 생성 완료 ({len(code_content)} bytes)")
                    except Exception as e:
                        print(f"❌ {filename} 생성 실패: {e}")
        
        # 기본 파일들 생성 (없는 경우)
        if not files_created:
            print("⚠️ 추출된 파일이 없습니다. 기본 파일들을 생성합니다.")
            self._create_default_files(project_name)
        
        print(f"\n✅ 총 {len(files_created)}개 파일 생성 완료")
        return files_created
    
    def _create_default_files(self, project_name: str):
        """기본 파일들 생성"""
        
        # main.py
        main_content = f'''#!/usr/bin/env python3
"""
{project_name} - 메인 실행 파일
"""
import sys
import logging

def setup_logging():
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger(__name__)

def main():
    logger = setup_logging()
    logger.info(f"{project_name} 시작!")
    
    print(f"🎉 {project_name} 프로젝트가 실행되었습니다!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''
        self.file_manager.write_file("main.py", main_content)
        
        # requirements.txt
        req_content = """# 기본 의존성
requests>=2.25.0
pytest>=7.0.0
pytest-cov>=4.0.0
"""
        self.file_manager.write_file("requirements.txt", req_content)
        
        # README.md
        readme_content = f"""# {project_name}

프로젝트 설명을 여기에 작성하세요.

## 설치 및 실행

```bash
pip install -r requirements.txt
python main.py
```

## 테스트

```bash
pytest tests/
```
"""
        self.file_manager.write_file("README.md", readme_content)
        
        # 기본 테스트
        self.file_manager.create_directory("tests")
        test_content = '''import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_basic():
    """기본 테스트"""
    assert True

def test_import():
    """메인 모듈 import 테스트"""
    try:
        import main
        assert True
    except ImportError:
        assert False, "main 모듈을 import할 수 없습니다"
'''
        self.file_manager.write_file("tests/test_main.py", test_content)
        self.file_manager.write_file("tests/__init__.py", "")
    
    async def show_final_results(self, project_dir: Path, files_created: Dict, test_results: Dict):
        """최종 결과 출력 (개선된 버전)"""
        print("\n" + "=" * 80)
        print("🎉 향상된 프로젝트 생성 완료!")
        print("=" * 80)
        
        print(f"📁 프로젝트 위치: {project_dir.absolute()}")
        print(f"📄 생성된 파일 수: {len(files_created)}")
        
        if self.file_manager.dependency_manager:
            installed = self.file_manager.dependency_manager.installed_packages
            if installed:
                print(f"📦 자동 설치된 패키지: {', '.join(installed)}")
        
        # 테스트 결과 요약
        print("\n📊 테스트 결과 요약:")
        if "syntax_check" in test_results:
            syntax = test_results["syntax_check"]
            passed = len(syntax.get("passed", []))
            failed = len(syntax.get("failed", []))
            print(f"  🔍 문법 검사: {passed}개 통과, {failed}개 실패")
        
        if "pytest" in test_results:
            pytest_result = test_results["pytest"]
            status = "통과" if pytest_result.get("passed") else "실패"
            print(f"  🧪 pytest: {status}")
        
        if "execution_test" in test_results:
            exec_result = test_results["execution_test"]
            if "file" in exec_result:
                status = "성공" if exec_result.get("passed") else "실패"
                print(f"  🚀 실행 테스트: {exec_result['file']} - {status}")
        
        # 다음 단계 안내
        print(f"\n🚀 다음 단계:")
        print(f"1. cd {project_dir.absolute()}")
        print(f"2. pip install -r requirements.txt")
        print(f"3. python main.py")
        print(f"4. pytest tests/")
    
    async def cleanup(self):
        """리소스 정리"""
        try:
            agents = [self.architect, self.code_generator, self.test_generator, 
                     self.qa_specialist, self.test_executor]
            if self.execution_tester:
                agents.append(self.execution_tester)
                
            for agent in agents:
                if hasattr(agent, 'model_client'):
                    await agent.model_client.close()
            
            # 코드 실행 환경 정리
            if hasattr(self, 'code_executor'):
                try:
                    await self.code_executor.stop()
                except:
                    pass
                    
        except Exception as e:
            print(f"⚠️ 정리 중 오류: {e}")

# 향상된 프로젝트 예제들
class EnhancedProjectExamples:
    """더 구체적이고 테스트가 포함된 프로젝트 예제들"""
    
    @staticmethod
    def fastapi_rest_api():
        return """FastAPI를 사용한 완전한 RESTful API 서버를 만들어주세요.

🎯 **핵심 기능:**
- User CRUD API (GET, POST, PUT, DELETE /users)
- JWT 인증 시스템 (/auth/login, /auth/register)
- Pydantic 모델을 활용한 데이터 검증
- SQLite 데이터베이스 연동 (SQLAlchemy)
- API 문서 자동 생성 (FastAPI의 자동 Swagger)
- 로깅 및 에러 처리

🧪 **테스트 요구사항:**
- 모든 API 엔드포인트 단위 테스트
- 데이터베이스 연동 통합 테스트
- JWT 인증 테스트
- 입력 검증 테스트 (유효/무효 데이터)

🔧 **기술 스택:**
- FastAPI (웹 프레임워크)
- SQLAlchemy (ORM)
- Pydantic (데이터 검증)
- python-jose (JWT)
- pytest + httpx (테스트)

📁 **파일 구조:**
- main.py (FastAPI 앱)
- models.py (Pydantic/SQLAlchemy 모델)
- auth.py (JWT 인증)
- database.py (DB 연결)
- tests/ (포괄적 테스트)

⚠️ **중요:** 즉시 실행 가능하고 모든 기능이 완전히 구현되어야 함!"""
    
    @staticmethod
    def data_pipeline():
        return """pandas와 matplotlib을 사용한 데이터 파이프라인을 만들어주세요.

🎯 **핵심 기능:**
- CSV/JSON 파일 자동 로드 및 파싱
- 데이터 정제 (결측치 처리, 이상치 탐지)
- 통계 분석 (기술통계, 상관관계)
- 자동 시각화 (히스토그램, 산점도, 히트맵)
- HTML/PDF 리포트 자동 생성
- 설정 파일 기반 파이프라인 실행

🧪 **테스트 요구사항:**
- 데이터 로드 함수 테스트
- 데이터 정제 로직 테스트
- 시각화 함수 테스트 (파일 생성 확인)
- 엣지 케이스 테스트 (빈 데이터, 잘못된 형식)

🔧 **기술 스택:**
- pandas (데이터 처리)
- matplotlib + seaborn (시각화)
- jinja2 (리포트 템플릿)
- click (CLI)
- pytest (테스트)

📊 **샘플 데이터:**
- sales_data.csv (매출 데이터)
- customer_data.json (고객 정보)
- config.yaml (파이프라인 설정)

⚠️ **중요:** 실제 데이터로 테스트 가능하고 리포트 생성까지 완전 동작!"""
    
    @staticmethod
    def cli_automation_tool():
        return """Click을 사용한 CLI 자동화 도구를 만들어주세요.

🎯 **핵심 기능:**
- 파일 일괄 처리 (압축, 변환, 백업)
- 시스템 모니터링 (CPU, 메모리, 디스크)
- 로그 분석 및 알림
- 스케줄링 기능 (cron 스타일)
- 설정 파일 관리 (YAML/JSON)
- 진행률 표시 및 컬러 출력

🧪 **테스트 요구사항:**
- 각 CLI 명령어 단위 테스트
- 파일 처리 통합 테스트
- 모킹을 활용한 시스템 호출 테스트
- CLI 인터페이스 테스트

🔧 **기술 스택:**
- click (CLI 프레임워크)
- rich (컬러 출력)
- pyyaml (설정 파일)
- schedule (스케줄링)
- psutil (시스템 정보)

💻 **CLI 명령어:**
```bash
tool file process --input dir1 --output dir2
tool monitor --cpu --memory
tool schedule --task backup --time "*/30 * * * *"
tool config --set key=value
```

⚠️ **중요:** 실제 시스템에서 작동하는 완전한 CLI 도구!"""
    
    @staticmethod
    def web_scraper_dashboard():
        return """Streamlit과 requests를 사용한 웹 스크래핑 대시보드를 만들어주세요.

🎯 **핵심 기능:**
- 다중 웹사이트 스크래핑 (뉴스, 가격 정보 등)
- 실시간 데이터 수집 및 업데이트
- 인터랙티브 대시보드 (차트, 표, 필터)
- 데이터 저장 및 히스토리 관리
- 알림 시스템 (임계값 초과 시)
- 스크래핑 스케줄러

🧪 **테스트 요구사항:**
- 웹 스크래핑 함수 테스트 (모킹 활용)
- 데이터 파싱 로직 테스트
- 대시보드 컴포넌트 테스트
- 예외 처리 테스트 (네트워크 오류 등)

🔧 **기술 스택:**
- streamlit (대시보드)
- requests + BeautifulSoup (스크래핑)
- pandas (데이터 처리)
- plotly (인터랙티브 차트)
- sqlite3 (데이터 저장)

📊 **대시보드 페이지:**
- 실시간 모니터링
- 히스토리 분석
- 설정 관리
- 알림 로그

⚠️ **중요:** 실제 웹사이트에서 데이터를 수집하고 시각화하는 완전한 시스템!"""

async def main():
    """메인 실행 함수 (6 Agent 시스템)"""
    print("🏗️ 향상된 Autogen 프로젝트 생성 시스템 (6 Agent)")
    print("=" * 60)
    
    try:
        creator = EnhancedProjectCreatorSystem()
        
        print("어떤 방식으로 프로젝트를 생성하시겠습니까?")
        print("1. 직접 입력")
        print("2. FastAPI REST API 서버")
        print("3. 데이터 파이프라인")
        print("4. CLI 자동화 도구")
        print("5. 웹 스크래핑 대시보드")
        
        choice = input("\n선택 (1-5): ").strip()
        
        if choice == "1":
            project_request = input("만들고 싶은 프로젝트를 상세히 설명해주세요: ").strip()
        elif choice == "2":
            project_request = EnhancedProjectExamples.fastapi_rest_api()
            print(f"선택된 예제: FastAPI REST API")
        elif choice == "3":
            project_request = EnhancedProjectExamples.data_pipeline()
            print(f"선택된 예제: 데이터 파이프라인")
        elif choice == "4":
            project_request = EnhancedProjectExamples.cli_automation_tool()
            print(f"선택된 예제: CLI 자동화 도구")
        elif choice == "5":
            project_request = EnhancedProjectExamples.web_scraper_dashboard()
            print(f"선택된 예제: 웹 스크래핑 대시보드")
        else:
            print("❌ 잘못된 선택입니다.")
            return
        
        if not project_request:
            print("❌ 프로젝트 요청이 입력되지 않았습니다.")
            return
        
        # 워크플로우 선택
        print("\n워크플로우를 선택하세요:")
        print("1. Full (모든 Agent) - 최고 품질")
        print("2. Code-only - 빠른 프로토타입")
        print("3. Test-focused - 테스트 중심")
        
        workflow_choice = input("선택 (1-3, 기본값=1): ").strip() or "1"
        workflow_map = {"1": "full", "2": "code_only", "3": "test_focused"}
        workflow_type = workflow_map.get(workflow_choice, "full")
        
        # 프로젝트 생성 실행
        project_dir = await creator.create_project(
            project_request, 
            workflow_type=workflow_type
        )
        
        if project_dir:
            print(f"\n🎊 프로젝트 생성 성공!")
            print(f"📍 위치: {project_dir.absolute()}")
            print(f"🔥 워크플로우: {workflow_type} ({len(creator.create_team(workflow_type).participants)}개 Agent)")
        else:
            print("\n❌ 프로젝트 생성 실패")
        
    except Exception as e:
        print(f"❌ 시스템 오류: {e}")

if __name__ == "__main__":
    import sys
    print(f"🐍 Python {sys.version}")
    print(f"📦 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    asyncio.run(main())