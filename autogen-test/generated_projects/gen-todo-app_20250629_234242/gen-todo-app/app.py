import os
import json
import time
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
# Flask flash 메시지를 사용하기 위한 시크릿 키 설정
# 실제 배포 환경에서는 환경 변수 등으로 안전하게 관리해야 합니다.
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your_super_secret_dev_key_change_me_in_prod')

# 데이터 파일 경로 설정
# 앱의 루트 디렉토리에 todos.json 파일을 생성합니다.
TODO_FILE = 'todos.json'

def load_todos():
    """
    todos.json 파일에서 할 일 목록을 로드합니다.
    파일이 없거나 비어있는 경우, 또는 JSON 파싱 오류 시 빈 리스트를 반환합니다.
    """
    if not os.path.exists(TODO_FILE) or os.path.getsize(TODO_FILE) == 0:
        app.logger.info(f"'{TODO_FILE}' not found or empty. Returning empty todo list.")
        return []
    try:
        with open(TODO_FILE, 'r', encoding='utf-8') as f:
            todos = json.load(f)
            # 데이터 무결성을 위해 각 할 일에 'completed' 필드가 있는지 확인
            for todo in todos:
                if 'completed' not in todo:
                    todo['completed'] = False
                if 'id' not in todo: # 모든 todo에 ID가 있는지 확인
                    # TODO: 실제 앱에서는 ID가 없는 경우 복구 로직이 필요할 수 있습니다.
                    # 여기서는 간단히 로그를 남기고 넘어갑니다.
                    app.logger.warning(f"Todo item without 'id' found: {todo}")
            return todos
    except json.JSONDecodeError as e:
        app.logger.error(f"Error decoding JSON from '{TODO_FILE}': {e}. File might be corrupted. Starting with empty list.")
        flash('할 일 데이터를 불러오는 중 오류가 발생했습니다. 파일이 손상되었을 수 있습니다.', 'danger')
        return []
    except Exception as e:
        app.logger.error(f"An unexpected error occurred while loading todos from '{TODO_FILE}': {e}")
        flash('할 일 데이터를 불러오는 중 알 수 없는 오류가 발생했습니다.', 'danger')
        return []

def save_todos(todos):
    """
    할 일 목록을 todos.json 파일에 저장합니다.
    저장 중 발생하는 IOError를 처리합니다.
    """
    try:
        with open(TODO_FILE, 'w', encoding='utf-8') as f:
            json.dump(todos, f, indent=4, ensure_ascii=False)
        app.logger.info(f"Todos successfully saved to '{TODO_FILE}'.")
    except IOError as e:
        app.logger.error(f"IOError occurred while saving todos to '{TODO_FILE}': {e}")
        flash(f'할 일을 저장하는 데 실패했습니다: {e}', 'danger')
    except Exception as e:
        app.logger.error(f"An unexpected error occurred while saving todos to '{TODO_FILE}': {e}")
        flash('알 수 없는 오류가 발생하여 할 일을 저장할 수 없습니다.', 'danger')

@app.route('/')
def index():
    """
    메인 페이지를 렌더링하고 현재 할 일 목록과 통계를 표시합니다.
    """
    todos = load_todos()
    total_todos = len(todos)
    # .get('completed', False)를 사용하여 completed 필드가 없을 경우 기본값 처리
    completed_todos = sum(1 for todo in todos if todo.get('completed', False)) 

    app.logger.info(f"Rendering index page. Total todos: {total_todos}, Completed: {completed_todos}")
    return render_template('index.html', 
                           todos=todos, 
                           total_todos=total_todos, 
                           completed_todos=completed_todos)

@app.route('/add', methods=['POST'])
def add_todo():
    """
    새로운 할 일을 추가합니다.
    POST 요청으로 'title' 폼 데이터를 받습니다.
    """
    title = request.form.get('title')
    if not title or title.strip() == '':
        flash('할 일 내용을 입력해주세요!', 'warning')
        app.logger.warning("Attempted to add an empty todo title.")
        return redirect(url_for('index'))
    
    title = title.strip() # 공백 제거

    todos = load_todos()
    
    # 타임스탬프 기반의 고유 ID 생성 (밀리초 단위)
    # 실제로는 더 견고한 UUID 등을 사용하는 것이 좋습니다.
    new_id = int(time.time() * 1000) 
    
    # 혹시 모를 ID 중복 방지 (동일 밀리초에 여러 요청이 오는 경우)
    # 매우 드물지만, 안전을 위해 기존 ID와 겹치지 않도록 조정합니다.
    while any(todo['id'] == new_id for todo in todos):
        new_id += 1 

    new_todo = {
        'id': new_id,
        'title': title,
        'completed': False
    }
    todos.append(new_todo)
    save_todos(todos)
    flash('할 일이 성공적으로 추가되었습니다!', 'success')
    app.logger.info(f"Added new todo: {new_todo['title']}")
    return redirect(url_for('index'))

@app.route('/complete/<int:todo_id>', methods=['POST'])
def complete_todo(todo_id):
    """
    특정 할 일의 완료 상태를 토글합니다.
    URL 경로를 통해 할 일 ID를 받습니다.
    """
    todos = load_todos()
    found = False
    for todo in todos:
        if todo['id'] == todo_id:
            # 현재 상태의 반대로 토글 (completed 필드가 없으면 False로 간주)
            todo['completed'] = not todo.get('completed', False) 
            found = True
            break
    
    if found:
        save_todos(todos)
        flash('할 일 상태가 업데이트되었습니다!', 'info')
        app.logger.info(f"Toggled completion for todo ID: {todo_id}")
    else:
        flash('해당 할 일을 찾을 수 없습니다.', 'danger')
        app.logger.warning(f"Attempted to toggle completion for non-existent todo ID: {todo_id}")
    return redirect(url_for('index'))

@app.route('/delete/<int:todo_id>', methods=['POST'])
def delete_todo(todo_id):
    """
    특정 할 일을 삭제합니다.
    URL 경로를 통해 할 일 ID를 받습니다.
    """
    todos = load_todos()
    initial_len = len(todos)
    # 리스트 컴프리헨션을 사용하여 해당 ID의 할 일을 제외한 새 리스트 생성
    todos = [todo for todo in todos if todo['id'] != todo_id]
    
    if len(todos) < initial_len:
        save_todos(todos)
        flash('할 일이 성공적으로 삭제되었습니다!', 'success')
        app.logger.info(f"Deleted todo ID: {todo_id}")
    else:
        flash('삭제할 할 일을 찾을 수 없습니다.', 'danger')
        app.logger.warning(f"Attempted to delete non-existent todo ID: {todo_id}")
    return redirect(url_for('index'))

if __name__ == '__main__':
    # 앱 시작 시 todos.json 파일이 없거나 비어있으면 빈 JSON 배열로 초기화
    # 이렇게 하면 첫 실행 시 파일이 자동으로 생성되어 오류를 방지합니다.
    if not os.path.exists(TODO_FILE) or os.path.getsize(TODO_FILE) == 0:
        try:
            with open(TODO_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f)
            print(f"Initialized empty '{TODO_FILE}' as it was missing or empty.")
        except IOError as e:
            print(f"ERROR: Could not initialize '{TODO_FILE}': {e}")
            # 이 경우, 앱이 계속 실행되지만, 할 일 저장/로드에 문제가 있을 수 있습니다.
        except Exception as e:
            print(f"ERROR: An unexpected error occurred during '{TODO_FILE}' initialization: {e}")

    # Flask 애플리케이션 실행
    # debug=True는 개발 중 자동 리로드와 디버그 정보를 제공합니다.
    # 운영 환경에서는 debug=False로 설정해야 합니다.
    app.run(debug=True)