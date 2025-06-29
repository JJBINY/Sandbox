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
            
            응답 형식 (정확히 이 형식을 따르세요):
            
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
        
        # 코드 생성자 - 더 구체적인 지시사항
        self.code_generator = AssistantAgent(
            name="CodeGenerator", 
            model_client=self.create_model_client(),
            system_message="""당신은 코드 생성 전문가입니다.
            
            ⚠️ 중요: 반드시 완전하고 실행 가능한 Python 코드를 생성해야 합니다!
            
            역할:
            1. 실행 가능한 Python 코드 작성 (주석만 말고 실제 구현!)
            2. 모든 필요한 파일 생성
            3. 에러 처리 및 로깅 포함
            4. 완전한 기능 구현
            
            ⚠️ 응답 형식을 정확히 따르세요:
            
            FILE:main.py
            ```python
            # 실제 완전한 Python 코드를 여기에 작성
            import os
            import sys
            
            def main():
                print("Hello World")
                # 실제 기능 구현
                
            if __name__ == "__main__":
                main()
            ```
            
            FILE:requirements.txt
            ```
            flask==2.3.0
            requests==2.31.0
            ```
            
            FILE:README.md
            ```markdown
            # 프로젝트 제목
            설명...
            ```
            
            각 파일마다 FILE:파일명 으로 시작하고, 그 다음에 코드 블록을 작성하세요.
            주석이나 설명만 쓰지 말고 실제 작동하는 코드를 구현하세요!"""
        )
        
        # 품질 보증
        self.qa_tester = AssistantAgent(
            name="QATester",
            model_client=self.create_model_client(), 
            system_message="""당신은 품질 보증 전문가입니다.
            
            역할:
            1. 코드 품질 검토
            2. 누락된 구현 확인
            3. 보안 취약점 확인
            4. 성능 최적화 제안
            5. 실행 가능성 검증
            
            다음을 확인하고 부족한 부분이 있으면 구체적인 코드로 보완하세요:
            ✅ 코드 문법 오류
            ✅ import 문 누락
            ✅ 실제 기능 구현 여부
            ✅ 파일 경로 오류
            ✅ 의존성 누락
            ✅ 실행 시나리오
            
            만약 이전 에이전트가 주석만 생성했다면, 실제 구현 코드를 제공하세요:
            
            FILE:보완할파일명.py
            ```python
            # 실제 완전한 구현 코드
            ```
            
            실행 가능한 완전한 코드를 보장하세요!"""
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

📋 요청사항: {project_request}
📁 프로젝트명: {project_name}

🎯 필수 요구사항:
1. 즉시 실행 가능한 완전한 Python 코드 (주석만 말고!)
2. 모든 import, 함수, 클래스 완전 구현
3. 완전한 파일 구조 (폴더 포함)
4. 실제 작동하는 의존성 (requirements.txt)
5. 상세한 실행 방법 (README.md)
6. 에러 처리 및 로깅 포함
7. 기본 테스트 코드

⚠️ 중요 지시사항:
- 주석이나 설명만 쓰지 말고 실제 구현 코드를 작성하세요!
- 모든 함수와 클래스는 완전히 구현되어야 합니다!
- 파일 형식을 정확히 지켜주세요: FILE:filename.py

🔥 예시 응답 형식:
FILE:main.py
```python
import os
import sys

def actual_working_function():
    # 실제 작동하는 코드
    result = "Hello World"
    return result

if __name__ == "__main__":
    print(actual_working_function())
```

각 에이전트는 자신의 역할에 맞게 완전한 코드를 구현해주세요!"""
            
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
        """협업 결과에서 파일 추출 및 생성 (개선된 버전)"""
        print("\n🔄 파일 추출 및 생성 중...")
        
        files_created = {}
        
        # 모든 메시지에서 코드 블록 찾기
        for message in response.messages:
            content = message.content
            print(f"\n🔍 {message.source}의 메시지 분석 중...")
            
            # 여러 패턴으로 파일 추출 시도
            import re
            
            # 패턴 1: FILE:filename 형식
            pattern1_matches = re.findall(r'FILE:([^\n]+)\s*```[a-zA-Z]*\s*\n(.*?)```', content, re.DOTALL)
            for filename, code_content in pattern1_matches:
                filename = filename.strip()
                code_content = code_content.strip()
                if filename and code_content and len(code_content) > 10:  # 너무 짧은 내용 제외
                    self.file_manager.write_file(filename, code_content)
                    files_created[filename] = True
                    print(f"✅ FILE: 패턴으로 {filename} 생성 (길이: {len(code_content)})")
            
            # 패턴 2: **파일명: filename** 형식
            pattern2_matches = re.findall(r'\*\*파일명:\s*([^*\n]+)\*\*\s*```[a-zA-Z]*\s*\n(.*?)```', content, re.DOTALL)
            for filename, code_content in pattern2_matches:
                filename = filename.strip()
                code_content = code_content.strip()
                if filename and code_content and len(code_content) > 10:
                    if filename not in files_created:  # 중복 방지
                        self.file_manager.write_file(filename, code_content)
                        files_created[filename] = True
                        print(f"✅ **파일명: 패턴으로 {filename} 생성 (길이: {len(code_content)})")
            
            # 패턴 3: # filename 또는 ## filename 형식
            pattern3_matches = re.findall(r'#+\s*([^#\n]+\.py|[^#\n]+\.txt|[^#\n]+\.md|[^#\n]+\.html|[^#\n]+\.css|[^#\n]+\.js)\s*```[a-zA-Z]*\s*\n(.*?)```', content, re.DOTALL)
            for filename, code_content in pattern3_matches:
                filename = filename.strip()
                code_content = code_content.strip()
                if filename and code_content and len(code_content) > 10:
                    if filename not in files_created:
                        self.file_manager.write_file(filename, code_content)
                        files_created[filename] = True
                        print(f"✅ # 패턴으로 {filename} 생성 (길이: {len(code_content)})")
            
            # 패턴 4: 단순히 filename.extension 후 코드 블록
            pattern4_matches = re.findall(r'([a-zA-Z0-9_/]+\.[a-zA-Z]+)\s*:?\s*```[a-zA-Z]*\s*\n(.*?)```', content, re.DOTALL)
            for filename, code_content in pattern4_matches:
                filename = filename.strip()
                code_content = code_content.strip()
                if filename and code_content and len(code_content) > 10:
                    if filename not in files_created:
                        self.file_manager.write_file(filename, code_content)
                        files_created[filename] = True
                        print(f"✅ 단순 패턴으로 {filename} 생성 (길이: {len(code_content)})")
        
        # 디버깅: 추출된 파일 목록 출력
        if files_created:
            print(f"\n📋 생성된 파일 목록:")
            for filename in files_created.keys():
                file_path = self.file_manager.current_project_path / filename
                if file_path.exists():
                    size = file_path.stat().st_size
                    print(f"  - {filename} ({size} bytes)")
        else:
            print("⚠️ 추출된 파일이 없습니다. 수동으로 기본 파일들을 생성합니다.")
            
            # 원본 메시지 내용 출력 (디버깅용)
            print("\n🔍 원본 메시지 내용 (디버깅):")
            for i, message in enumerate(response.messages[:2]):  # 처음 2개 메시지만
                print(f"\n--- {message.source} 메시지 {i+1} (처음 500자) ---")
                print(message.content[:500])
                print("..." if len(message.content) > 500 else "")
        
        # 기본 파일들이 없으면 템플릿으로 생성
        if 'requirements.txt' not in files_created:
            self.create_enhanced_requirements()
        
        if 'README.md' not in files_created:
            self.create_enhanced_readme(project_name)
        
        if not any(f.endswith('.py') for f in files_created.keys()):
            self.create_enhanced_main(project_name)
        
        print(f"\n✅ 총 {len(files_created)}개 파일 + 기본 파일들이 생성되었습니다.")
        return files_created
    
    def create_enhanced_requirements(self):
        """향상된 requirements.txt 생성"""
        content = """# 기본 의존성 - 프로젝트에 따라 수정하세요
requests>=2.25.0
python-dotenv>=0.19.0

# 웹 개발 (필요시 주석 해제)
# flask>=2.0.0
# fastapi>=0.68.0
# uvicorn>=0.15.0

# 데이터 분석 (필요시 주석 해제)
# pandas>=1.3.0
# numpy>=1.21.0
# matplotlib>=3.4.0

# CLI 도구 (필요시 주석 해제)
# click>=8.0.0
# rich>=10.0.0

# 테스트 (필요시 주석 해제)
# pytest>=6.0.0
# pytest-cov>=2.12.0
"""
        self.file_manager.write_file("requirements.txt", content)
    
    def create_enhanced_readme(self, project_name: str):
        """향상된 README.md 생성"""
        content = f"""# {project_name}

Autogen 다중 에이전트 시스템으로 생성된 Python 프로젝트입니다.

## 🚀 빠른 시작

### 설치

```bash
# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는 Windows: venv\\Scripts\\activate

# 의존성 설치
pip install -r requirements.txt
```

### 실행

```bash
python main.py
```

## 📁 프로젝트 구조

```
{project_name}/
├── main.py              # 메인 실행 파일
├── requirements.txt     # 의존성 목록  
├── README.md           # 프로젝트 문서
├── config/             # 설정 파일들
├── modules/            # 추가 모듈들
└── tests/              # 테스트 파일들
```

## 🛠️ 개발

### 새로운 기능 추가
1. `modules/` 디렉토리에 새 모듈 생성
2. `main.py`에서 모듈 import
3. 테스트 파일 작성

### 테스트 실행
```bash
pytest tests/
```

## 📝 생성 정보

- **생성 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **생성 도구**: Autogen + Gemini API
- **Python 버전**: 3.8+

## 🤝 기여

이 프로젝트를 개선하고 싶으시다면:
1. Fork 후 수정
2. 테스트 추가
3. Pull Request 생성

## 📄 라이선스

MIT License - 자유롭게 사용하세요!
"""
        self.file_manager.write_file("README.md", content)
    
    def create_enhanced_main(self, project_name: str):
        """향상된 main.py 생성"""
        content = f'''#!/usr/bin/env python3
"""
{project_name} - 메인 실행 파일

Autogen 다중 에이전트 시스템으로 생성된 프로젝트입니다.
이 파일을 수정하여 원하는 기능을 구현하세요.
"""

import sys
import os
import argparse
from datetime import datetime

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def setup_logging():
    """로깅 설정"""
    import logging
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('app.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def load_config():
    """설정 로드"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        config = {{
            'debug': os.getenv('DEBUG', 'False').lower() == 'true',
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
        }}
        return config
    except ImportError:
        print("python-dotenv가 설치되지 않았습니다. 기본 설정을 사용합니다.")
        return {{'debug': False, 'log_level': 'INFO'}}

def example_function():
    """예제 함수 - 실제 기능으로 교체하세요"""
    logger = setup_logging()
    
    logger.info("프로젝트가 성공적으로 시작되었습니다!")
    
    # 여기에 실제 기능을 구현하세요
    print(f"🎉 {{project_name}} 프로젝트가 실행되었습니다!")
    print(f"📅 실행 시간: {{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}")
    print(f"🐍 Python 버전: {{sys.version}}")
    print(f"📁 작업 디렉토리: {{os.getcwd()}}")
    
    # 예제 작업
    example_data = [1, 2, 3, 4, 5]
    result = sum(example_data)
    print(f"📊 예제 계산 결과: {{example_data}} 의 합 = {{result}}")
    
    return result

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='{project_name} - 프로젝트 실행')
    parser.add_argument('--debug', action='store_true', help='디버그 모드로 실행')
    parser.add_argument('--config', type=str, help='설정 파일 경로')
    
    args = parser.parse_args()
    
    # 설정 로드
    config = load_config()
    
    if args.debug:
        config['debug'] = True
    
    # 디버그 정보 출력
    if config['debug']:
        print("🐛 디버그 모드로 실행 중...")
        print(f"설정: {{config}}")
    
    try:
        # 메인 로직 실행
        result = example_function()
        
        print(f"\\n✅ 프로젝트 실행 완료! 결과: {{result}}")
        return 0
        
    except KeyboardInterrupt:
        print("\\n⏹️ 사용자에 의해 중단되었습니다.")
        return 1
    except Exception as e:
        print(f"\\n❌ 오류가 발생했습니다: {{e}}")
        if config['debug']:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
'''
        self.file_manager.write_file("main.py", content)
        
        # 추가로 기본 모듈 구조도 생성
        self.create_basic_project_structure(project_name)
    
    def create_basic_project_structure(self, project_name: str):
        """기본 프로젝트 구조 생성"""
        
        # modules 디렉토리와 __init__.py
        self.file_manager.create_directory("modules")
        modules_init = '''"""
프로젝트 모듈들

여기에 재사용 가능한 모듈들을 작성하세요.
"""

__version__ = "0.1.0"
__author__ = "Autogen System"
'''
        self.file_manager.write_file("modules/__init__.py", modules_init)
        
        # config 디렉토리
        self.file_manager.create_directory("config")
        
        # .env 예제 파일
        env_example = f'''# {project_name} 환경 설정

# 디버그 모드
DEBUG=False

# 로그 레벨 (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# 데이터베이스 URL (예시)
# DATABASE_URL=sqlite:///app.db

# API 키들 (예시)
# API_KEY=your_api_key_here
# SECRET_KEY=your_secret_key_here

# 서버 설정 (웹 앱인 경우)
# HOST=0.0.0.0
# PORT=5000
'''
        self.file_manager.write_file(".env.example", env_example)
        
        # tests 디렉토리와 기본 테스트
        self.file_manager.create_directory("tests")
        test_main = f'''"""
{project_name} 테스트

기본 테스트 파일입니다.
"""

import unittest
import sys
import os

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestMain(unittest.TestCase):
    """메인 모듈 테스트"""
    
    def test_import(self):
        """모듈 import 테스트"""
        try:
            import main
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"main 모듈을 import할 수 없습니다: {{e}}")
    
    def test_example_function(self):
        """예제 함수 테스트"""
        try:
            import main
            result = main.example_function()
            self.assertIsNotNone(result)
            self.assertIsInstance(result, (int, float))
        except Exception as e:
            self.fail(f"example_function 실행 실패: {{e}}")

if __name__ == '__main__':
    unittest.main()
'''
        self.file_manager.write_file("tests/test_main.py", test_main)
        
        print("📁 기본 프로젝트 구조가 생성되었습니다.")
    
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
    """프로젝트 생성 예제들 (더 구체적)"""
    
    @staticmethod
    def web_app_example():
        return """Flask를 사용한 완전한 할 일 관리 웹 앱을 만들어주세요.

🎯 구체적인 기능:
- GET /: 메인 페이지 (HTML 템플릿)
- POST /add: 새 할 일 추가
- POST /complete/<id>: 할 일 완료 처리
- POST /delete/<id>: 할 일 삭제
- 데이터는 todos.json 파일에 저장
- Bootstrap CSS로 예쁜 인터페이스
- 실시간 할 일 카운터

🔧 기술 스택:
- Flask (웹 프레임워크)
- Jinja2 (템플릿)
- JSON (데이터 저장)
- Bootstrap (UI)

📁 필요한 파일:
- app.py (메인 Flask 앱)
- templates/index.html (메인 페이지)
- static/style.css (스타일)
- requirements.txt (flask, jinja2)
- README.md (설치/실행 방법)

⚠️ 주의: 모든 파일을 완전히 구현하고, 즉시 실행 가능해야 합니다!"""
    
    @staticmethod
    def data_analysis_example():
        return """pandas와 matplotlib을 사용한 완전한 데이터 분석 도구를 만들어주세요.

🎯 구체적인 기능:
- CSV 파일 자동 로드 및 분석
- 기본 통계 (평균, 중앙값, 표준편차)
- 히스토그램, 산점도, 상관관계 매트릭스 생성
- HTML 리포트 자동 생성
- 명령줄에서 실행 가능

🔧 기술 스택:
- pandas (데이터 처리)
- matplotlib/seaborn (시각화)
- jinja2 (HTML 리포트)
- argparse (CLI)

📁 필요한 파일:
- main.py (메인 실행 파일)
- analyzer.py (분석 로직)
- report_generator.py (리포트 생성)
- templates/report.html (리포트 템플릿)
- sample_data.csv (예제 데이터)
- requirements.txt

⚠️ 주의: 실제 CSV를 읽고 그래프를 생성하는 완전한 코드 구현!"""
    
    @staticmethod
    def api_client_example():
        return """완전한 REST API 클라이언트 라이브러리를 만들어주세요.

🎯 구체적인 기능:
- APIClient 클래스 (GET, POST, PUT, DELETE)
- 자동 재시도 로직 (exponential backoff)
- JSON 응답 자동 파싱
- 에러 처리 및 로깅
- 설정 파일 지원 (config.json)
- 사용 예제 및 테스트

🔧 기술 스택:
- requests (HTTP 클라이언트)
- json (설정/응답 처리)
- logging (로깅)
- time (재시도 로직)

📁 필요한 파일:
- client.py (APIClient 클래스)
- config.py (설정 관리)
- exceptions.py (커스텀 예외)
- examples.py (사용 예제)
- tests/test_client.py (테스트)
- config.json (설정 파일)
- requirements.txt

⚠️ 주의: 실제 API 호출이 가능한 완전한 클라이언트 구현!"""
    
    @staticmethod
    def cli_tool_example():
        return """Click을 사용한 완전한 명령줄 도구를 만들어주세요.

🎯 구체적인 기능:
- 다중 하위 명령어 (init, process, status)
- 파일 처리 (텍스트 파일 읽기/쓰기)
- 진행률 표시바 (tqdm)
- 설정 파일 지원 (.config.yaml)
- 컬러 출력 (rich)
- 로깅 및 디버그 모드

🔧 기술 스택:
- click (CLI 프레임워크)
- tqdm (진행률 표시)
- rich (컬러 출력)
- pyyaml (설정 파일)

📁 필요한 파일:
- cli.py (메인 CLI)
- commands/ (하위 명령어들)
  - init.py
  - process.py
  - status.py
- utils.py (유틸리티)
- config.yaml (기본 설정)
- requirements.txt

⚠️ 주의: 실제로 명령어가 작동하는 완전한 CLI 도구 구현!"""
    
    @staticmethod
    def game_example():
        return """pygame을 사용한 간단한 2D 게임을 만들어주세요.

🎯 구체적인 기능:
- 플레이어 캐릭터 (키보드로 이동)
- 적 캐릭터 (자동 이동)
- 충돌 감지
- 점수 시스템
- 게임 오버 화면
- 사운드 효과 (선택사항)

🔧 기술 스택:
- pygame (게임 엔진)
- math (물리 계산)

📁 필요한 파일:
- game.py (메인 게임)
- player.py (플레이어 클래스)
- enemy.py (적 클래스)
- assets/ (이미지, 사운드)
- requirements.txt

⚠️ 주의: 실제로 실행되는 완전한 게임 구현!"""

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
        print("6. 2D 게임 예제 (pygame)")
        
        choice = input("\n선택 (1-6): ").strip()
        
        if choice == "1":
            project_request = input("만들고 싶은 프로젝트를 상세히 설명해주세요: ").strip()
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
        elif choice == "6":
            project_request = ProjectExamples.game_example()
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