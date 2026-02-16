from parser import parse_code, format_code, show_ast_structure

print("Enter Python code (Press Enter twice to finish):")

lines = []
while True:
    line = input()
    if line == "":
        break
    lines.append(line)

user_code = "\n".join(lines)

parsed = parse_code(user_code)

if isinstance(parsed, str):
    print(parsed)
else:
    print("\nAST Structure:\n")
    print(show_ast_structure(user_code))

    print("\nFormatted Code:\n")
    print(format_code(user_code))
