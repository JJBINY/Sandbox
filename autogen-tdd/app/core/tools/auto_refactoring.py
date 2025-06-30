import rope.base.project
from rope.refactor.rename import Rename
from rope.refactor.extract import ExtractMethod, ExtractVariable
from rope.refactor.move import MoveModule

class AutoRefactoring:
    def __init__(self, project_path: str):
        self.project = rope.base.project.Project(project_path)
        self.file_modifier = SafeFileModifier(project_path)
        
    async def execute_refactoring_plan(self, opportunities: List[Dict]):
        """리팩토링 계획 실행"""
        results = []
        
        for opportunity in opportunities:
            try:
                result = await self.execute_single_refactoring(opportunity)
                results.append(result)
            except Exception as e:
                results.append({
                    'opportunity': opportunity,
                    'status': 'failed',
                    'error': str(e)
                })
                
        return results
        
    async def execute_single_refactoring(self, opportunity: Dict):
        """단일 리팩토링 실행"""
        refactoring_type = opportunity['type']
        
        if refactoring_type == 'extract_method':
            return await self.extract_method(opportunity)
        elif refactoring_type == 'rename':
            return await self.rename_symbol(opportunity)
        elif refactoring_type == 'move_module':
            return await self.move_module(opportunity)
        elif refactoring_type == 'remove_duplication':
            return await self.remove_code_duplication(opportunity)
            
    async def extract_method(self, opportunity: Dict):
        """메서드 추출 리팩토링"""
        file_path = opportunity['file_path']
        start_line = opportunity['start_line']
        end_line = opportunity['end_line']
        method_name = opportunity['suggested_name']
        
        resource = self.project.get_resource(file_path)
        
        # 라인 번호를 오프셋으로 변환
        start_offset = resource.read().find('\n' * (start_line - 1))
        end_offset = resource.read().find('\n' * end_line)
        
        extract_method = ExtractMethod(
            self.project, resource, start_offset, end_offset
        )
        
        changes = extract_method.get_changes(method_name)
        self.project.do(changes)
        
        return {
            'type': 'extract_method',
            'status': 'success',
            'file': file_path,
            'method': method_name
        }