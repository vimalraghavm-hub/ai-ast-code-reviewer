"""
multi_language_detector.py - Lightweight syntax validation and heuristic scoring for JS, TS, Java, and C++.
Complements the AI's semantic analysis with deterministic logic.
"""
import re

def get_js_ts_score(code: str) -> int:
    """Basic heuristic for JS/TS code quality."""
    score = 100
    # Check for excessive use of 'var' instead of 'const/let'
    if re.search(r'\bvar\b', code):
        score -= 10
    # Check for console logs in production-like environments
    if re.search(r'console\.log', code):
        score -= 5
    # Check for empty catch blocks
    if re.search(r'catch\s*\(\s*\w+\s*\)\s*{\s*}', code):
        score -= 15
    return max(0, score)

def get_java_score(code: str) -> int:
    """Basic heuristic for Java code quality."""
    score = 100
    # Check for missing main or class structure
    if not re.search(r'public\s+class', code):
        score -= 20
    # Check for System.out.println
    if re.search(r'System\.out\.println', code):
        score -= 5
    # Check for raw types in collections
    if re.search(r'List\s+\w+\s*=\s*new\s+ArrayList', code) and not re.search(r'List<', code):
        score -= 10
    return max(0, score)

def get_cpp_score(code: str) -> int:
    """Basic heuristic for C/C++ code quality."""
    score = 100
    # Check for unsafe functions
    if re.search(r'\bgets\(', code) or re.search(r'\bstrcpy\(', code):
        score -= 20
    # Check for goto usage
    if re.search(r'\bgoto\b', code):
        score -= 15
    # Check for missing return in main (vague check)
    if re.search(r'int\s+main', code) and not re.search(r'return\s+0', code):
        score -= 5
    return max(0, score)

def get_language_score(code: str, language: str) -> int:
    """Dispatcher for multi-language deterministic scoring."""
    lang = language.lower()
    if lang in ["javascript", "typescript", "js", "ts"]:
        return get_js_ts_score(code)
    elif lang == "java":
        return get_java_score(code)
    elif lang in ["c", "cpp", "c++"]:
        return get_cpp_score(code)
    return 0
