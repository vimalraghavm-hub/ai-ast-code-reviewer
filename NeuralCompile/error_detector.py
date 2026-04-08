import ast
import re
import textwrap
import json
import os

class CodeScorer(ast.NodeVisitor):
    """
    Advanced AST-based Python Code Quality Analyzer.
    Evaluates naming, structure, usage, cleanliness, and formatting.
    """
    def __init__(self, original_code):
        self.original_code = textwrap.dedent(original_code).strip()
        self.defined_imports = {}
        self.defined_classes = set()
        self.defined_functions = set()
        self.defined_vars = set()
        self.used_names = set() 
        self.naming_violations = [] 
        self.infinite_loops = []
        self.params = set()
        self.total_functions = 0
        self.snake_case_funcs = 0
        self.total_classes = 0
        self.pascal_case_classes = 0
        self.functions_short_args = True 
        self.functions_short_lines = 0

    def visit_Import(self, node):
        for alias in node.names:
            self.defined_imports[alias.asname or alias.name] = node.lineno
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            self.defined_imports[alias.asname or alias.name] = node.lineno
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.total_classes += 1
        self.defined_classes.add(node.name)
        if re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name): 
            self.pascal_case_classes += 1
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.total_functions += 1
        if not node.name.startswith('__'): 
            self.defined_functions.add(node.name)
        for arg in node.args.args:
            p_name = arg.arg
            if p_name != 'self':
                self.params.add(p_name)
                if len(p_name) < 4 and p_name not in ['i', 'j', 'k', '_']:
                    self.naming_violations.append(f"Argument '{p_name}' at line {node.lineno} is too short.")
        if re.match(r'^[a-z_][a-z0-9_]*$', node.name): 
            self.snake_case_funcs += 1
        start, end = node.lineno, getattr(node, 'end_lineno', node.lineno)
        if (end - start) <= 40: self.functions_short_lines += 1
        if len(node.args.args) > 5: self.functions_short_args = False
        self.generic_visit(node)

    def visit_While(self, node):
        if isinstance(node.test, ast.Constant) and bool(node.test.value) is True:
            if not any(isinstance(child, ast.Break) for child in ast.walk(node)):
                self.infinite_loops.append(node.lineno)
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, (ast.Store, ast.Load)):
            self.used_names.add(node.id)
            if isinstance(node.ctx, ast.Store):
                if node.id not in self.defined_classes and node.id not in self.defined_functions:
                    self.defined_vars.add(node.id)
                if len(node.id) < 4 and node.id not in ['i', 'j', 'k', '_'] and node.id not in self.params:
                    self.naming_violations.append(f"Variable '{node.id}' at line {node.lineno} is too short.")
        self.generic_visit(node)

    def calculate_final_score(self):
        category_scores = {"Naming": 0, "Structure": 0, "Logic": 0, "Cleanliness": 0, "Quality": 0}
        f_pts = (self.snake_case_funcs / self.total_functions * 10) if self.total_functions > 0 else 10
        c_pts = (self.pascal_case_classes / self.total_classes * 10) if self.total_classes > 0 else 10
        category_scores["Naming"] = round(f_pts + c_pts)
        s_pts = 10 if self.functions_short_args else 0
        l_pts = (self.functions_short_lines / self.total_functions * 10) if self.total_functions > 0 else 10
        category_scores["Structure"] = round(s_pts + l_pts)
        u_classes = self.defined_classes - self.used_names
        u_funcs = self.defined_functions - self.used_names
        l_pts = 20 - (10 if u_classes else 0) - (10 if u_funcs else 0)
        category_scores["Logic"] = max(0, l_pts)
        u_imports = set(self.defined_imports.keys()) - self.used_names
        u_vars = (self.defined_vars | self.params) - self.used_names
        cln_pts = 20 - (10 if u_imports else 0) - (10 if u_vars else 0)
        category_scores["Cleanliness"] = max(0, cln_pts)
        quality_pts = (10 if not self.naming_violations else 0) + 10
        if self.infinite_loops: quality_pts = 0 
        category_scores["Quality"] = max(0, quality_pts)
        final_score = sum(category_scores.values())
        return final_score, category_scores, {"Gained": [], "Lost": self.naming_violations}

def get_python_score(code: str) -> int:
    try:
        tree = ast.parse(code)
        scorer = CodeScorer(code)
        scorer.visit(tree)
        score, _, _ = scorer.calculate_final_score()
        return score
    except:
        return 0
