import ast

def parse_code(user_code):
    try:
        tree = ast.parse(user_code)
        return tree
    except SyntaxError as e:
        return f"Syntax Error: {e}"


def format_code(user_code):
    tree = ast.parse(user_code)
    return ast.unparse(tree)


def show_ast_structure(user_code):
    tree = ast.parse(user_code)
    return ast.dump(tree)
