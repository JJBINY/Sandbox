import ast
import os
from pathlib import Path
from typing import Dict, List, Set
import networkx as nx

class ProjectAnalyzer:
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.dependency_graph = nx.DiGraph()
        self.modules = {}
        self.test_coverage = {}
        
    async def analyze_project(self) -> Dict:
        """전체 프로젝트 분석"""
        analysis = {
            'structure': await self.analyze_structure(),
            'dependencies': await self.analyze_dependencies(),
            'quality_metrics': await self.analyze_quality(),
            'test_coverage': await self.analyze_test_coverage(),
            'refactoring_opportunities': await self.identify_refactoring_opportunities()
        }
        
        return analysis
        
    async def analyze_structure(self) -> Dict:
        """프로젝트 구조 분석"""
        structure = {
            'modules': {},
            'packages': [],
            'entry_points': [],
            'configuration_files': []
        }
        
        for py_file in self.project_path.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue
                
            module_info = await self.analyze_module(py_file)
            structure['modules'][str(py_file)] = module_info
            
        return structure
        
    async def analyze_module(self, file_path: Path) -> Dict:
        """개별 모듈 분석"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return {'error': f'Syntax error: {e}'}
            
        analyzer = ModuleAnalyzer()
        analyzer.visit(tree)
        
        return {
            'functions': analyzer.functions,
            'classes': analyzer.classes,
            'imports': analyzer.imports,
            'complexity': analyzer.complexity,
            'lines_of_code': len(content.splitlines())
        }
        
    async def identify_refactoring_opportunities(self) -> List[Dict]:
        """리팩토링 기회 식별"""
        opportunities = []
        
        # 코드 중복 감지
        duplicates = await self.detect_code_duplication()
        opportunities.extend(duplicates)
        
        # 긴 함수 감지
        long_functions = await self.detect_long_functions()
        opportunities.extend(long_functions)
        
        # 순환 의존성 감지
        circular_deps = await self.detect_circular_dependencies()
        opportunities.extend(circular_deps)
        
        # 코드 스멜 감지
        code_smells = await self.detect_code_smells()
        opportunities.extend(code_smells)
        
        return opportunities

class ModuleAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.functions = []
        self.classes = []
        self.imports = []
        self.complexity = 0
        
    def visit_FunctionDef(self, node):
        self.functions.append({
            'name': node.name,
            'line_start': node.lineno,
            'line_end': node.end_lineno,
            'complexity': self.calculate_cyclomatic_complexity(node),
            'parameters': len(node.args.args),
            'decorators': [ast.unparse(d) for d in node.decorator_list]
        })
        self.generic_visit(node)
        
    def visit_ClassDef(self, node):
        self.classes.append({
            'name': node.name,
            'line_start': node.lineno,
            'line_end': node.end_lineno,
            'methods': len([n for n in node.body if isinstance(n, ast.FunctionDef)]),
            'base_classes': [ast.unparse(base) for base in node.bases]
        })
        self.generic_visit(node)
        
    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append({
                'module': alias.name,
                'alias': alias.asname,
                'type': 'import'
            })
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node):
        for alias in node.names:
            self.imports.append({
                'module': node.module,
                'name': alias.name,
                'alias': alias.asname,
                'type': 'from_import'
            })
        self.generic_visit(node)