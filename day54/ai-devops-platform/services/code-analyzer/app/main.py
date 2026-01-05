from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import ast
import re
import numpy as np
from datetime import datetime
import hashlib

app = FastAPI(title="AI Code Analyzer", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CodeAnalysisRequest(BaseModel):
    code: str
    language: str = "python"
    filename: str = "unknown.py"

class Issue(BaseModel):
    type: str
    severity: str
    line: int
    message: str
    suggestion: str
    confidence: float

class AnalysisResult(BaseModel):
    filename: str
    issues: List[Issue]
    metrics: Dict[str, float]
    score: float
    timestamp: str

class CodeAnalyzer:
    def __init__(self):
        self.security_patterns = {
            r'eval\(': ('CRITICAL', 'Use of eval() is dangerous', 'Use ast.literal_eval() or safer alternatives'),
            r'exec\(': ('CRITICAL', 'Use of exec() is dangerous', 'Refactor to avoid dynamic code execution'),
            r'__import__': ('HIGH', 'Dynamic imports can be risky', 'Use standard import statements'),
            r'pickle\.loads': ('HIGH', 'Pickle deserialization is unsafe', 'Use JSON or safer serialization'),
            r'subprocess\.(call|run|Popen)': ('MEDIUM', 'Subprocess execution needs validation', 'Validate and sanitize all inputs'),
            r'(SELECT|UPDATE|DELETE|INSERT).*%s': ('HIGH', 'Potential SQL injection', 'Use parameterized queries'),
            r'password\s*=\s*["\'][^"\']+["\']': ('CRITICAL', 'Hardcoded password detected', 'Use environment variables or secrets management'),
            r'api[_-]?key\s*=\s*["\'][^"\']+["\']': ('CRITICAL', 'Hardcoded API key detected', 'Use environment variables'),
        }
        
    def analyze_code(self, code: str, filename: str) -> AnalysisResult:
        issues = []
        
        # Security analysis
        issues.extend(self._security_scan(code))
        
        # Complexity analysis
        complexity_issues = self._complexity_analysis(code)
        issues.extend(complexity_issues)
        
        # Code quality checks
        issues.extend(self._quality_checks(code))
        
        # Calculate metrics
        metrics = self._calculate_metrics(code)
        
        # Calculate overall score
        score = self._calculate_score(issues, metrics)
        
        return AnalysisResult(
            filename=filename,
            issues=issues,
            metrics=metrics,
            score=score,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def _security_scan(self, code: str) -> List[Issue]:
        issues = []
        lines = code.split('\n')
        
        for pattern, (severity, message, suggestion) in self.security_patterns.items():
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    confidence = 0.85 if severity == 'CRITICAL' else 0.75
                    issues.append(Issue(
                        type='security',
                        severity=severity,
                        line=i,
                        message=message,
                        suggestion=suggestion,
                        confidence=confidence
                    ))
        
        return issues
    
    def _complexity_analysis(self, code: str) -> List[Issue]:
        issues = []
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    complexity = self._calculate_cyclomatic_complexity(node)
                    if complexity > 10:
                        issues.append(Issue(
                            type='complexity',
                            severity='MEDIUM' if complexity < 15 else 'HIGH',
                            line=node.lineno,
                            message=f'Function "{node.name}" has high cyclomatic complexity: {complexity}',
                            suggestion='Consider breaking down into smaller functions',
                            confidence=0.90
                        ))
                    
                    # Check for too many parameters
                    param_count = len(node.args.args)
                    if param_count > 5:
                        issues.append(Issue(
                            type='complexity',
                            severity='LOW',
                            line=node.lineno,
                            message=f'Function "{node.name}" has {param_count} parameters',
                            suggestion='Consider using a configuration object or builder pattern',
                            confidence=0.80
                        ))
        except SyntaxError:
            pass
        
        return issues
    
    def _quality_checks(self, code: str) -> List[Issue]:
        issues = []
        lines = code.split('\n')
        
        # Check for long lines
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                issues.append(Issue(
                    type='style',
                    severity='LOW',
                    line=i,
                    message=f'Line length exceeds 120 characters ({len(line)} chars)',
                    suggestion='Break line into multiple lines',
                    confidence=0.95
                ))
        
        # Check for TODO/FIXME comments
        for i, line in enumerate(lines, 1):
            if re.search(r'#\s*(TODO|FIXME|HACK)', line, re.IGNORECASE):
                issues.append(Issue(
                    type='maintenance',
                    severity='LOW',
                    line=i,
                    message='Technical debt marker found',
                    suggestion='Create a ticket to address this issue',
                    confidence=1.0
                ))
        
        return issues
    
    def _calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _calculate_metrics(self, code: str) -> Dict[str, float]:
        lines = code.split('\n')
        total_lines = len(lines)
        code_lines = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
        comment_lines = len([l for l in lines if l.strip().startswith('#')])
        
        try:
            tree = ast.parse(code)
            functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        except:
            functions = []
            classes = []
        
        return {
            'total_lines': float(total_lines),
            'code_lines': float(code_lines),
            'comment_lines': float(comment_lines),
            'comment_ratio': float(comment_lines / max(code_lines, 1)),
            'function_count': float(len(functions)),
            'class_count': float(len(classes))
        }
    
    def _calculate_score(self, issues: List[Issue], metrics: Dict[str, float]) -> float:
        # Start with perfect score
        score = 100.0
        
        # Deduct points based on severity
        severity_weights = {
            'CRITICAL': 15,
            'HIGH': 10,
            'MEDIUM': 5,
            'LOW': 2
        }
        
        for issue in issues:
            score -= severity_weights.get(issue.severity, 1)
        
        # Bonus for good comment ratio
        if metrics['comment_ratio'] > 0.2:
            score += 5
        
        return max(0.0, min(100.0, score))

analyzer = CodeAnalyzer()

@app.post("/analyze", response_model=AnalysisResult)
async def analyze_code(request: CodeAnalysisRequest):
    """Analyze code for security issues, complexity, and quality"""
    try:
        result = analyzer.analyze_code(request.code, request.filename)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "code-analyzer"}
