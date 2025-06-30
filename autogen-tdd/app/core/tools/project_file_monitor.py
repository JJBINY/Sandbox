import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import tree_sitter_python as tspython
from tree_sitter import Language, Parser
from app.core.tools.project_file_handler import ProejctFileHandler

class ProjectFileMonitor:
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.observer = Observer()
        self.parser = Parser()
        self.language = Language(tspython.language())
        self.parser.language = self.language
        
        self.file_cache = {}
        self.analysis_cache = {}
        
    def start_monitoring(self):
        """프로젝트 파일 변경 모니터링 시작"""
        handler = ProjectFileHandler(self.on_file_changed)
        self.observer.schedule(handler, self.project_path, recursive=True)
        self.observer.start()
        
    async def on_file_changed(self, file_path: str, event_type: str):
        """파일 변경 시 실시간 분석"""
        if not file_path.endswith(('.py', '.js', '.ts')):
            return
            
        # 파일 내용 분석
        analysis = await self.analyze_file(file_path)
        
        # 에이전트에게 변경 사항 알림
        await self.notify_agents(file_path, event_type, analysis)
        
    async def analyze_file(self, file_path: str):
        """파일 구조 및 의존성 분석"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Tree-sitter로 파싱
        tree = self.parser.parse(bytes(content, "utf8"))
        
        analysis = {
            'functions': self.extract_functions(tree),
            'classes': self.extract_classes(tree),
            'imports': self.extract_imports(tree),
            'complexity': self.calculate_complexity(tree)
        }
        
        self.analysis_cache[file_path] = analysis
        return analysis
        
    def extract_functions(self, tree):
        """함수 정의 추출"""
        functions = []
        
        def traverse(node):
            if node.type == 'function_definition':
                name_node = node.child_by_field_name('name')
                if name_node:
                    functions.append({
                        'name': name_node.text.decode('utf8'),
                        'start_line': node.start_point[0],
                        'end_line': node.end_point[0],
                        'parameters': self.extract_parameters(node)
                    })
            
            for child in node.children:
                traverse(child)
                
        traverse(tree.root_node)
        return functions