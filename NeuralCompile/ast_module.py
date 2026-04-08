"""
ast_module.py - AST (Abstract Syntax Tree) visualization page.
"""
import ast
import json

import reflex as rx
from .components import navbar, footer
from reflex_monaco.monaco import MonacoEditor


class ASTState(rx.State):
    code_input: str = "def greet(name):\n    return f'Hello, {name}!'"
    language: str = "python"
    supported_languages: list[str] = ["python", "javascript", "typescript", "c", "cpp", "java"]
    ast_json: str = ""
    error: str = ""
    is_generating: bool = False

    def set_language(self, lang: str):
        self.language = lang

    def set_code_input(self, val: str):
        self.code_input = val

    async def generate_ast(self):
        if not self.code_input.strip() or self.is_generating:
            return
        self.is_generating = True
        self.error = ""
        self.ast_json = ""
        yield

        import asyncio
        loop = asyncio.get_event_loop()

        if self.language == "python":
            try:
                tree = ast.parse(self.code_input)
                self.ast_json = ast.dump(tree, indent=2)
            except SyntaxError as e:
                self.error = f"SyntaxError at line {e.lineno}: {e.msg}"
            except Exception as e:
                self.error = str(e)
        else:
            try:
                from dotenv import load_dotenv
                load_dotenv()
                from langchain_groq import ChatGroq
                import os
                llm = ChatGroq(temperature=0, model_name="llama-3.1-8b-instant", api_key=os.getenv("GROQ_API_KEY"))
                prompt = f"""Generate a structural Abstract Syntax Tree (AST) representation for this {self.language} code.
Match the style of Python's ast.dump(indent=2). Use hierarchical indentation.
Code:\n{self.code_input}"""
                response = await loop.run_in_executor(None, lambda: llm.invoke(prompt).content)
                self.ast_json = response.strip()
            except Exception as e:
                self.error = f"AI AST Parse failed: {str(e)}"
        
        self.is_generating = False
        yield


def ast_page():
    return rx.vstack(
        navbar(active_page="AST"),
        rx.vstack(
            rx.badge("🌳 AST Explorer", color_scheme="green"),
            rx.heading("Abstract Syntax Tree Viewer", size="7"),
            rx.text("Parse Python code and explore its AST representation.", color="gray"),

            rx.hstack(
                rx.text("Language:", font_weight="600"),
                rx.select(
                    ASTState.supported_languages,
                    value=ASTState.language,
                    on_change=ASTState.set_language,
                    width="120px", size="1", variant="soft",
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("tree-pine", size=14), "Parse AST",
                    on_click=ASTState.generate_ast,
                    color_scheme="green", size="2",
                    is_loading=ASTState.is_generating
                ),
            ),

            rx.hstack(
                rx.vstack(
                    rx.text("Source Code", font_weight="700", size="2"),
                    rx.box(
                        rx.cond(
                            ASTState.is_hydrated,
                            rx.box(
                                MonacoEditor.create(
                                    id="ast-editor",
                                    value=ASTState.code_input,
                                    on_change=ASTState.set_code_input,
                                    language=ASTState.language,
                                    theme="vs-dark",
                                    width="100%",
                                    height="100%",
                                ),
                                width="100%", height="100%"
                            ),
                            rx.center(
                                rx.vstack(
                                    rx.spinner(size="3"),
                                    rx.text("Connecting to Neural Engine...", font_size="14px", color="rgba(255,255,255,0.4)"),
                                    align="center", spacing="3"
                                ),
                                width="100%", height="100%", background="rgba(0,0,0,0.1)"
                            )
                        ),
                        width="100%", height="350px", 
                        border="1px solid var(--border-color)", border_radius="8px", overflow="hidden",
                    ),
                    width="50%", spacing="2",
                ),

                rx.vstack(
                    rx.text("AST Output", font_weight="700", size="2"),
                    rx.cond(
                        ASTState.error != "",
                        rx.box(
                            rx.text(ASTState.error, color="#ff7b72",
                                    font_family="'JetBrains Mono', monospace", size="2"),
                            padding="12px",
                            border="1px solid #cf222e",
                            border_radius="8px",
                            background="rgba(207,34,46,0.05)",
                            width="100%",
                        ),
                        rx.cond(
                            ASTState.ast_json != "",
                                    rx.box(
                                        rx.code_block(
                                            ASTState.ast_json, 
                                            theme="vs-dark",
                                            language=ASTState.language,
                                            show_line_numbers=False,
                                            custom_style={
                                                "fontSize": "11px", 
                                                "height": "350px", 
                                                "backgroundColor": "transparent", 
                                                "padding": "0",
                                                "margin": "0",
                                            }
                                        ),
                                        rx.button(
                                            rx.icon("copy", size=14), 
                                            rx.text("Copy Tree", size="1"),
                                            on_click=rx.set_clipboard(ASTState.ast_json), 
                                            position="absolute", top="8px", right="8px",
                                            size="1", variant="soft", color_scheme="blue", z_index="10"
                                        ),
                                        class_name="neural-code-container",
                                        padding="40px 15px 15px 15px",
                                        overflow_y="auto",
                                        height="400px",
                                    ),
                            rx.center(
                                rx.vstack(
                                    rx.icon("tree-pine", size=48, color="#30363d"),
                                    rx.text("AST will appear here", color="gray"),
                                    align="center",
                                ),
                                height="350px", width="100%",
                                border="1px solid #30363d", border_radius="8px",
                            ),
                        ),
                    ),
                    width="50%", spacing="2",
                ),

                width="100%", spacing="4", align="start",
            ),

            width="100%", padding_x="40px",
            align="center", spacing="4",
            padding_top="24px",
            class_name="page-content",
        ),
        footer(),
        width="100%", min_height="100vh",
        background_color="var(--bg-color)",
    )
