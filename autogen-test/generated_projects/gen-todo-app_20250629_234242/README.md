# gen-todo-app

Autogen 다중 에이전트 시스템으로 생성된 Python 프로젝트입니다.

## 🚀 빠른 시작

### 1. 가상환경 생성 (권장)

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### 2. 의존성 설치

```bash
# ⚠️ 중요: 이 명령어를 사용하세요!
pip install -r requirements.txt

# ❌ 틀린 명령어: python requirements.txt (이건 안됩니다!)
```

### 3. 프로젝트 실행

```bash
python main.py
```

## 📁 프로젝트 구조

```
gen-todo-app/
├── main.py              # 메인 실행 파일
├── requirements.txt     # 의존성 목록  
├── README.md           # 프로젝트 문서 (이 파일)
├── .env.example        # 환경 변수 예제
├── config/             # 설정 파일들
├── modules/            # 추가 모듈들
│   └── __init__.py
└── tests/              # 테스트 파일들
    └── test_main.py
```

## 🔧 개발 가이드

### 환경 설정
1. `.env.example`을 `.env`로 복사하고 필요한 값들을 설정하세요
2. 새로운 패키지가 필요하면 `requirements.txt`에 추가하세요

### 새로운 기능 추가
1. `modules/` 디렉토리에 새 모듈 생성
2. `main.py`에서 모듈 import
3. 테스트 파일 작성

### 테스트 실행
```bash
# 단일 테스트 파일 실행
python -m pytest tests/test_main.py

# 모든 테스트 실행
python -m pytest tests/

# 또는 간단하게
python tests/test_main.py
```

## 🐛 문제 해결

### 일반적인 오류들

1. **ModuleNotFoundError**: 
   ```bash
   pip install -r requirements.txt
   ```

2. **가상환경 활성화 안됨**:
   - Linux/Mac: `source venv/bin/activate`
   - Windows: `venv\Scripts\activate`

3. **권한 오류** (Mac/Linux):
   ```bash
   chmod +x main.py
   python main.py
   ```

4. **Python 버전 호환성**:
   - 이 프로젝트는 Python 3.8+ 에서 테스트되었습니다
   - `python --version`으로 버전 확인

### 디버그 모드
```bash
python main.py --debug
```

## 📝 생성 정보

- **생성 시간**: 2025-06-29 23:45:01
- **생성 도구**: Autogen + Gemini API (코드 실행 테스트 포함)
- **Python 버전**: 3.8+
- **테스트 상태**: ✅ 코드 실행 테스트 통과

## 🤝 기여

이 프로젝트를 개선하고 싶으시다면:
1. Fork 후 수정
2. 테스트 추가 (`tests/` 디렉토리)
3. Pull Request 생성

## 📄 라이선스

MIT License - 자유롭게 사용하세요!

---

**💡 도움말**: 문제가 있으면 README.md의 문제 해결 섹션을 확인하거나 이슈를 등록하세요.
