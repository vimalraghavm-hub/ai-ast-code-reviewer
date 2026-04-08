import reflex as rx

class CodeState(rx.State):
    code_input: str = ""
    result: str = ""
    def set_code_input(self, code: str):
        self.code_input = code
        # Here you would add logic to process the code and generate review output
        self.review_output = "This is where the AI review results would appear."
    def analyze_code(self):
        # Placeholder for code analysis logic
        if self.code_input==" ":
                self.result = "Please enter code to analyze."
        else:
            self.result = "AI analysis will appear here after processing the input code."




# ---------------- NAVBAR ---------------- #

def navbar():
    return rx.hstack(
        rx.hstack(
            rx.icon("cpu"),
            rx.text("AI Code Reviewer", font_weight="bold", font_size="20px"),
            spacing="2",
        ),
        rx.spacer(),
        rx.hstack(
            rx.link("Home", href="/"),
            rx.link("History", href="/history"),
            rx.link("About", href="/about"),
            rx.link("Help", href="/help"),
            spacing="6",
        ),
        padding="20px",
        width="100%",
    )


# ---------------- HERO SECTION ---------------- #

def hero():
    return rx.center(
        rx.vstack(
            rx.badge("AI Powered Analysis", color_scheme="purple"),

            rx.heading(
                "AI-Driven Code Reviewer System",
                size="8",
                text_align="center",
            ),

            rx.text(
                "Advanced code review using AST parsing, "
                "PEP8 validation and AI-based optimization.",
                text_align="center",
                color="gray",
            ),

            rx.hstack(
                rx.button("95% Accurate"),
                rx.button("Real-time Analysis", variant="outline"),
                rx.button("Secure & Reliable", variant="outline"),
                spacing="4",
                margin_top="20px",
            ),

            spacing="6",
            align="center",
        ),
        height="80vh",
        width="100%",
        bg="linear-gradient(135deg, #6B73FF 0%, #000DFF 100%)",
        color="white",
    )


def analyzer_page():
    return rx.vstack(

        navbar(),

        rx.heading("AI Code Analyzer", size="8"),

        rx.text("Paste your Python code or upload a file to analyze."),

        rx.text_area(
            placeholder="Paste your code here...",
            value=CodeState.code_input,
            on_change=CodeState.set_code_input,
            width="80%",
            height="300px",
        ),

        rx.upload(
            rx.button("Upload Python File"),
            border="1px dashed gray",
            padding="1em",
        ),

        rx.button(
            "Analyze Code",
            on_click=CodeState.analyze_code,
            color_scheme="blue",
            margin_top="20px"
        ),

        rx.divider(),

        rx.heading("Analysis Result", size="6"),

        rx.box(
            rx.text(CodeState.result),
            padding="20px",
            border="1px solid #ccc",
            width="80%"
        ),

        align="center",
        spacing="5",
        padding="40px"
    )


# ---------------- PAGES ---------------- #

def home():
    return rx.vstack(
        navbar(),
        hero(),
        spacing="0",
    )


def history():
    return rx.center(rx.heading("History Page"), height="80vh")


def about():
    return rx.center(rx.heading("About Page"), height="80vh")


def help_page():
    return rx.center(rx.heading("Help Page"), height="80vh")


# ---------------- APP ---------------- #

app = rx.App()
app.add_page(home, route="/")
app.add_page(history, route="/history")
app.add_page(about, route="/about")
app.add_page(help_page, route="/help")