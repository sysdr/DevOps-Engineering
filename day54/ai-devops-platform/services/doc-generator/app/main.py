from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import ast
import re
from datetime import datetime

app = FastAPI(title="Doc Generator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CodeFile(BaseModel):
    filename: str
    content: str
    language: str = "python"

class Documentation(BaseModel):
    filename: str
    title: str
    description: str
    sections: List[Dict]
    generated_at: str

class DocGenerator:
    def __init__(self):
        pass
    
    def generate_docs(self, code_file: CodeFile) -> Documentation:
        """Generate documentation from code file"""
        if code_file.language.lower() == 'python':
            return self._generate_python_docs(code_file)
        else:
            return self._generate_generic_docs(code_file)
    
    def _generate_python_docs(self, code_file: CodeFile) -> Documentation:
        """Generate documentation for Python code"""
        sections = []
        
        try:
            tree = ast.parse(code_file.content)
            
            # Extract module docstring
            module_doc = ast.get_docstring(tree) or "No description available"
            
            # Extract classes
            classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            if classes:
                class_section = {
                    'title': 'Classes',
                    'items': []
                }
                for cls in classes:
                    class_doc = ast.get_docstring(cls) or "No description"
                    methods = [m.name for m in cls.body if isinstance(m, ast.FunctionDef)]
                    class_section['items'].append({
                        'name': cls.name,
                        'description': class_doc,
                        'methods': methods,
                        'line': cls.lineno
                    })
                sections.append(class_section)
            
            # Extract functions
            functions = [
                node for node in ast.walk(tree)
                if isinstance(node, ast.FunctionDef) and node.col_offset == 0
            ]
            if functions:
                func_section = {
                    'title': 'Functions',
                    'items': []
                }
                for func in functions:
                    func_doc = ast.get_docstring(func) or "No description"
                    
                    # Extract parameters
                    params = []
                    for arg in func.args.args:
                        param_info = {'name': arg.arg}
                        if arg.annotation:
                            param_info['type'] = ast.unparse(arg.annotation)
                        params.append(param_info)
                    
                    # Extract return type
                    return_type = None
                    if func.returns:
                        return_type = ast.unparse(func.returns)
                    
                    func_section['items'].append({
                        'name': func.name,
                        'description': func_doc,
                        'parameters': params,
                        'returns': return_type,
                        'line': func.lineno
                    })
                sections.append(func_section)
            
            # Extract constants/globals
            assignments = [
                node for node in ast.walk(tree)
                if isinstance(node, ast.Assign) and node.col_offset == 0
            ]
            if assignments:
                const_section = {
                    'title': 'Constants',
                    'items': []
                }
                for assign in assignments[:10]:  # Limit to first 10
                    for target in assign.targets:
                        if isinstance(target, ast.Name):
                            value = ast.unparse(assign.value) if len(ast.unparse(assign.value)) < 50 else '...'
                            const_section['items'].append({
                                'name': target.id,
                                'value': value,
                                'line': assign.lineno
                            })
                if const_section['items']:
                    sections.append(const_section)
            
        except SyntaxError as e:
            sections.append({
                'title': 'Error',
                'items': [{'error': f'Syntax error in code: {str(e)}'}]
            })
        
        return Documentation(
            filename=code_file.filename,
            title=self._generate_title(code_file.filename),
            description=module_doc,
            sections=sections,
            generated_at=datetime.utcnow().isoformat()
        )
    
    def _generate_generic_docs(self, code_file: CodeFile) -> Documentation:
        """Generate basic documentation for non-Python code"""
        lines = code_file.content.split('\n')
        
        # Extract comments
        comments = []
        for i, line in enumerate(lines, 1):
            if line.strip().startswith('//') or line.strip().startswith('#'):
                comments.append({'line': i, 'text': line.strip()})
        
        sections = [{
            'title': 'Overview',
            'items': [{
                'lines': len(lines),
                'comments': len(comments)
            }]
        }]
        
        if comments:
            sections.append({
                'title': 'Comments',
                'items': comments[:20]  # Limit to first 20
            })
        
        return Documentation(
            filename=code_file.filename,
            title=self._generate_title(code_file.filename),
            description="Automated documentation generated",
            sections=sections,
            generated_at=datetime.utcnow().isoformat()
        )
    
    def _generate_title(self, filename: str) -> str:
        """Generate human-readable title from filename"""
        name = filename.split('/')[-1].replace('.py', '').replace('_', ' ').replace('-', ' ')
        return name.title()

generator = DocGenerator()

@app.post("/generate", response_model=Documentation)
async def generate_documentation(code_file: CodeFile):
    """Generate documentation from code file"""
    try:
        docs = generator.generate_docs(code_file)
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "doc-generator"}
