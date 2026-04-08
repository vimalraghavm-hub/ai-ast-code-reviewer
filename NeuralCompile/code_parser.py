import ast
import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Groq client using the API key from environment variables
groq_api_key = os.getenv("GROQ_API_KEY")

model = ChatGroq(model = "llama-3.1-8b-instant",  groq_api_key=groq_api_key)

def parse_student_code(student_code):
    """
    Parses the student's Python code using AST to find unused imports and variables,
    and then generates an AI-driven review using Groq API.
    """
    
    try:
        # Generate the Abstract Syntax Tree (AST) for the provided code
        tree = ast.parse(student_code)
        results = {
        "unused_imports": [],
        "unused_variables": [],
        "ai_review": "",
        "success": True,  
        "tree": tree
        }
        all_imports = {}
        all_variables = {}
        used_names = set()

        # Traverse the AST to collect definitions and usages
        for node in ast.walk(tree):
            # 1. Collect all imported modules and aliases
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    all_imports[name] = alias.name

            # 2. Collect all defined variables (Store context)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                all_variables[node.id] = True

            # 3. Track name and attribute usage (Load context)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used_names.add(node.id)
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                used_names.add(node.value.id)

        # Identify imports that were never used
        for imp in all_imports:
            if imp not in used_names:
                results["unused_imports"].append(imp)

        # Identify variables that were never used
        for var in all_variables:
            if var not in used_names:
                results["unused_variables"].append(var)

        # Clean up results: Remove keys if no unused items are found
        if not results["unused_imports"]: del results["unused_imports"]
        if not results["unused_variables"]: del results["unused_variables"]
        
        # --- Groq AI Review Integration ---
        # Generate a brief code review feedback using Llama3 on Groq
        chat_completion = model.chat.completions.create(
            messages=[{
                "role": "user",
                "content": f"Provide a very brief 2-line technical review for this code: {student_code}"
            }],
            model="llama-3.1-8b-instant", # This is the exact 'instant' model name
        )
        results["ai_review"] = chat_completion.choices[0].message.content

        return results
        
    except Exception as e:
        return {"error": str(e), "status": "Failed"}