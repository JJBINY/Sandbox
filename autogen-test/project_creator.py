# project_creator.py - 실행 가능한 프로젝트 생성 시스템
import asyncio
import os
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from dotenv import load_dotenv
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_ext.models.openai import OpenAIChatCompletionClient
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

class ProjectFileManager:
    """프로젝트 파일 관리 클래스"""
    
    def __init__(self, base_dir: str = "generated_projects"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        self.current_project_path = None
    
    def create_project_directory(self, project_name: str) -> Path:
        """프로젝트 디렉토리 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_dir = self.base_dir / f"{project_name}_{timestamp}"
        project_dir.mkdir(parents=True, exist_ok=True)
        self.current_project_path = project_dir
        return project_dir
    
    def write_file(self, relative_path: str, content: str) -> Path:
        """파일 작성"""
        if not self.current_project_path:
            raise ValueError("프로젝트 디렉토리가 설정되지 않았습니다.")
        
        file_path = self.current_project_path / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"📝 파일 생성: {relative_path}")
        return file_path
    
    def create_directory(self, relative_path: str) -> Path:
        """디렉토리 생성"""
        if not self.current_project_path:
            raise ValueError("프로젝트 디렉토리가 설정되지 않았습니다.")
        
        dir_path = self.current_project_path / relative_path
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"📁 디렉토리 생성: {relative_path}")
        return dir_path
    
    def install_dependencies(self) -> bool:
        """의존성 설치"""
        if not self.current_project_path:
            return False
        
        requirements_file = self.current_project_path / "requirements.txt"
        if not requirements_file.exists():
            print("⚠️ requirements.txt가 없습니다.")
            return False
        
        try:
            print("📦 의존성 설치 중...")
            result = subprocess.run(
                ["pip", "install", "-r", str(requirements_file)],
                cwd=self.current_project_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                print("✅ 의존성 설치 완료!")
                return True
            else:
                print(f"❌ 의존성 설치 실패: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ 의존성 설치 시간 초과")
            return False
        except Exception as e:
            print(f"❌ 의존성 설치 중 오류: {e}")
            return False
    
    def test_project(self) -> bool:
        """프로젝트 테스트 실행"""
        if not self.current_project_path:
            return False
        
        # main.py 또는 app.py 실행 테스트
        test_files = ["main.py", "app.py", "run.py"]
        
        for test_file in test_files:
            file_path = self.current_project_path / test_file
            if file_path.exists():
                try:
                    print(f"🧪 {test_file} 실행 테스트 중...")
                    result = subprocess.run(
                        ["python", "-c", f"import {test_file[:-3]}; print('Import successful')"],
                        cwd=self.current_project_path,
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode == 0:
                        print(f"✅ {test_file} 실행 테스트 성공!")
                        return True
                    else:
                        print(f"⚠️ {test_file} 실행 테스트 실패: {result.stderr}")
                        
                except Exception as e:
                    print(f"⚠️ {test_file} 테스트 중 오류: {e}")
        
        print("ℹ️ 실행 테스트를 건너뜁니다.")
        return True

# 파일 작성을 위한 도구 함수들
def write_project_file(file_manager: ProjectFileManager, relative_path: str, content: str) -> str:
    """프로젝트 파일 작성 도구"""
    try:
        file_path = file_manager.write_file(relative_path, content)
        return f"✅ 파일 '{relative_path}' 생성 완료"
    except Exception as e:
        return f"❌ 파일 '{relative_path}' 생성 실패: {e}"

def create_project_directory_tool(file_manager: ProjectFileManager, relative_path: str) -> str:
    """프로젝트 디렉토리 생성 도구"""
    try:
        dir_path = file_manager.create_directory(relative_path)
        return f"✅ 디렉토리 '{relative_path}' 생성 완료"
    except Exception as e:
        return f"❌ 디렉토리 '{relative_path}' 생성 실패: {e}"

class ProjectCreatorSystem:
    """프로젝트 생성 시스템"""
    
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
        """프로젝트 생성 전용 에이전트들 설정"""
        
        # 프로젝트 설계자
        self.architect = AssistantAgent(
            name="ProjectArchitect",
            model_client=self.create_model_client(),
            system_message="""당신은 프로젝트 아키텍트입니다.
            
            역할:
            1. 프로젝트 구조 설계
            2. 필요한 파일 목록 작성
            3. 의존성 분석
            4. 실행 방법 정의
            
            응답 형식:
            ## 프로젝트 구조
            ```
            project_name/
            ├── main.py
            ├── requirements.txt
            ├── README.md
            └── modules/
                └── __init__.py
            ```
            
            ## 파일 설명
            - main.py: 메인 실행 파일
            - requirements.txt: 의존성 목록
            
            ## 실행 방법
            ```bash
            pip install -r requirements.txt
            python main.py
            ```
            
            구체적이고 실행 가능한 프로젝트 구조를 제안하세요."""
        )
        
        # 코드 생성자
        self.code_generator = AssistantAgent(
            name="CodeGenerator", 
            model_client=self.create_model_client(),
            system_message="""당신은 코드 생성 전문가입니다.
            
            역할:
            1. 실행 가능한 Python 코드 작성
            2. 모든 필요한 파일 생성
            3. 에러 처리 및 로깅 포함
            4. 문서화 주석 추가
            
            파일별로 완전한 코드를 제공하세요:
            
            **파일명: main.py**
            ```python
            # 완전한 코드 내용
            ```
            
            **파일명: requirements.txt**
            ```
            # 의존성 목록
            ```
            
            각 파일은 즉시 실행 가능해야 합니다."""
        )
        
        # 품질 보증
        self.qa_tester = AssistantAgent(
            name="QATester",
            model_client=self.create_model_client(), 
            system_message="""당신은 품질 보증 전문가입니다.
            
            역할:
            1. 코드 품질 검토
            2. 보안 취약점 확인
            3. 성능 최적화 제안
            4. 테스트 케이스 작성
            5. 실행 가능성 검증
            
            다음을 확인하세요:
            ✅ 코드 문법 오류
            ✅ import 문 누락
            ✅ 파일 경로 오류
            ✅ 의존성 누락
            ✅ 실행 시나리오
            
            문제가 있다면 구체적인 수정 방안을 제시하세요."""
        )
    
    def create_team(self, max_turns: int = 8):
        """프로젝트 생성 팀 구성"""
        termination_condition = MaxMessageTermination(max_turns)
        return RoundRobinGroupChat(
            participants=[
                self.architect,
                self.code_generator,
                self.qa_tester
            ],
            termination_condition=termination_condition
        )
    
    async def create_project(self, project_request: str, project_name: str = None):
        """프로젝트 생성 메인 함수"""
        print("🏗️ 프로젝트 생성 시스템 시작!")
        print(f"📋 요청사항: {project_request}")
        print("-" * 60)
        
        try:
            # 프로젝트명 설정
            if not project_name:
                project_name = input("프로젝트명을 입력하세요 (기본값: my_project): ").strip() or "my_project"
            
            # 프로젝트 디렉토리 생성
            project_dir = self.file_manager.create_project_directory(project_name)
            print(f"📁 프로젝트 디렉토리 생성: {project_dir}")
            
            # 에이전트 협업으로 프로젝트 설계
            team = self.create_team()
            
            enhanced_request = f"""다음 요청에 따라 완전히 실행 가능한 Python 프로젝트를 설계하고 구현해주세요:

요청사항: {project_request}

프로젝트명: {project_name}

요구사항:
1. 즉시 실행 가능한 코드
2. 완전한 파일 구조
3. 의존성 관리 (requirements.txt)
4. 실행 방법 안내 (README.md)
5. 에러 처리 포함
6. 간단한 테스트 포함

각 에이전트는 자신의 역할에 맞게 기여해주세요."""
            
            response = await team.run(task=enhanced_request)
            
            # 협업 결과에서 프로젝트 파일 추출 및 생성
            await self.extract_and_create_files(response, project_name)
            
            # 프로젝트 설정 및 테스트
            await self.setup_and_test_project(project_dir)
            
            return project_dir
            
        except Exception as e:
            print(f"❌ 프로젝트 생성 중 오류: {e}")
            return None
        finally:
            await self.cleanup()
    
    async def extract_and_create_files(self, response, project_name: str):
        """협업 결과에서 파일 추출 및 생성"""
        print("\n🔄 파일 추출 및 생성 중...")
        
        # 기본 파일들 생성
        files_created = {}
        
        # 모든 메시지에서 코드 블록 찾기
        for message in response.messages:
            content = message.content
            
            # 파일명과 코드 블록 추출
            import re
            
            # **파일명: filename** 패턴 찾기
            file_patterns = re.findall(r'\*\*파일명:\s*([^*]+)\*\*\s*```[a-zA-Z]*\n(.*?)```', content, re.DOTALL)
            
            for filename, code_content in file_patterns:
                filename = filename.strip()
                code_content = code_content.strip()
                
                if filename and code_content:
                    self.file_manager.write_file(filename, code_content)
                    files_created[filename] = True
        
        # 기본 파일들이 없으면 생성
        if 'requirements.txt' not in files_created:
            self.create_default_requirements()
        
        if 'README.md' not in files_created:
            self.create_default_readme(project_name)
        
        if 'main.py' not in files_created and 'app.py' not in files_created:
            self.create_default_main()
        
        print(f"✅ 총 {len(files_created)} + 기본 파일들이 생성되었습니다.")
    
    def create_default_requirements(self):
        """기본 requirements.txt 생성"""
        content = """# 기본 의존성
# 필요에 따라 추가하세요
"""
        self.file_manager.write_file("requirements.txt", content)
    
    def create_default_readme(self, project_name: str):
        """기본 README.md 생성"""
        content = f"""# {project_name}

Autogen 다중 에이전트 시스템으로 생성된 프로젝트입니다.

## 설치

```bash
pip install -r requirements.txt
```

## 실행

```bash
python main.py
```

## 생성 정보

- 생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 생성 도구: Autogen + Gemini API
"""
        self.file_manager.write_file("README.md", content)
    
    def create_default_main(self):
        """기본 main.py 생성"""
        content = '''#!/usr/bin/env python3
"""
메인 실행 파일
"""

def main():
    print("프로젝트가 성공적으로 실행되었습니다!")
    print("이 파일을 수정하여 원하는 기능을 구현하세요.")

if __name__ == "__main__":
    main()
'''
        self.file_manager.write_file("main.py", content)
    
    async def setup_and_test_project(self, project_dir: Path):
        """프로젝트 설정 및 테스트"""
        print("\n🔧 프로젝트 설정 및 테스트...")
        
        # 의존성 설치 여부 묻기
        install_deps = input("\n📦 의존성을 설치하시겠습니까? (y/n): ").strip().lower()
        if install_deps in ['y', 'yes', '예']:
            self.file_manager.install_dependencies()
        
        # 프로젝트 테스트 실행
        test_project = input("🧪 프로젝트 테스트를 실행하시겠습니까? (y/n): ").strip().lower()
        if test_project in ['y', 'yes', '예']:
            self.file_manager.test_project()
        
        print(f"\n🎉 프로젝트 생성 완료!")
        print(f"📁 프로젝트 위치: {project_dir.absolute()}")
        print(f"📝 다음 명령으로 프로젝트 폴더로 이동하세요:")
        print(f"   cd {project_dir.absolute()}")
    
    async def cleanup(self):
        """리소스 정리"""
        try:
            agents = [self.architect, self.code_generator, self.qa_tester]
            for agent in agents:
                if hasattr(agent, 'model_client'):
                    await agent.model_client.close()
        except Exception as e:
            print(f"⚠️ 정리 중 오류: {e}")

# 프로젝트 생성 예제들
class ProjectExamples:
    """프로젝트 생성 예제들"""
    
    @staticmethod
    def web_app_example():
        return """Flask를 사용한 간단한 할 일 관리 웹 앱을 만들어주세요.
        
기능:
- 할 일 추가/삭제/완료
- 웹 인터페이스 (HTML/CSS)
- 데이터는 JSON 파일에 저장
- 기본 API 엔드포인트 제공"""
    
    @staticmethod
    def data_analysis_example():
        return """pandas와 matplotlib을 사용한 데이터 분석 도구를 만들어주세요.
        
기능:
- CSV 파일 읽기
- 기본 통계 분석
- 그래프 생성 (히스토그램, 산점도)
- 결과를 HTML 리포트로 출력"""
    
    @staticmethod
    def api_client_example():
        return """REST API 클라이언트 라이브러리를 만들어주세요.
        
기능:
- HTTP 요청 처리 (GET, POST, PUT, DELETE)
- JSON 응답 파싱
- 에러 처리 및 재시도 로직
- 설정 파일 지원
- 로깅 기능"""
    
    @staticmethod
    def cli_tool_example():
        return """명령줄 도구를 만들어주세요.
        
기능:
- argparse를 사용한 명령줄 인자 처리
- 여러 하위 명령어 지원
- 파일 처리 기능
- 진행률 표시
- 설정 파일 지원"""

async def main():
    """메인 실행 함수"""
    print("🏗️ Autogen 프로젝트 생성 시스템")
    print("=" * 50)
    
    try:
        creator = ProjectCreatorSystem()
        
        print("어떤 방식으로 프로젝트를 생성하시겠습니까?")
        print("1. 직접 입력")
        print("2. 웹 앱 예제 (Flask TODO 앱)")
        print("3. 데이터 분석 도구 예제")
        print("4. API 클라이언트 예제")
        print("5. CLI 도구 예제")
        
        choice = input("\n선택 (1-5): ").strip()
        
        if choice == "1":
            project_request = input("만들고 싶은 프로젝트를 설명해주세요: ").strip()
        elif choice == "2":
            project_request = ProjectExamples.web_app_example()
            print(f"선택된 예제:\n{project_request}")
        elif choice == "3":
            project_request = ProjectExamples.data_analysis_example()
            print(f"선택된 예제:\n{project_request}")
        elif choice == "4":
            project_request = ProjectExamples.api_client_example()
            print(f"선택된 예제:\n{project_request}")
        elif choice == "5":
            project_request = ProjectExamples.cli_tool_example()
            print(f"선택된 예제:\n{project_request}")
        else:
            print("❌ 잘못된 선택입니다.")
            return
        
        if not project_request:
            print("❌ 프로젝트 요청이 입력되지 않았습니다.")
            return
        
        # 프로젝트 생성 실행
        project_dir = await creator.create_project(project_request)
        
        if project_dir:
            print(f"\n🎊 프로젝트 생성 성공!")
            print(f"📍 위치: {project_dir.absolute()}")
        else:
            print("\n❌ 프로젝트 생성 실패")
        
    except Exception as e:
        print(f"❌ 시스템 오류: {e}")

if __name__ == "__main__":
    asyncio.run(main())