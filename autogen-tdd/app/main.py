"""
TDD 바이브코딩 시스템 메인 실행 파일
"""
import asyncio
import sys
from pathlib import Path


def setup_project_path():
    """프로젝트 루트 경로를 sys.path에 추가"""
    current_file = Path(__file__).resolve()

    # app/main.py -> app -> ${root}
    project_root = current_file.parent.parent 

    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        print(f"✅ 프로젝트 루트 추가: {project_root}")

    # 확인: app 디렉토리가 존재하는지 체크
    app_dir = project_root / "app"
    if not app_dir.exists():
        raise FileNotFoundError(f"app 디렉토리를 찾을 수 없습니다: {app_dir}")

    return project_root

# 가장 먼저 경로 설정
setup_project_path()

from app.core.tdd_system import TDDVibecodingSystem
from app.example.tdd_examples import TDDExamples
from config.settings import AppConfig


async def main():
    """메인 실행 함수"""
    print("🎯 TDD 바이브코딩 시스템")
    print("=" * 60)

    try:
        # 설정 검증
        AppConfig.validate_config()

        # 예제 요구사항 선택
        examples = TDDExamples.get_example_requirements()

        print("TDD로 구현할 프로젝트를 선택하세요:")
        for key, req in examples.items():
            print(f"{key}. {req['title']}")

        choice = input("\n선택 (1-5): ").strip()

        if choice in examples:
            if choice == "5":
                # 커스텀 요구사항
                requirement = input("\n구현하고 싶은 기능을 상세히 설명해주세요: ").strip()
                if not requirement:
                    print("❌ 요구사항이 입력되지 않았습니다.")
                    return
            else:
                requirement = examples[choice]["description"]
                print(f"\n선택된 프로젝트: {examples[choice]['title']}")
                print(f"요구사항: {requirement}")

                confirm = input("\n이 요구사항으로 TDD를 진행하시겠습니까? (y/n): ").strip().lower()
                if confirm not in ['y', 'yes', '예']:
                    print("❌ 취소되었습니다.")
                    return
        else:
            print("❌ 잘못된 선택입니다.")
            return

        # 프로젝트 이름 입력
        project_name = input("프로젝트 이름을 입력하세요 (기본값: tdd_project): ").strip() or "tdd_project"

        # 최대 반복 수 설정
        max_iterations = input("\n최대 TDD 반복 수를 입력하세요 (기본값: 3): ").strip()
        max_iterations = int(max_iterations) if max_iterations.isdigit() else 3

        print(f"\n🚀 최대 {max_iterations}회 TDD 반복을 시작합니다...")
        print("Red (테스트 작성) → Green (코드 구현) → Refactor (리팩토링)")

        # TDD 시스템 초기화 및 실행
        tdd_system = TDDVibecodingSystem()

        # TDD 프로세스 실행
        results = await tdd_system.start_tdd_process(requirement, project_name, max_iterations)

        if results:
            print("\n🎉 TDD 바이브코딩이 성공적으로 완료되었습니다!")
            print("💡 생성된 프로젝트 디렉토리에서 코드를 확인해보세요.")
        else:
            print("\n❌ TDD 프로세스 중 문제가 발생했습니다.")

    except Exception as e:
        print(f"❌ 시스템 오류: {e}")
        print("💡 .env 파일의 API 키 설정과 pytest 설치를 확인해주세요.")


if __name__ == "__main__":
    asyncio.run(main())