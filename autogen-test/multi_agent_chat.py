# multi_agent_chat.py - 완전한 다중 에이전트 협업 시스템
import asyncio
import os
import json
from datetime import datetime
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
        print(f"📱 사용 모델: {cls.GEMINI_MODEL}")
        return True

class MultiAgentSystem:
    """다중 에이전트 협업 시스템"""
    
    def __init__(self):
        # 설정 검증
        Config.validate_config()
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
        """전문화된 에이전트들을 설정"""
        
        # 기획자 에이전트
        self.planner = AssistantAgent(
            name="Planner",
            model_client=self.create_model_client(),
            system_message="""당신은 프로젝트 기획 전문가입니다.
            문제를 체계적으로 분석하고 단계별 계획을 수립합니다.
            
            다음과 같은 형식으로 응답하세요:
            1. 문제 분석
            2. 목표 설정  
            3. 단계별 계획
            4. 필요한 자원
            
            간결하고 실행 가능한 계획을 제시해주세요."""
        )
        
        # 개발자 에이전트
        self.developer = AssistantAgent(
            name="Developer",
            model_client=self.create_model_client(),
            system_message="""당신은 숙련된 소프트웨어 개발자입니다.
            
            역할:
            - 코드 설계 및 구현
            - 기술 스택 선택
            - 최적화 및 리팩토링
            
            Python, JavaScript, React 등에 능통하며,
            깨끗하고 유지보수 가능한 코드를 작성합니다."""
        )
        
        # 리뷰어 에이전트
        self.reviewer = AssistantAgent(
            name="Reviewer",
            model_client=self.create_model_client(),
            system_message="""당신은 코드 리뷰 및 품질 관리 전문가입니다.
            
            체크 항목:
            ✅ 코드 품질 및 가독성
            ✅ 보안 취약점
            ✅ 성능 최적화
            ✅ 베스트 프랙티스 준수
            
            건설적인 피드백과 구체적인 개선 방안을 제시하세요."""
        )
    
    def create_team(self, max_turns: int = 6):
        """지정된 최대 턴 수로 팀 생성"""
        termination_condition = MaxMessageTermination(max_turns)
        return RoundRobinGroupChat(
            participants=[
                self.planner,
                self.developer, 
                self.reviewer
            ],
            termination_condition=termination_condition
        )
    
    async def start_collaboration(self, task: str, max_turns: int = 6):
        """다중 에이전트 협업 시작"""
        print("🤝 다중 에이전트 협업 시스템 시작!")
        print(f"📋 작업: {task}")
        print(f"👥 참여 에이전트: Planner, Developer, Reviewer")
        print(f"🔄 최대 턴 수: {max_turns}\n")
        
        try:
            # 지정된 최대 턴 수로 팀 생성
            team = self.create_team(max_turns)
            
            # 협업 시작 - task만 전달
            response = await team.run(task=task)
            
            print("\n✅ 협업이 완료되었습니다!")
            print(f"📊 총 {len(response.messages)}개의 메시지가 교환되었습니다.")
            
            # 결과 출력 방식 선택
            print("\n어떤 방식으로 결과를 확인하시겠습니까?")
            print("1. 요약만 보기 (기본)")
            print("2. 전체 대화 내용 보기")
            print("3. 최종 결과물만 보기")
            print("4. 전체 + 파일 저장")
            
            view_choice = input("선택 (1-4, 엔터=1): ").strip() or "1"
            
            if view_choice == "1":
                self.show_summary(response)
            elif view_choice == "2":
                self.show_full_conversation(response)
            elif view_choice == "3":
                self.show_final_result(response)
            elif view_choice == "4":
                self.show_full_conversation(response)
                await self.save_collaboration_result(task, response)
            else:
                self.show_summary(response)
            
            return response
            
        except Exception as e:
            print(f"❌ 협업 중 오류가 발생했습니다: {e}")
            return None
        finally:
            # 리소스 정리
            await self.cleanup()
    
    def show_summary(self, response):
        """협업 결과 요약 보기"""
        print("\n📋 협업 결과 요약:")
        for i, message in enumerate(response.messages[-3:], 1):
            agent_name = message.source
            content_preview = message.content[:100] + "..." if len(message.content) > 100 else message.content
            print(f"{i}. {agent_name}: {content_preview}")
    
    def show_full_conversation(self, response):
        """전체 대화 내용 보기"""
        print("\n" + "="*60)
        print("📋 전체 협업 과정 및 결과물")
        print("="*60)
        
        for i, message in enumerate(response.messages, 1):
            agent_name = message.source
            content = message.content
            
            # 각 에이전트별로 다른 이모지
            emoji_map = {
                "user": "👤",
                "Planner": "📋",
                "Developer": "💻", 
                "Reviewer": "🔍"
            }
            emoji = emoji_map.get(agent_name, "🤖")
            
            print(f"\n{emoji} {agent_name} (메시지 {i}):")
            print("-" * 40)
            print(content)
    
    def show_final_result(self, response):
        """최종 결과물만 보기"""
        if len(response.messages) > 0:
            final_message = response.messages[-1]
            print("\n" + "="*60)
            print("🎯 최종 결과물")
            print("="*60)
            print(f"작성자: {final_message.source}")
            print(f"내용:\n{final_message.content}")
        else:
            print("❌ 결과물이 없습니다.")
    
    async def save_collaboration_result(self, task: str, response):
        """협업 결과를 파일로 저장"""
        try:
            # 타임스탬프 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"collaboration_result_{timestamp}.md"
            
            # 마크다운 형식으로 저장
            content = f"# 다중 에이전트 협업 결과\n\n"
            content += f"**작업**: {task}\n\n"
            content += f"**완료 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            content += f"**참여 에이전트**: Planner, Developer, Reviewer\n\n"
            content += f"**총 메시지 수**: {len(response.messages)}\n\n"
            content += "---\n\n"
            
            # 전체 대화 내용
            content += "## 📋 전체 협업 과정\n\n"
            
            for i, message in enumerate(response.messages, 1):
                agent_name = message.source
                message_content = message.content
                
                # 에이전트별 이모지
                emoji_map = {
                    "user": "👤",
                    "Planner": "📋", 
                    "Developer": "💻",
                    "Reviewer": "🔍"
                }
                emoji = emoji_map.get(agent_name, "🤖")
                
                content += f"### {emoji} {agent_name} (메시지 {i})\n\n"
                content += f"{message_content}\n\n"
                content += "---\n\n"
            
            # 최종 결과물
            if len(response.messages) > 0:
                final_message = response.messages[-1]
                content += "## 🎯 최종 결과물\n\n"
                content += f"**작성자**: {final_message.source}\n\n"
                content += f"{final_message.content}\n\n"
            
            # 파일 저장
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ 협업 결과가 '{filename}' 파일로 저장되었습니다!")
            
            # JSON 형식으로도 저장할지 묻기
            json_choice = input("📄 JSON 형식으로도 저장하시겠습니까? (y/n): ").strip().lower()
            if json_choice in ['y', 'yes', '예']:
                json_filename = f"collaboration_result_{timestamp}.json"
                
                # JSON 데이터 구성
                json_data = {
                    "task": task,
                    "timestamp": datetime.now().isoformat(),
                    "participants": ["Planner", "Developer", "Reviewer"],
                    "total_messages": len(response.messages),
                    "messages": [
                        {
                            "index": i,
                            "source": msg.source,
                            "content": msg.content,
                            "type": msg.type if hasattr(msg, 'type') else "TextMessage"
                        }
                        for i, msg in enumerate(response.messages, 1)
                    ]
                }
                
                with open(json_filename, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2)
                
                print(f"✅ JSON 형식으로도 '{json_filename}' 파일에 저장되었습니다!")
                
        except Exception as e:
            print(f"❌ 파일 저장 중 오류가 발생했습니다: {e}")

    async def simple_task_example(self):
        """간단한 작업 예제"""
        task = """간단한 TODO 앱을 만들어주세요.

요구사항:
1. 할 일 추가/삭제/완료 기능
2. 간단한 웹 인터페이스
3. 로컬 저장소 사용

각자의 전문 분야에서 기여해주세요."""
        
        return await self.start_collaboration(task, max_turns=8)

    async def quick_test(self):
        """빠른 테스트"""
        task = "간단한 계산기 웹 앱을 만드는 계획을 세워주세요. 기본적인 사칙연산 기능이면 충분합니다."
        return await self.start_collaboration(task, max_turns=4)
    
    async def stream_collaboration(self):
        """실시간 협업 보기"""
        task = input("수행할 작업을 입력하세요: ").strip()
        if not task:
            task = "웹 기반 간단한 메모 앱을 만드는 계획을 세워주세요."
        
        max_turns = input("최대 턴 수 (기본값: 4): ").strip()
        max_turns = int(max_turns) if max_turns.isdigit() else 4
        
        print(f"\n📋 작업: {task}")
        print(f"🔄 최대 {max_turns}턴으로 실시간 협업을 시작합니다...\n")
        
        try:
            # 실시간 스트림으로 협업 진행
            team = self.create_team(max_turns)
            
            print("=" * 60)
            print("🎥 실시간 협업 시작!")
            print("=" * 60)
            
            message_count = 0
            async for item in team.run_stream(task=task):
                # 타입 체크: BaseChatMessage vs TaskResult
                if hasattr(item, 'source'):  # BaseChatMessage
                    message_count += 1
                    agent_name = item.source
                    content = item.content
                    
                    # 에이전트별 이모지
                    emoji_map = {
                        "user": "👤",
                        "Planner": "📋",
                        "Developer": "💻", 
                        "Reviewer": "🔍"
                    }
                    emoji = emoji_map.get(agent_name, "🤖")
                    
                    print(f"\n{emoji} {agent_name} (메시지 {message_count}):")
                    print("-" * 40)
                    print(content)
                    print("\n" + "="*60)
                    
                    # 잠시 대기 (읽기 쉽게)
                    await asyncio.sleep(0.5)
                    
                elif hasattr(item, 'messages'):  # TaskResult (마지막 결과)
                    print(f"\n🏁 협업 완료!")
                    print(f"📊 총 {len(item.messages)}개의 메시지가 교환되었습니다.")
                    print(f"⏹️ 종료 이유: {item.stop_reason}")
                    
                    # 최종 결과 표시
                    if item.messages:
                        final_message = item.messages[-1]
                        print(f"\n🎯 최종 결과:")
                        print(f"작성자: {final_message.source}")
                        print(f"내용: {final_message.content[:200]}...")
                
                else:  # BaseAgentEvent (이벤트)
                    print(f"📡 이벤트: {type(item).__name__}")
            
            print("\n✅ 실시간 협업이 완료되었습니다!")
            
        except Exception as e:
            print(f"❌ 실시간 협업 중 오류: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """리소스 정리"""
        try:
            agents = [self.planner, self.developer, self.reviewer]
            for agent in agents:
                if hasattr(agent, 'model_client'):
                    await agent.model_client.close()
        except Exception as e:
            print(f"⚠️ 정리 중 오류: {e}")

async def main():
    """메인 실행 함수"""
    print("Autogen 0.4 + Gemini 다중 에이전트 시스템")
    print("=" * 50)
    
    try:
        multi_system = MultiAgentSystem()
        
        print("어떤 예제를 실행하시겠습니까?")
        print("1. TODO 앱 개발")
        print("2. 빠른 테스트")
        print("3. 커스텀 작업")
        print("4. 실시간 협업 보기 (스트림)")
        
        choice = input("\n선택 (1-4): ").strip()
        
        if choice == "1":
            print("\n🚀 TODO 앱 개발 협업을 시작합니다...")
            await multi_system.simple_task_example()
        elif choice == "2":
            print("\n🚀 빠른 테스트를 시작합니다...")
            await multi_system.quick_test()
        elif choice == "3":
            custom_task = input("수행할 작업을 입력하세요: ").strip()
            if custom_task:
                max_turns = input("최대 턴 수 (기본값: 6): ").strip()
                max_turns = int(max_turns) if max_turns.isdigit() else 6
                print(f"\n🚀 커스텀 작업 협업을 시작합니다... (최대 {max_turns}턴)")
                await multi_system.start_collaboration(custom_task, max_turns)
            else:
                print("❌ 작업이 입력되지 않았습니다.")
        elif choice == "4":
            print("\n🚀 실시간 협업을 시작합니다...")
            await multi_system.stream_collaboration()
        else:
            print("❌ 잘못된 선택입니다.")
        
    except Exception as e:
        print(f"❌ 시스템 오류: {e}")

if __name__ == "__main__":
    asyncio.run(main())