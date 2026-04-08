"""
home_module.py - Landing page, About, and Help pages for Neural Compile.
"""
import reflex as rx
from .components import navbar, footer


def feature_highlight_card(icon, color, title, subtitle, description, href, badge_text):
    return rx.vstack(
        rx.hstack(
            rx.box(
                rx.icon(icon, size=28, color="white"),
                background=f"linear-gradient(135deg, {color}aa, {color})",
                padding="14px",
                border_radius="14px",
            ),
            rx.vstack(
                rx.badge(badge_text, color_scheme="gray", variant="soft", size="1"),
                rx.text(title, font_weight="800", size="5", class_name="feature-title"),
                spacing="1",
                align="start",
            ),
            spacing="4",
            align="center",
            width="100%",
        ),
        rx.text(subtitle, font_weight="600", size="3", color=color),
        rx.text(description, color="gray", size="2", line_height="1.7"),
        rx.link(
            rx.hstack(
                rx.text("Explore", size="2", color=color, font_weight="600"),
                rx.icon("arrow-right", size=14, color=color),
                spacing="1",
                align="center",
            ),
            href=href,
        ),
        padding="28px",
        background="rgba(255,255,255,0.03)",
        border=f"1px solid {color}33",
        border_radius="20px",
        align="start",
        spacing="4",
        class_name="feature-highlight-card",
        width="100%",
        _hover={"border": f"1px solid {color}88", "background": f"rgba(255,255,255,0.06)", "transform": "translateY(-4px)", "transition": "all 0.25s ease"},
        transition="all 0.25s ease",
    )


# FAQ data: (icon, question, answer)
_FAQS = [
    (
        "code-2",
        "What programming languages does Neural Compile support?",
        "Neural Compile supports Python, JavaScript, TypeScript, Java, C, C++."
        "The Monaco editor provides syntax highlighting for 50+ languages, while deep AI analysis and CFG generation "
        "are optimized for Python, JavaScript, and TypeScript.",
    ),
    (
        "user-x",
        "Do I need to create an account to use Neural Compile?",
        "No account is needed! Neural Compile uses a hardware fingerprint stored in your browser to identify your device. "
        "Your code execution history is automatically saved and accessible from the History page, completely anonymously.",
    ),
    (
        "zap",
        "How fast is the AI analysis?",
        "Extremely fast. We use Groq's LPU (Language Processing Unit) inference, which is 10-100x faster than "
        "traditional GPU-based AI inference. You can expect AI code reviews to complete in under a second for most code snippets.",
    ),
    (
        "git-branch",
        "What is a Control Flow Graph (CFG) and why is it useful?",
        "A CFG is a visual representation of all possible paths your code can take during execution. "
        "Each node is a block of code, and edges represent jumps (like if/else or loops). It helps you visually "
        "understand complex logic, identify dead code, and see how an AI reads your program's structure.",
    ),
    (
        "monitor-play",
        "What is the difference between the Visualizer and the CFG Viewer?",
        "The Visualizer is a runtime tool — it executes your code step-by-step and shows you the memory state "
        "(variables, stacks) at each moment. The CFG Viewer is a static analysis tool — it shows the logical "
        "structure of your code's branches and paths without running it.",
    ),
    (
        "shield-check",
        "Is my code safe and private?",
        "Your code is sent to the Groq API only when you explicitly click 'AI Analyze' or use the AI Chat. "
        "Code execution happens on the Neural Compile server. We do not permanently store your source code; "
        "history records contain execution outputs, not the full source.",
    ),
    (
        "message-circle",
        "Can the AI Chat see my current code?",
        "Yes! The AI Chat Assistant is context-aware. It automatically includes the code from your current "
        "editor session so you can ask questions like 'what does this function do?' or 'how can I optimize this loop?' "
        "without needing to copy-paste anything.",
    ),
    (
        "github",
        "Is Neural Compile open source?",
        "Yes! Neural Compile is open source and available on GitHub. The project is built with Reflex (Python web framework), "
        "Groq for AI inference, and Monaco Editor for the code editing experience. Contributions and feedback are welcome.",
    ),
]


def faq_accordion_item(icon: str, question: str, answer: str, value: str):
    """
    Accordion FAQ item styled to match the project's dark #0d1117 theme.
    Uses custom.css classes: faq-accordion-item, faq-accordion-content, faq-answer-card.
    """
    return rx.accordion.item(
        value=value,
        header=rx.hstack(
            rx.icon("circle-help", size=18, color="#6B73FF", flex_shrink="0"),
            rx.text(
                question,
                size="3",
                font_weight="600",
                color="#e6edf3",
            ),
            spacing="3",
            align="center",
            width="100%",
        ),
        content=rx.box(
            rx.hstack(
                rx.text(
                    answer,
                    size="2",
                    color="#8b949e",
                    line_height="1.8",
                    flex="1",
                ),
                rx.box(
                    rx.icon("message-circle", size=18, color="#6B73FF"),
                    padding="8px",
                    border_radius="50%",
                    background="rgba(107,115,255,0.12)",
                    border="1px solid rgba(107,115,255,0.2)",
                    flex_shrink="0",
                    align_self="flex-start",
                ),
                spacing="4",
                align="start",
                width="100%",
            ),
            class_name="faq-answer-card",
        ),
        class_name="faq-accordion-item",
    )



def home_page():
    return rx.vstack(
        navbar(active_page="Home"),
        # Hero
        rx.box(
            rx.center(
                rx.vstack(
                    rx.image(src="/logo.png", width="150px", height="auto", margin_bottom="20px"),
                    rx.badge("🧠 Neural Compile(AI-Driven Code Reviewer)", color_scheme="blue", class_name="hero-badge"),
                    rx.heading(
                        "The AI-Powered Compilation Suite",
                        size="9",
                        text_align="center",
                        class_name="hero-heading",
                        background="linear-gradient(135deg, #e6edf3 0%, #6B73FF 50%, #9747FF 100%)",
                        background_clip="text",
                        color="transparent",
                    ),
                    rx.text(
                        "Write, execute, visualize, and optimize code across multiple languages with Groq-accelerated AI analysis.",
                        text_align="center",
                        color="gray",
                        max_width="600px",
                        class_name="hero-subtext",
                    ),
                    rx.hstack(
                        rx.link(
                            rx.button("Open Editor", color_scheme="blue", size="3", class_name="shimmer-btn glow-btn"),
                            href="/editor",
                        ),
                        rx.link(
                            rx.button("Visualize Code", variant="outline", size="3", class_name="shimmer-btn"),
                            href="/visualizer",
                        ),
                        rx.link(
                            rx.button("AI Analyzer", color_scheme="violet", size="3", class_name="shimmer-btn"),
                            href="/analyze",
                        ),
                        spacing="4",
                        class_name="hero-buttons",
                    ),
                    spacing="6",
                    align="center",
                    max_width="800px",
                ),
                width="100%",
                min_height="70vh",
            ),
            width="100%",
            class_name="hero-section",
        ),

        # Quick Feature Overview
        rx.vstack(
            rx.heading("Everything You Need", size="7", text_align="center"),
            rx.hstack(
                *[
                    rx.vstack(
                        rx.icon(icon, size=32, color=color),
                        rx.text(title, font_weight="700", size="4"),
                        rx.text(desc, color="gray", text_align="center", size="2"),
                        padding="28px",
                        background="rgba(107,115,255,0.05)",
                        border="1px solid rgba(107,115,255,0.15)",
                        border_radius="16px",
                        align="center",
                        class_name="feature-card",
                        spacing="3",
                        flex="1",
                    )
                    for icon, color, title, desc in [
                        ("code", "#6B73FF",    "Neural IDE",        "Monaco-powered editor with multi-language support and IntelliSense."),
                        ("git-branch", "#9747FF","CFG Viewer",      "Interactive Control Flow Graphs rendered in real-time."),
                        ("monitor-play", "#E36209","Neural Tutor",  "Python Tutor-style line-by-line execution with variable state tracking."),
                        ("zap", "#7ee787",     "AI Code Review",    "Groq-accelerated analysis for bugs, performance, and clean code."),
                        ("history", "#0969DA", "Device History",    "Execution logs partitioned by hardware fingerprint - no login required."),
                    ]
                ],
                width="100%", spacing="4", align="start",
            ),
            width="100%",
            padding="40px",
            max_width="1400px",
            margin_x="auto",
            spacing="8",
        ),

        # === FEATURE HIGHLIGHTS ===
        rx.vstack(
            rx.center(
                rx.vstack(
                    rx.badge("Core Features", color_scheme="violet", size="2"),
                    rx.heading(
                        "Powerful Tools, Beautifully Integrated",
                        size="8",
                        text_align="center",
                        background="linear-gradient(135deg, #e6edf3 0%, #9747FF 100%)",
                        background_clip="text",
                        color="transparent",
                    ),
                    rx.text(
                        "Every module in Neural Compile is purpose-built to make you a faster, smarter developer.",
                        text_align="center",
                        color="gray",
                        max_width="550px",
                        size="3",
                    ),
                    spacing="4",
                    align="center",
                ),
                width="100%",
            ),
            rx.grid(
                feature_highlight_card(
                    "git-branch", "#9747FF",
                    "Control Flow Graph (CFG) Viewer",
                    "See how your code thinks.",
                    "Neural Compile automatically generates an interactive Control Flow Graph from your source code. "
                    "Understand the exact execution path of your program, identify unreachable code blocks, and spot "
                    "complex branching logic that could hide bugs. Supports Python, JavaScript, and more.",
                    "/analyze",
                    "Compiler Intelligence",
                ),
                feature_highlight_card(
                    "monitor-play", "#E36209",
                    "Step-by-Step Code Visualizer",
                    "Watch your code come alive, line by line.",
                    "Like Python Tutor, but smarter. The Neural Visualizer executes your code step-by-step, showing you "
                    "the exact state of every variable, stack frame, and data structure at each moment in time. "
                    "Perfect for debugging, learning, and teaching complex algorithms.",
                    "/visualizer",
                    "Execution Tracing",
                ),
                feature_highlight_card(
                    "zap", "#7ee787",
                    "AI Code Analysis",
                    "Groq-accelerated intelligence for your code.",
                    "Powered by Groq's blazing-fast LPU inference, Neural Compile's AI Analyzer reviews your code for "
                    "bugs, security vulnerabilities, performance bottlenecks, and style issues in under a second. "
                    "It reasons over your code's AST — not just the text — for deeper, more accurate insights.",
                    "/analyze",
                    "AI-Powered",
                ),
                feature_highlight_card(
                    "message-circle", "#0969DA",
                    "AI Chat Assistant",
                    "Your senior developer, always available.",
                    "Ask questions about your code in plain English. The AI Chat has full context of your current "
                    "code editor contents and conversation history. Get explanations, ask for refactoring suggestions, "
                    "or have it write new functions — all without leaving your IDE.",
                    "/editor",
                    "Conversational AI",
                ),
                columns="2",
                spacing="6",
                width="100%",
            ),
            width="100%",
            padding="60px 40px",
            max_width="1200px",
            margin_x="auto",
            spacing="9",
        ),

        # === FAQ SECTION — Accordion Cards ===
        rx.vstack(
            # Section header
            rx.center(
                rx.vstack(
                    rx.badge("FAQ", color_scheme="violet", size="2"),
                    rx.heading(
                        "Frequently Asked Questions",
                        size="8",
                        text_align="center",
                        color="white",
                    ),
                    rx.text(
                        "Everything you need to know about Neural Compile.",
                        text_align="center",
                        color="#94a3b8",
                        size="3",
                    ),
                    spacing="4",
                    align="center",
                    max_width="600px",
                ),
                width="100%",
            ),
            # Accordion — max width centered, matching the faq-accordion.tsx layout
            rx.box(
                rx.accordion.root(
                    *[
                        faq_accordion_item(icon, question, answer, f"faq-{i}")
                        for i, (icon, question, answer) in enumerate(_FAQS)
                    ],
                    collapsible=True,
                    type="single",
                    width="100%",
                ),
                width="100%",
                max_width="760px",
                margin_x="auto",
            ),
            width="100%",
            padding="60px 40px",
            max_width="1200px",
            margin_x="auto",
            spacing="9",
            border_top="1px solid rgba(107,115,255,0.15)",
            border_bottom="1px solid rgba(107,115,255,0.15)",
            background="rgba(5,5,25,0.4)",
        ),

        footer(),
        background_color="var(--bg-color)",
        width="100%",
        spacing="0",
    )


def about_page():
    return rx.vstack(
        navbar(active_page="About"),
        rx.container(
            rx.vstack(
                rx.center(
                    rx.vstack(
                        rx.badge("About Neural Compile", color_scheme="blue", size="3"),
                        rx.heading("Neural Compile: An Agentic Framework for Modern Compilers", size="9", text_align="center"),
                        rx.text(
                            "The evolution of software development requires more than just syntax checking. "
                            "Neural Compile bridges the gap between raw code and human intent using AI-driven agentic reasoning.",
                            max_width="800px", text_align="center", font_size="1.2em", color="gray"
                        ),
                        spacing="6", align="center",
                    ),
                    padding_y="60px",
                ),

                rx.divider(),

                # Problem & Solution
                rx.grid(
                    rx.vstack(
                        rx.heading("The Problem", size="6", color="red"),
                        rx.text("Traditional compilers are deterministic and 'intent-blind'. They can tell you where a semicolon is missing, but they can't understand the semantic logic of a complex algorithm or identify subtle architectural flaws that lead to technical debt."),
                        align="start", spacing="3",
                    ),
                    rx.vstack(
                        rx.heading("The Agentic Solution", size="6", color="green"),
                        rx.text("Neural Compile introduces an 'Agentic' layer. Instead of simple rule-based checks, it utilizes AI agents that reason about your code's Abstract Syntax Tree (AST) and Control Flow Graph (CFG) to provide human-like feedback and optimizations."),
                        align="start", spacing="3",
                    ),
                    columns="2", spacing="8", width="100%", padding_y="40px",
                ),

                rx.divider(),

                # How it works
                rx.vstack(
                    rx.heading("How It Works: Neural Networks & NLP", size="7"),
                    rx.text(
                        "At its core, Neural Compile treats code as a specialized form of natural language. "
                        "By using Transformer-based models via Groq's API acceleration, we perform Natural Language Processing (NLP) "
                        "over the code's structural data. This allows the system to 'reason' about variables, loops, and logic "
                        "just like a senior engineer would during a code review.",
                        max_width="900px",
                    ),
                    rx.hstack(
                        rx.badge("NLP Reasoning", color_scheme="orange"),
                        rx.badge("Graph Analysis", color_scheme="blue"),
                        rx.badge("LLM Orchestration", color_scheme="green"),
                        spacing="3",
                    ),
                    align="start", spacing="4", padding_y="40px",
                ),

                rx.divider(),

                # Future Work
                rx.vstack(
                    rx.heading("The Roadmap: Future Work", size="7"),
                    rx.grid(
                        rx.vstack(
                            rx.heading("Multi-Language Expansion", size="4"),
                            rx.text("Adding deep support for low-level systems languages like C++ and Rust, including memory safety analysis."),
                            align="start",
                        ),
                        rx.vstack(
                            rx.heading("Real-time Agentic Fixes", size="4"),
                            rx.text("Moving beyond analysis to 'Self-Healing' code where agents suggest and apply fixes as you type."),
                            align="start",
                        ),
                        rx.vstack(
                            rx.heading("Git & CI/CD Integration", size="4"),
                            rx.text("Automated agentic code reviews integrated directly into your Pull Request workflow."),
                            align="start",
                        ),
                        rx.vstack(
                            rx.heading("Deep AST Reasoning", size="4"),
                            rx.text("Enhanced mapping between visual AST nodes and semantic intent for even more precise bug detection."),
                            align="start",
                        ),
                        columns="2", spacing="6", width="100%",
                    ),
                    align="start", spacing="6", padding_y="40px",
                ),

                spacing="8",
                width="100%",
                padding_x="20px",
            ),
            max_width="1000px",
            margin_x="auto",
        ),
        footer(),
        background_color="var(--bg-color)", width="100%",
        padding_bottom="100px",
    )


def help_page():
    return rx.vstack(
        navbar(active_page="Help"),
        rx.center(
            rx.vstack(
                rx.badge("Help & Documentation", color_scheme="green"),
                rx.heading("Getting Started", size="8"),
                rx.vstack(
                    *[
                        rx.hstack(
                            rx.badge(step, color_scheme="blue", variant="soft"),
                            rx.text(desc, size="3"),
                            spacing="4", align="center",
                        )
                        for step, desc in [
                            ("1", "Navigate to /editor or /visualizer"),
                            ("2", "Select your programming language from the dropdown"),
                            ("3", "Write or paste your code in the Monaco editor"),
                            ("4", "Click RUN to execute, VISUALIZE to trace line-by-line, or AI FIX to review"),
                            ("5", "Your sessions are automatically saved and viewable at /history"),
                        ]
                    ],
                    spacing="4", align="start",
                ),
                spacing="6", align="start", max_width="600px",
            ),
            min_height="70vh", width="100%",
        ),
        footer(),
        background_color="var(--bg-color)", width="100%",
    )
