import ast
import networkx as nx
from typing import Dict, Any, List, Optional

class CFGGenerator(ast.NodeVisitor):
    def __init__(self):
        self.graph = nx.DiGraph()
        self.current_node_id = 0
        self.last_node_id = None
        self.pending_statements = []
        self.start_lineno = 0
    
    def _flush_statements(self):
        if not self.pending_statements:
            return
        
        label = "\n".join(self.pending_statements)
        node_id = self.current_node_id
        self.current_node_id += 1
        self.graph.add_node(node_id, label=label, type="statement", lineno=self.start_lineno)
        
        if self.last_node_id is not None:
            self.graph.add_edge(self.last_node_id, node_id)
        
        self.last_node_id = node_id
        self.pending_statements = []

    def _add_special_node(self, label: str, node_type: str = "statement", lineno: int = 0) -> int:
        self._flush_statements()
        node_id = self.current_node_id
        self.current_node_id += 1
        self.graph.add_node(node_id, label=label, type=node_type, lineno=lineno)
        
        if self.last_node_id is not None:
            self.graph.add_edge(self.last_node_id, node_id)
        
        self.last_node_id = node_id
        return node_id

    def build(self, source_code: str) -> Dict[str, Any]:
        self.graph.clear()
        self.current_node_id = 0
        self.last_node_id = None
        self.pending_statements = []
        
        try:
            tree = ast.parse(source_code)
            self.visit(tree)
            self._flush_statements()
            
            nodes = []
            for n in self.graph.nodes:
                node_data = self.graph.nodes[n]
                nodes.append({
                    "id": n,
                    "label": node_data.get("label"),
                    "type": node_data.get("type"),
                    "lineno": node_data.get("lineno", 0)
                })
            
            edges = [{"source": u, "target": v, "label": self.graph.edges[u,v].get("label", "")} 
                     for u, v in self.graph.edges]
            
            return {"nodes": nodes, "edges": edges}
        except Exception as e:
            return {"error": str(e)}

    def generic_visit(self, node):
        if isinstance(node, (ast.Assign, ast.Expr, ast.Import, ast.ImportFrom, ast.Pass)):
            if not self.pending_statements:
                self.start_lineno = node.lineno
            label = ast.unparse(node)[:40] if hasattr(ast, "unparse") else type(node).__name__
            self.pending_statements.append(f"L{node.lineno}: {label}")
        elif isinstance(node, (ast.Return, ast.Break, ast.Continue)):
            label = ast.unparse(node)[:40] if hasattr(ast, "unparse") else type(node).__name__
            self._add_special_node(f"L{node.lineno}: {label}", "return", node.lineno)
        else:
            super().generic_visit(node)

    def visit_FunctionDef(self, node):
        self._add_special_node(f"L{node.lineno}: def {node.name}(...)", "function_def", node.lineno)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self._add_special_node(f"L{node.lineno}: async def {node.name}(...)", "function_def", node.lineno)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self._add_special_node(f"L{node.lineno}: class {node.name}", "class_def", node.lineno)
        self.generic_visit(node)

    def visit_If(self, node):
        self._flush_statements()
        cond_str = ast.unparse(node.test)[:40] if hasattr(ast, "unparse") else "condition"
        cond_node = self._add_special_node(f"L{node.lineno}: if {cond_str}", "condition", node.lineno)
        
        entry_id = cond_node
        # True Branch
        self.last_node_id = entry_id
        for child in node.body: self.visit(child)
        self._flush_statements()
        last_body_node = self.last_node_id
            
        # False Branch
        if node.orelse:
            self.last_node_id = entry_id
            for child in node.orelse: self.visit(child)
            self._flush_statements()
            last_else_node = self.last_node_id
            self.last_node_id = last_body_node # Continue from both ideally, but keep linear for simplicity
        else:
            self.last_node_id = last_body_node

    def visit_While(self, node):
        self._flush_statements()
        cond_str = ast.unparse(node.test)[:40] if hasattr(ast, "unparse") else "cond"
        loop_guard = self._add_special_node(f"L{node.lineno}: while {cond_str}", "loop_guard", node.lineno)
        self.last_node_id = loop_guard
        for child in node.body: self.visit(child)
        self._flush_statements()
        if self.last_node_id is not None:
             self.graph.add_edge(self.last_node_id, loop_guard, label="loop")
        self.last_node_id = loop_guard

    def visit_For(self, node):
        self._flush_statements()
        target = ast.unparse(node.target) if hasattr(ast, "unparse") else "var"
        loop_guard = self._add_special_node(f"L{node.lineno}: for {target} in ...", "loop_guard", node.lineno)
        self.last_node_id = loop_guard
        for child in node.body: self.visit(child)
        self._flush_statements()
        if self.last_node_id is not None:
            self.graph.add_edge(self.last_node_id, loop_guard, label="loop")
        self.last_node_id = loop_guard

    def visit_Try(self, node):
        nid = self._add_node(f"L{node.lineno}: try", "statement", node.lineno)
        self.last_node_id = nid
        for child in node.body:
            self.visit(child)
        
        last_try_node = self.last_node_id
        for handler in node.handlers:
            self.last_node_id = nid
            ename = ast.unparse(handler.type) if handler.type and hasattr(ast, "unparse") else "Exception"
            eid = self._add_node(f"L{handler.lineno}: except {ename}", "condition", handler.lineno)
            for child in handler.body:
                self.visit(child)
        
        self.last_node_id = last_try_node

def generate_cfg(code: str) -> dict:
    """Entry point for creating the CFG dict."""
    try:
        gen = CFGGenerator()
        return gen.build(code)
    except SyntaxError as e:
        return {"error": f"Syntax error at line {e.lineno}: {e.msg}"}
    except Exception as e:
        return {"error": str(e)}
