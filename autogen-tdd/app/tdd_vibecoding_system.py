import sys
from pathlib import Path

# ⚠️ 반드시 다른 모든 import 이전에 경로 설정
def setup_project_path():
    """프로젝트 루트 경로를 sys.path에 추가"""
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent 
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        print(f"✅ 프로젝트 루트 추가: {project_root}")
    app_dir = project_root / "app"
    if not app_dir.exists():
        raise FileNotFoundError(f"app 디렉토리를 찾을 수 없습니다: {app_dir}")
    return project_root

setup_project_path()

import asyncio
from typing import Dict, List, Optional
import streamlit as st
import os
import traceback
import openai
import google.generativeai as genai
from datetime import datetime
import time

# 실제 AI 클라이언트 클래스들
class AIClient:
    """통합 AI 클라이언트"""
    
    def __init__(self):
        self.openai_client = None
        self.gemini_model = None
        self.current_provider = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """AI 클라이언트들 초기화"""
        # OpenAI 클라이언트 초기화
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            try:
                self.openai_client = openai.OpenAI(api_key=openai_key)
                self.current_provider = "openai"
                print("✅ OpenAI 클라이언트 초기화 성공")
            except Exception as e:
                print(f"⚠️ OpenAI 클라이언트 초기화 실패: {e}")
        
        # Gemini 클라이언트 초기화
        gemini_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if gemini_key:
            try:
                genai.configure(api_key=gemini_key)
                self.gemini_model = genai.GenerativeModel('gemini-pro')
                if not self.current_provider:  # OpenAI가 없으면 Gemini 사용
                    self.current_provider = "gemini"
                print("✅ Gemini 클라이언트 초기화 성공")
            except Exception as e:
                print(f"⚠️ Gemini 클라이언트 초기화 실패: {e}")
        
        if not self.current_provider:
            raise Exception("OpenAI 또는 Gemini API 키가 필요합니다.")
    
    def generate_response(self, prompt: str, system_message: str = "", max_tokens: int = 2000) -> str:
        """AI 응답 생성"""
        try:
            if self.current_provider == "openai" and self.openai_client:
                return self._generate_openai_response(prompt, system_message, max_tokens)
            elif self.current_provider == "gemini" and self.gemini_model:
                return self._generate_gemini_response(prompt, system_message, max_tokens)
            else:
                raise Exception("사용 가능한 AI 클라이언트가 없습니다.")
        except Exception as e:
            print(f"❌ AI 응답 생성 실패: {e}")
            # 폴백으로 다른 프로바이더 시도
            if self.current_provider == "openai" and self.gemini_model:
                try:
                    return self._generate_gemini_response(prompt, system_message, max_tokens)
                except:
                    pass
            elif self.current_provider == "gemini" and self.openai_client:
                try:
                    return self._generate_openai_response(prompt, system_message, max_tokens)
                except:
                    pass
            raise e
    
    def _generate_openai_response(self, prompt: str, system_message: str, max_tokens: int) -> str:
        """OpenAI API 호출"""
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",  # 또는 gpt-3.5-turbo
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.7
        )
        return response.choices[0].message.content
    
    def _generate_gemini_response(self, prompt: str, system_message: str, max_tokens: int) -> str:
        """Gemini API 호출"""
        full_prompt = f"{system_message}\n\n{prompt}" if system_message else prompt
        response = self.gemini_model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=0.7
            )
        )
        return response.text

class RealTDDAgent:
    """실제 TDD 작업을 수행하는 AI 에이전트"""
    
    def __init__(self, ai_client: AIClient, agent_type: str):
        self.ai_client = ai_client
        self.agent_type = agent_type
        self.system_messages = {
            "test_generator": """당신은 전문적인 테스트 코드 생성 전문가입니다. 
주어진 요구사항에 따라 완전하고 실행 가능한 단위 테스트 코드를 Python unittest 형태로 생성해주세요.
테스트는 다음 원칙을 따라야 합니다:
1. 명확하고 읽기 쉬운 테스트 이름
2. 적절한 엣지 케이스 포함
3. 입력 검증 테스트
4. 예외 상황 테스트
5. 실제 실행 가능한 코드""",
            
            "code_generator": """당신은 전문적인 Python 개발자입니다.
주어진 요구사항과 테스트 코드에 따라 실제 작동하는 Python 코드를 생성해주세요.
코드는 다음 원칙을 따라야 합니다:
1. 클린 코드 원칙 준수
2. 적절한 오류 처리
3. 명확한 함수/클래스 구조
4. 주석과 docstring 포함
5. 테스트를 통과할 수 있는 완전한 구현""",
            
            "refactorer": """당신은 코드 품질 전문가입니다.
주어진 코드를 분석하고 다음 관점에서 리팩토링해주세요:
1. 코드 중복 제거
2. 함수/클래스 분리
3. 변수명 개선
4. 성능 최적화
5. 가독성 향상
6. 디자인 패턴 적용""",
            
            "orchestrator": """당신은 TDD 프로세스를 관리하는 전문가입니다.
사용자의 요구사항을 분석하고 적절한 작업 순서와 전략을 제시해주세요.
다음을 고려해서 응답하세요:
1. 요구사항 명확화
2. 테스트 우선 개발 전략
3. 단계별 구현 계획
4. 리스크 요소 식별"""
        }
    
    def generate_response(self, user_input: str, context: str = "") -> str:
        """AI 에이전트 응답 생성"""
        system_message = self.system_messages.get(self.agent_type, "")
        
        # 컨텍스트가 있으면 포함
        prompt = f"컨텍스트: {context}\n\n사용자 요청: {user_input}" if context else user_input
        
        try:
            response = self.ai_client.generate_response(
                prompt=prompt,
                system_message=system_message,
                max_tokens=2000
            )
            return response
        except Exception as e:
            return f"❌ AI 응답 생성 중 오류: {str(e)}"

class TDDLiveCodingUI:
    def __init__(self, system_instance=None):
        self.system_instance = system_instance
        self.ai_client = None
        self.agents = {}
        self.current_state = {
            "test_count": 0,
            "code_count": 0,
            "test_passed": 0,
            "test_total": 0,
            "quality_score": 0,
            "current_phase": "대기중"
        }
        self._init_session_state()
        self._initialize_ai_agents()
        
    def _init_session_state(self):
        """세션 상태 초기화"""
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        if 'current_code' not in st.session_state:
            st.session_state.current_code = "# 여기에 코드를 작성하세요\n\ndef example_function():\n    pass"
        if 'test_code' not in st.session_state:
            st.session_state.test_code = "# 테스트 코드가 여기에 표시됩니다\n\nimport unittest\n\nclass TestExample(unittest.TestCase):\n    pass"
        if 'test_results' not in st.session_state:
            st.session_state.test_results = []
        if 'debug_logs' not in st.session_state:
            st.session_state.debug_logs = []
        if 'agent_status' not in st.session_state:
            st.session_state.agent_status = {}
        if 'workflow_progress' not in st.session_state:
            st.session_state.workflow_progress = {'current_step': 0}
        if 'current_active_agent' not in st.session_state:
            st.session_state.current_active_agent = None
        if 'is_processing' not in st.session_state:
            st.session_state.is_processing = False
    
    def _initialize_ai_agents(self):
        """실제 AI 에이전트들 초기화"""
        try:
            self.ai_client = AIClient()
            self.agents = {
                'orchestrator': RealTDDAgent(self.ai_client, 'orchestrator'),
                'test_generator': RealTDDAgent(self.ai_client, 'test_generator'),
                'code_generator': RealTDDAgent(self.ai_client, 'code_generator'),
                'refactorer': RealTDDAgent(self.ai_client, 'refactorer')
            }
            self.log_debug("✅ 실제 AI 에이전트 초기화 완료", "INFO")
        except Exception as e:
            self.log_debug(f"❌ AI 에이전트 초기화 실패: {str(e)}", "ERROR")
            # 에러가 발생해도 UI는 계속 동작하도록 함
            self.agents = {}
            
    def log_debug(self, message: str, level: str = "INFO"):
        """디버그 로그 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message
        }
        st.session_state.debug_logs.append(log_entry)
        
        if len(st.session_state.debug_logs) > 100:
            st.session_state.debug_logs = st.session_state.debug_logs[-100:]
        
        print(f"[{level}] [{timestamp}] {message}")
    
    def handle_user_input_real(self, user_input: str) -> str:
        """실제 AI 에이전트와 사용자 입력 처리"""
        if not self.ai_client:
            return "❌ AI 클라이언트가 초기화되지 않았습니다. API 키를 확인해주세요."
        
        try:
            st.session_state.is_processing = True
            self.log_debug(f"🚀 실제 AI 에이전트에게 요청: {user_input}")
            
            # 대화 콘텍스트 수집
            context = self._get_conversation_context()
            
            # 의도 분석 및 적절한 에이전트 선택
            if "테스트" in user_input.lower():
                response = self._handle_test_request_with_ai(user_input, context)
            elif "코드" in user_input.lower() or "구현" in user_input.lower():
                response = self._handle_code_request_with_ai(user_input, context)
            elif "리팩토링" in user_input.lower() or "개선" in user_input.lower():
                response = self._handle_refactor_request_with_ai(user_input, context)
            else:
                response = self._handle_general_request_with_ai(user_input, context)
            
            st.session_state.is_processing = False
            self.log_debug("✅ AI 응답 처리 완료")
            return response
            
        except Exception as e:
            st.session_state.is_processing = False
            error_msg = f"❌ AI 처리 중 오류: {str(e)}"
            self.log_debug(error_msg, "ERROR")
            return error_msg
    
    def _handle_test_request_with_ai(self, user_input: str, context: str) -> str:
        """실제 AI를 사용한 테스트 요청 처리"""
        try:
            self.set_agent_status('test_generator', 'working', 'AI 테스트 생성 중', 20)
            
            # AI에게 테스트 코드 생성 요청
            self.log_debug("🧪 AI에게 테스트 코드 생성 요청 중...")
            
            # 현재 코드도 컨텍스트에 포함
            full_context = f"{context}\n\n현재 코드:\n{st.session_state.current_code}"
            
            test_prompt = f"""
다음 요구사항에 대한 완전한 Python unittest 테스트 코드를 생성해주세요:

요구사항: {user_input}

컨텍스트: {full_context}

다음 형식으로 응답해주세요:
```python
import unittest

class Test[기능명](unittest.TestCase):
    # 실제 실행 가능한 테스트 코드
    pass

if __name__ == '__main__':
    unittest.main()
```
"""
            
            self.set_agent_status('test_generator', 'processing', 'AI 응답 생성 중', 60)
            
            # 실제 AI 호출
            ai_response = self.agents['test_generator'].generate_response(test_prompt)
            
            self.set_agent_status('test_generator', 'processing', '테스트 코드 파싱 중', 80)
            
            # AI 응답에서 코드 부분 추출
            test_code = self._extract_code_from_response(ai_response)
            
            if test_code:
                st.session_state.test_code = test_code
                self.set_agent_status('test_generator', 'completed', '테스트 생성 완료', 100)
                self.log_debug("✅ AI로 테스트 코드 생성 완료")
                return f"✅ AI가 테스트 코드를 생성했습니다!\n\n**생성된 응답 요약:**\n{ai_response[:200]}..."
            else:
                # 코드 추출 실패 시 전체 응답을 테스트 코드로 설정
                st.session_state.test_code = ai_response
                self.log_debug("⚠️ 코드 추출 실패, 전체 응답 사용", "WARNING")
                return f"✅ AI가 테스트 코드를 생성했습니다!\n\n{ai_response}"
                
        except Exception as e:
            self.set_agent_status('test_generator', 'error', f'AI 테스트 생성 실패: {str(e)}', 0)
            error_msg = f"❌ AI 테스트 생성 중 오류: {str(e)}"
            self.log_debug(error_msg, "ERROR")
            return error_msg
    
    def _handle_code_request_with_ai(self, user_input: str, context: str) -> str:
        """실제 AI를 사용한 코드 요청 처리"""
        try:
            self.set_agent_status('code_generator', 'working', 'AI 코드 생성 중', 20)
            
            self.log_debug("💻 AI에게 코드 구현 요청 중...")
            
            # 테스트 코드도 컨텍스트에 포함
            full_context = f"{context}\n\n현재 테스트 코드:\n{st.session_state.test_code}"
            
            code_prompt = f"""
다음 요구사항을 만족하는 완전한 Python 코드를 구현해주세요:

요구사항: {user_input}

컨텍스트: {full_context}

다음 사항을 고려해서 구현해주세요:
1. 클린 코드 원칙 준수
2. 적절한 예외 처리
3. 명확한 함수/클래스 구조
4. 주석과 docstring 포함
5. 테스트를 통과할 수 있는 완전한 구현

Python 코드만 응답해주세요.
"""
            
            self.set_agent_status('code_generator', 'processing', 'AI 응답 생성 중', 60)
            
            # 실제 AI 호출
            ai_response = self.agents['code_generator'].generate_response(code_prompt)
            
            self.set_agent_status('code_generator', 'processing', '코드 파싱 중', 80)
            
            # AI 응답에서 코드 부분 추출
            code = self._extract_code_from_response(ai_response)
            
            if code:
                st.session_state.current_code = code
                self.set_agent_status('code_generator', 'completed', '코드 생성 완료', 100)
                self.log_debug("✅ AI로 코드 구현 완료")
                return f"✅ AI가 코드를 구현했습니다!\n\n**생성된 응답 요약:**\n{ai_response[:200]}..."
            else:
                # 코드 추출 실패 시 전체 응답을 코드로 설정
                st.session_state.current_code = ai_response
                self.log_debug("⚠️ 코드 추출 실패, 전체 응답 사용", "WARNING")
                return f"✅ AI가 코드를 구현했습니다!\n\n{ai_response}"
                
        except Exception as e:
            self.set_agent_status('code_generator', 'error', f'AI 코드 생성 실패: {str(e)}', 0)
            error_msg = f"❌ AI 코드 생성 중 오류: {str(e)}"
            self.log_debug(error_msg, "ERROR")
            return error_msg
    
    def _handle_refactor_request_with_ai(self, user_input: str, context: str) -> str:
        """실제 AI를 사용한 리팩토링 요청 처리"""
        try:
            self.set_agent_status('refactorer', 'working', 'AI 리팩토링 중', 20)
            
            self.log_debug("🔧 AI에게 리팩토링 요청 중...")
            
            current_code = st.session_state.current_code
            
            refactor_prompt = f"""
다음 코드를 리팩토링해주세요:

요구사항: {user_input}
컨텍스트: {context}

현재 코드:
```python
{current_code}
```

다음 관점에서 리팩토링해주세요:
1. 코드 중복 제거
2. 함수/클래스 분리 개선
3. 변수명 및 함수명 개선
4. 성능 최적화
5. 가독성 향상
6. 적절한 디자인 패턴 적용

리팩토링된 코드만 응답해주세요.
"""
            
            self.set_agent_status('refactorer', 'processing', 'AI 응답 생성 중', 60)
            
            # 실제 AI 호출
            ai_response = self.agents['refactorer'].generate_response(refactor_prompt)
            
            self.set_agent_status('refactorer', 'processing', '리팩토링 코드 적용 중', 80)
            
            # AI 응답에서 코드 부분 추출
            refactored_code = self._extract_code_from_response(ai_response)
            
            if refactored_code:
                st.session_state.current_code = refactored_code
                self.set_agent_status('refactorer', 'completed', '리팩토링 완료', 100)
                self.log_debug("✅ AI로 리팩토링 완료")
                return f"✅ AI가 코드를 리팩토링했습니다!\n\n**개선 사항:**\n{ai_response[:200]}..."
            else:
                # 코드 추출 실패 시 전체 응답을 코드로 설정
                st.session_state.current_code = ai_response
                self.log_debug("⚠️ 리팩토링 코드 추출 실패, 전체 응답 사용", "WARNING")
                return f"✅ AI가 코드를 리팩토링했습니다!\n\n{ai_response}"
                
        except Exception as e:
            self.set_agent_status('refactorer', 'error', f'AI 리팩토링 실패: {str(e)}', 0)
            error_msg = f"❌ AI 리팩토링 중 오류: {str(e)}"
            self.log_debug(error_msg, "ERROR")
            return error_msg
    
    def _handle_general_request_with_ai(self, user_input: str, context: str) -> str:
        """실제 AI를 사용한 일반 요청 처리"""
        try:
            self.set_agent_status('orchestrator', 'processing', 'AI 분석 중', 60)
            
            self.log_debug("🎯 AI 오케스트레이터에게 요청 중...")
            
            general_prompt = f"""
다음 사용자 요청을 분석하고 TDD 개발 관점에서 적절한 조언을 제공해주세요:

사용자 요청: {user_input}
컨텍스트: {context}

다음을 포함해서 응답해주세요:
1. 요구사항 분석
2. 추천하는 TDD 접근 방법
3. 단계별 구현 계획
4. 예상되는 테스트 케이스들
5. 다음 단계 제안

친근하고 전문적인 톤으로 응답해주세요.
"""
            
            # 실제 AI 호출
            ai_response = self.agents['orchestrator'].generate_response(general_prompt)
            
            self.set_agent_status('orchestrator', 'completed', '분석 완료', 100)
            self.log_debug("✅ AI 오케스트레이터 응답 완료")
            
            return ai_response
                
        except Exception as e:
            self.set_agent_status('orchestrator', 'error', f'AI 분석 실패: {str(e)}', 0)
            error_msg = f"❌ AI 분석 중 오류: {str(e)}"
            self.log_debug(error_msg, "ERROR")
            return error_msg
    
    def _extract_code_from_response(self, response: str) -> Optional[str]:
        """AI 응답에서 코드 부분만 추출"""
        try:
            # ```python으로 감싸진 코드 찾기
            if "```python" in response:
                start = response.find("```python") + 9
                end = response.find("```", start)
                if end != -1:
                    return response[start:end].strip()
            
            # ```로만 감싸진 코드 찾기
            elif "```" in response:
                parts = response.split("```")
                if len(parts) >= 3:
                    return parts[1].strip()
            
            # 코드 블록이 없으면 전체 응답에서 import나 class, def가 있는지 확인
            elif any(keyword in response for keyword in ["import ", "class ", "def ", "if __name__"]):
                return response.strip()
            
            return None
        except Exception as e:
            self.log_debug(f"코드 추출 중 오류: {str(e)}", "ERROR")
            return None
    
    def _get_conversation_context(self) -> str:
        """대화 콘텍스트 가져오기"""
        if 'conversation_context' not in st.session_state:
            return ""
        
        context_parts = []
        for conv in st.session_state.conversation_context[-3:]:
            context_parts.append(f"사용자: {conv['user_input']}")
            if 'response' in conv:
                context_parts.append(f"어시스턴트: {conv['response'][:100]}...")
        
        return "\n".join(context_parts)
    
    def set_agent_status(self, agent_id: str, status: str, task: str = "", progress: float = 0):
        """에이전트 상태 설정"""
        if agent_id not in st.session_state.agent_status:
            st.session_state.agent_status[agent_id] = {}
        
        progress = max(0.0, min(100.0, progress))
        
        st.session_state.agent_status[agent_id].update({
            'active': status in ['working', 'processing'],
            'status': status,
            'current_task': task,
            'progress': progress,
            'last_action': f"{status}: {datetime.now().strftime('%H:%M:%S')}"
        })
        
        if status in ['working', 'processing']:
            st.session_state.current_active_agent = agent_id
            self.log_debug(f"🤖 에이전트 활성화: {agent_id} - {task} ({progress}%)")
        elif status == 'completed':
            if st.session_state.get('current_active_agent') == agent_id:
                st.session_state.current_active_agent = None
            self.log_debug(f"✅ 에이전트 완료: {agent_id}")
        elif status == 'error':
            st.session_state.agent_status[agent_id]['progress'] = 0
            self.log_debug(f"❌ 에이전트 오류: {agent_id} - {task}", "ERROR")

    # UI 렌더링 메서드들은 기존과 동일하게 유지 (render_dashboard, render_chat_interface 등)
    def render_dashboard(self):
        """실시간 대시보드 렌더링"""
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.title("🚀 TDD 라이브 코딩 환경 (실제 AI 연동)")
        with col2:
            if st.session_state.get('is_processing', False):
                st.error("🔴 AI 처리 중...")
            else:
                # AI 클라이언트 상태 표시
                if self.ai_client and self.ai_client.current_provider:
                    st.success(f"🟢 {self.ai_client.current_provider.upper()} 연결됨")
                else:
                    st.warning("🟡 AI 연결 안됨")
        with col3:
            if st.button("🔄 새로고침"):
                st.rerun()
        
        # AI 상태 표시
        if self.ai_client:
            st.info(f"🤖 현재 AI: {self.ai_client.current_provider.upper() if self.ai_client.current_provider else 'None'}")
        else:
            st.error("❌ AI 클라이언트 초기화 실패")
        
        # 나머지 대시보드 렌더링...
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "💬 AI 채팅", 
            "💻 코드 에디터", 
            "🧪 테스트 코드", 
            "📊 테스트 결과",
            "🔧 디버그 로그"
        ])
        
        with tab1:
            self.render_chat_interface()
        with tab2:
            self.render_code_editor()
        with tab3:
            self.render_test_code_editor()
        with tab4:
            self.render_test_results()
        with tab5:
            self.render_debug_interface()
    
    def render_chat_interface(self):
        """AI와의 실시간 채팅"""
        st.subheader("💬 AI 에이전트와 대화")
        
        # API 상태 표시
        if self.ai_client and self.ai_client.current_provider:
            st.success(f"✅ {self.ai_client.current_provider.upper()} API 연결됨")
        else:
            st.error("❌ AI API 연결 안됨 - API 키를 확인해주세요")
            return
        
        # 채팅 히스토리 표시
        if not st.session_state.chat_history:
            st.info("🤖 AI 에이전트와 대화를 시작해보세요! 실제 OpenAI/Gemini API가 응답합니다.")
        else:
            for message in st.session_state.chat_history[-10:]:
                with st.chat_message(message["role"]):
                    st.write(f"**{message['agent']}**: {message['content']}")
                    if message.get('timestamp'):
                        st.caption(f"⏰ {message['timestamp']}")
        
        # 사용자 입력
        user_input = st.chat_input("AI 에이전트와 대화하기 (실제 API 호출)...")
        
        if user_input:
            self.add_chat_message("user", "사용자", user_input)
            self.log_debug(f"🚀 실제 AI API 호출 시작: {user_input}")
            
            try:
                with st.spinner("🤖 AI가 실제로 응답 생성 중... (API 호출)"):
                    # 실제 AI 에이전트와 통신
                    response = self.handle_user_input_real(user_input)
                    if response:
                        self.add_chat_message("assistant", "AI 어시스턴트", response)
                        self.log_debug(f"✅ AI 응답 완료: {response[:50]}...")
            except Exception as e:
                error_msg = f"AI 통신 오류: {str(e)}"
                st.error(error_msg)
                self.log_debug(error_msg, "ERROR")
                self.add_chat_message("system", "오류", error_msg)
                
            st.rerun()
    
    def add_chat_message(self, role: str, agent: str, content: str):
        """채팅 메시지 추가"""
        message = {
            "role": role,
            "agent": agent,
            "content": content,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        st.session_state.chat_history.append(message)
        self.log_debug(f"💬 채팅 메시지 추가: [{agent}] {content[:50]}...")
    
    # 나머지 UI 메서드들 (render_code_editor, render_test_code_editor 등)은 기존과 동일...
    def render_code_editor(self):
        """코드 에디터 렌더링"""
        st.subheader("📝 메인 코드")
        
        new_code = st.text_area(
            "코드를 입력하세요:",
            value=st.session_state.current_code,
            height=400,
            key="code_editor"
        )
        
        if new_code != st.session_state.current_code:
            st.session_state.current_code = new_code
            self.log_debug("📝 코드 변경 감지")
            
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 코드 저장", type="primary"):
                st.success("코드가 저장되었습니다!")
                
        with col2:
            if st.button("▶️ 코드 실행"):
                try:
                    compile(st.session_state.current_code, '<string>', 'exec')
                    st.success("✅ 코드 구문이 올바릅니다!")
                except SyntaxError as e:
                    st.error(f"❌ 구문 오류: {str(e)}")
                
        with col3:
            if st.button("🔄 코드 초기화"):
                st.session_state.current_code = "# 여기에 코드를 작성하세요\n\ndef example_function():\n    pass"
                st.rerun()
    
    def render_test_code_editor(self):
        """테스트 코드 에디터"""
        st.subheader("🧪 테스트 코드")
        
        new_test_code = st.text_area(
            "테스트 코드:",
            value=st.session_state.test_code,
            height=400,
            key="test_code_editor"
        )
        
        if new_test_code != st.session_state.test_code:
            st.session_state.test_code = new_test_code
            
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🧪 테스트 실행", type="primary"):
                st.info("테스트 실행 시뮬레이션 (실제 실행은 추후 구현)")
                
        with col2:
            if st.button("🤖 AI 테스트 생성"):
                if self.ai_client:
                    response = self.handle_user_input_real("현재 코드에 대한 완전한 단위 테스트를 생성해주세요.")
                    if response:
                        self.add_chat_message("assistant", "AI 테스트 생성기", response)
                        st.rerun()
                else:
                    st.error("AI 클라이언트가 연결되지 않았습니다.")
    
    def render_test_results(self):
        """테스트 결과"""
        st.subheader("📊 테스트 실행 결과")
        st.info("테스트 실행 기능은 추후 구현됩니다.")
    
    def render_debug_interface(self):
        """디버그 인터페이스"""
        st.subheader("🔧 디버그 로그")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 로그 새로고침"):
                st.rerun()
        with col2:
            if st.button("🗑️ 로그 지우기"):
                st.session_state.debug_logs = []
                st.rerun()
        with col3:
            log_level = st.selectbox("로그 레벨", ["ALL", "INFO", "WARNING", "ERROR"], index=0)
        
        filtered_logs = st.session_state.debug_logs
        if log_level != "ALL":
            filtered_logs = [log for log in filtered_logs if log['level'] == log_level]
        
        if filtered_logs:
            for log in filtered_logs[-20:]:
                level_color = {"INFO": "🔵", "WARNING": "🟡", "ERROR": "🔴"}.get(log['level'], "⚪")
                with st.expander(f"{level_color} [{log['timestamp']}] {log['message'][:50]}...", expanded=False):
                    st.code(log['message'])
        else:
            st.info("표시할 로그가 없습니다.")

class TDDLiveCodingSystem:
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.ui = TDDLiveCodingUI(system_instance=self)
        
    def get_agents(self):
        """UI에서 에이전트 가져오기"""
        return self.ui.agents if self.ui else {}

def check_environment():
    """환경 설정 확인"""
    issues = []
    
    # OpenAI API 키 확인
    if os.getenv('OPENAI_API_KEY'):
        issues.append("✅ OPENAI_API_KEY 설정됨")
    else:
        issues.append("❌ OPENAI_API_KEY 환경변수 없음")
    
    # Gemini API 키 확인
    if os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY'):
        issues.append("✅ GEMINI_API_KEY 설정됨")
    else:
        issues.append("❌ GEMINI_API_KEY 환경변수 없음")
    
    return issues

@st.cache_resource
def get_system_instance():
    """시스템 인스턴스 캐시"""
    return TDDLiveCodingSystem("./my_project")

def main():
    """메인 Streamlit 앱"""
    st.set_page_config(
        page_title="TDD 바이브코딩 시스템 (실제 AI)",
        page_icon="🚀",
        layout="wide"
    )
    
    st.title("🚀 TDD 바이브코딩 시스템 (실제 AI 연동)")
    
    # 환경 확인
    with st.sidebar:
        st.header("🔧 시스템 상태")
        
        env_issues = check_environment()
        for issue in env_issues:
            if "✅" in issue:
                st.success(issue)
            else:
                st.error(issue)
        
        # API 키 설정 안내
        if not (os.getenv('OPENAI_API_KEY') or os.getenv('GEMINI_API_KEY')):
            st.warning("⚠️ 최소 하나의 API 키가 필요합니다")
            st.info("""
            **API 키 설정:**
            ```bash
            # OpenAI
            export OPENAI_API_KEY='your-openai-key'
            
            # 또는 Gemini
            export GEMINI_API_KEY='your-gemini-key'
            ```
            """)
    
    try:
        # 시스템 초기화
        system = get_system_instance()
        
        # 메인 대시보드
        system.ui.render_dashboard()
        
        # TDD 개발 섹션
        st.header("🎯 실제 AI와 함께하는 TDD 개발")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            requirement = st.text_area(
                "요구사항을 입력하세요:",
                height=150,
                placeholder="예: 간단한 계산기를 만들어주세요. 덧셈, 뺄셈, 곱셈, 나눗셈이 가능해야 합니다.",
                help="AI가 실제로 분석하고 TDD 프로세스를 진행합니다."
            )
        
        with col2:
            st.write("")
            st.write("")
            
            if st.button("🚀 AI TDD 개발 시작", type="primary", use_container_width=True):
                if requirement.strip():
                    # AI 클라이언트 확인
                    if not system.ui.ai_client:
                        st.error("❌ AI API 연결이 필요합니다.")
                        return
                    
                    system.ui.add_chat_message("user", "사용자", f"새 프로젝트: {requirement}")
                    
                    with st.spinner("🤖 AI가 실제로 전체 TDD 프로세스 실행 중..."):
                        try:
                            # 오케스트레이터로 전체 계획 수립
                            plan_response = system.ui.handle_user_input_real(f"다음 요구사항을 분석하고 TDD 개발 계획을 세워주세요: {requirement}")
                            system.ui.add_chat_message("assistant", "AI 기획자", plan_response)
                            
                            # 테스트 생성
                            test_response = system.ui.handle_user_input_real(f"다음 요구사항에 대한 완전한 테스트 코드를 생성해주세요: {requirement}")
                            system.ui.add_chat_message("assistant", "AI 테스트 생성기", test_response)
                            
                            # 코드 구현
                            code_response = system.ui.handle_user_input_real(f"테스트를 통과하는 코드를 구현해주세요: {requirement}")
                            system.ui.add_chat_message("assistant", "AI 코드 생성기", code_response)
                            
                            st.success("🎉 AI TDD 개발 완료!")
                            st.balloons()
                            
                        except Exception as e:
                            st.error(f"❌ AI TDD 프로세스 중 오류: {str(e)}")
                            
                        st.rerun()
                else:
                    st.error("요구사항을 입력해주세요.")
            
            st.write("---")
            st.write("**개별 AI 작업:**")
            
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                if st.button("🧪 AI 테스트 생성"):
                    if requirement.strip():
                        response = system.ui.handle_user_input_real(f"테스트 코드 생성: {requirement}")
                        system.ui.add_chat_message("assistant", "AI 테스터", response)
                        st.rerun()
            
            with col_b:
                if st.button("💻 AI 코드 구현"):
                    if requirement.strip():
                        response = system.ui.handle_user_input_real(f"코드 구현: {requirement}")
                        system.ui.add_chat_message("assistant", "AI 개발자", response)
                        st.rerun()
            
            with col_c:
                if st.button("🔧 AI 리팩토링"):
                    if st.session_state.current_code:
                        response = system.ui.handle_user_input_real(f"코드 리팩토링: {requirement}")
                        system.ui.add_chat_message("assistant", "AI 리팩토러", response)
                        st.rerun()
    
    except Exception as e:
        st.error(f"❌ 시스템 오류: {str(e)}")
        with st.expander("오류 상세"):
            st.code(traceback.format_exc())

if __name__ == "__main__":
    main()