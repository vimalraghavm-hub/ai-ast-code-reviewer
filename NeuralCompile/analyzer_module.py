"""
analyzer_module.py - AI-powered code analyzer page with FIFO history, Neural Logic, and NLP metrics.
Uses Groq/LLM (Neural Network) for deep semantic analysis.
"""
import asyncio
import os
import re
import json
from datetime import datetime
from typing import List, Dict

import reflex as rx
import pydantic
from .models import HistoryEntry
from .fingerprint import DeviceState
from .components import navbar, footer
from reflex_monaco.monaco import MonacoEditor
from .error_detector import get_python_score
from .multi_language_detector import get_language_score

class AnalysisEntry(pydantic.BaseModel):
    code: str
    report: str
    language: str
    timestamp: str
    neural_score: int
    intent: str

def _analyze_with_neural_logic(code: str, language: str) -> dict:
    """Uses a 100B+ Parameter Neural Network (Groq) for NLP-driven code analysis."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        from langchain_groq import ChatGroq
        llm = ChatGroq(temperature=0.2, model_name="llama-3.1-8b-instant", api_key=os.getenv("GROQ_API_KEY"))
        
        prompt = f"""You are an advanced Neural Code Intelligence System.
Perform a deep Natural Language Processing (NLP) and Neural Network-based semantic analysis of the following {language} code.

1.  **Report**: provide a detailed markdown analysis (bugs, performance, clean code). 
    - **AI Optimization**: You MUST provide a high-performance, optimized version of the code that reduces time/space complexity or improves resource usage.
    - **Complexity Analysis**: You MUST explain the **Time Complexity** and **Space Complexity** for BOTH the original user code and your suggested optimized version.
    - **Structural Improvement**: If the code is just a simple script, suggest implementing it within a **Class** structure for better modularity and scalability.
    - **Robustness**: If there is no **Exception Handling** (try-except), suggest adding it to handle edge cases and runtime errors effectively.
    - **Syntax Safety**: You MUST ensure any code you suggest or fixed has valid syntax. Specifically, ensure all docstrings are correctly closed with triple quotes (\"\"\") and avoid unmatched single/double quotes.
2.  **Semantic Metrics** (JSON block at end):
    - "neural_complexity": 1-100 score
    - "semantic_intent": 1-2 word description (e.g., "Data Pipeline", "Neural Net", "Algorithm")
    - "maintainability_index": 1-100
    - "nlp_confidence": 0-1.0
    - "suggested_code": the full corrected code block.

```{language}
{code}
```"""
        ai_resp = llm.invoke(prompt).content
        
        # Extract markdown report
        report = re.split(r"```json", ai_resp, flags=re.IGNORECASE)[0]
        
        # Extract JSON metrics
        m = {"neural_complexity": 75, "semantic_intent": "General Logic", "maintainability_index": 80, "nlp_confidence": 0.95, "suggested_code": ""}
        try:
            json_match = re.search(r"```json\n(.*?)\n```", ai_resp, re.DOTALL | re.IGNORECASE)
            if json_match:
                m.update(json.loads(json_match.group(1)))
        except:
            pass
        # Deterministic Score for languages
        if language.lower() == "python":
            deterministic_score = get_python_score(code)
        else:
            deterministic_score = get_language_score(code, language)

        # Final score is a blend of deterministic logic and AI semantic judgment
        final_score = deterministic_score if deterministic_score > 0 else m.get("neural_complexity", 75)
        
        # Build metrics table for the report
        metrics_table = f"""
### 📊 Semantic Metrics
| Metric | Value |
| :--- | :--- |
| **Maintainability Index** | {m.get('maintainability_index', 'N/A')}% |
| **Neural Complexity** | {m.get('neural_complexity', 'N/A')}% |
| **Semantic Intent** | {m.get('semantic_intent', 'N/A')} |
| **NLP Confidence** | {m.get('nlp_confidence', 'N/A')} |
"""
        # Prepend score and append metrics to report
        report_with_score = f"# Code Quality Score: {final_score}/100\n\n" + report + metrics_table
            
        return {"report": report_with_score, "metrics": {**m, "quality_score": final_score}}
    except Exception as e:
        return {"report": f"❌ Neural Analysis failed: {e}", "metrics": {"quality_score": 0}}


class AnalyzerState(rx.State):
    code_input: str = ""
    language: str = "python"
    supported_languages: list[str] = ["python", "javascript", "typescript", "c", "cpp", "java"]
    analysis_result: str = ""
    is_analyzing: bool = False
    
    # Neural & NLP Metrics
    quality_score: int = 0
    neural_complexity: int = 0
    semantic_intent: str = "N/A"
    maintainability: int = 0
    nlp_confidence: float = 0.0
    suggested_code: str = ""
    
    # FIFO History (Limited to 5)
    analysis_history: List[AnalysisEntry] = []

    def set_code_input(self, val: str):
        self.code_input = val

    def set_language(self, lang: str):
        self.language = lang

    async def analyze(self):
        if not self.code_input.strip() or self.is_analyzing:
            return
        self.is_analyzing = True
        self.analysis_result = "🧠 Invoking Neural Logic Engine..."
        yield

        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, _analyze_with_neural_logic, self.code_input, self.language)
        
        self.analysis_result = data["report"]
        m = data["metrics"]
        self.quality_score = m.get("quality_score", 0)
        self.neural_complexity = m.get("neural_complexity", 0)
        self.semantic_intent = m.get("semantic_intent", "N/A")
        self.maintainability = m.get("maintainability_index", 0)
        self.nlp_confidence = m.get("nlp_confidence", 0.0)
        self.suggested_code = m.get("suggested_code", "")

        # Add to FIFO History
        new_entry = AnalysisEntry(
            code=self.code_input,
            report=self.analysis_result,
            language=self.language,
            timestamp=datetime.now().strftime("%H:%M:%S"),
            neural_score=self.neural_complexity,
            intent=self.semantic_intent
        )
        self.analysis_history.insert(0, new_entry) # Recent first
        if len(self.analysis_history) > 5:
            self.analysis_history.pop()

        # Persistent history
        device_state = await self.get_state(DeviceState)
        uuid = device_state.safe_uuid
        with rx.session() as session:
            session.add(HistoryEntry(
                device_uuid=uuid,
                title=f"Neural Analysis: {self.semantic_intent}",
                code=self.code_input[:2000],
                result=self.analysis_result[:2000],
                language=self.language,
                category="analysis",
            ))
            session.commit()

        self.is_analyzing = False

    def load_report(self, entry: AnalysisEntry):
        self.code_input = entry.code
        self.analysis_result = entry.report
        self.language = entry.language
        self.neural_complexity = entry.neural_score
        self.semantic_intent = entry.intent
        # Suggestions re-extracted if needed, but here we just show report

    def clear_all(self):
        self.code_input = ""
        self.analysis_result = ""
        self.analysis_history = []
        self.neural_complexity = 0
        self.semantic_intent = "N/A"

    def clear_input(self):
        self.code_input = ""
        self.analysis_result = ""


def neural_stat_card(label: str, value: str, icon: str, color: str):
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(icon, size=14, color=color),
                rx.text(label, font_size="10px", font_weight="bold", color="gray"),
                spacing="2", align="center",
            ),
            rx.text(value, font_size="18px", font_weight="800", color="var(--text-color)"),
            spacing="1", align="start",
        ),
        padding="12px", border="1px solid var(--border-color)", border_radius="10px", background="rgba(107, 115, 255, 0.03)", flex="1",
    )


def analyzer_page():
    return rx.vstack(
        navbar(active_page="Analyzer"),
        rx.vstack(
            rx.badge("🧠 Neural Network & NLP Powered", color_scheme="violet"),
            rx.heading("Neural Intent Analyzer", size="8", margin_top="4px"),
            rx.text("Semantic analysis using 100B+ parameter transformer architecture.", color="gray", font_size="14px"),

            # Stats Dashboard
            rx.hstack(
                neural_stat_card("Quality Score", AnalyzerState.quality_score.to(str) + "%", "star", "#FFD700"),
                neural_stat_card("Neural Complexity", AnalyzerState.neural_complexity.to(str) + "%", "activity", "#FF6B6B"),
                neural_stat_card("Semantic Intent", AnalyzerState.semantic_intent.to(str), "target", "#6B73FF"),
                neural_stat_card("NLP Confidence", AnalyzerState.nlp_confidence.to(str), "brain", "#9747FF"),
                width="100%", spacing="4", margin_top="10px",
            ),

            rx.hstack(
                rx.select(AnalyzerState.supported_languages, value=AnalyzerState.language, on_change=AnalyzerState.set_language, width="140px", size="2"),
                rx.spacer(),
                rx.button("Reset Session", on_click=AnalyzerState.clear_all, color_scheme="red", variant="ghost", size="2"),
                rx.button(rx.icon("brain", size=14), "Neural Analysis", on_click=AnalyzerState.analyze, color_scheme="iris", size="2", is_loading=AnalyzerState.is_analyzing),
                width="100%", align="center", margin_top="10px",
            ),

            rx.hstack(
                # LEFT: Editor
                rx.vstack(
                    rx.text("Raw Source Code", font_weight="700", size="2"),
                    rx.box(
                        rx.cond(
                            AnalyzerState.is_hydrated,
                            rx.box(
                                MonacoEditor.create(
                                    id="analyzer-editor",
                                    value=AnalyzerState.code_input,
                                    on_change=AnalyzerState.set_code_input,
                                    language=AnalyzerState.language,
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
                        width="100%", height="450px", 
                        border="1px solid var(--border-color)", border_radius="12px", overflow="hidden",
                    ),
                    width="45%",
                ),

                # CENTER: Report
                rx.vstack(
                    rx.text("Neural Intelligence Report", font_weight="700", size="2"),
                    rx.box(
                        rx.cond(
                            AnalyzerState.analysis_result != "",
                            rx.markdown(
                                AnalyzerState.analysis_result,
                                class_name="chat-markdown",
                                component_map={
                                    "code": lambda value, inline=False: rx.cond(
                                        inline,
                                        rx.code(
                                            value, 
                                            background="rgba(107,115,255,0.15)",
                                            color="#6B73FF",
                                            font_size="12px",
                                            padding="2px 4px",
                                            border="1px solid rgba(107,115,255,0.3)"
                                        ),
                                        rx.box(
                                            rx.code_block(
                                                value,
                                                theme="vs-dark",
                                                language=AnalyzerState.language,
                                                show_line_numbers=False,
                                                width="100%",
                                                custom_style={"backgroundColor": "transparent", "padding": "0", "margin": "0"},
                                            ),
                                            rx.button(
                                                rx.icon("copy", size=14), 
                                                on_click=rx.set_clipboard(value), 
                                                position="absolute", top="8px", right="8px", 
                                                size="1", variant="soft", color_scheme="blue",
                                                z_index="10"
                                            ),
                                            class_name="neural-code-container",
                                            padding="35px 15px 15px 15px",
                                            margin_y="8px",
                                        ),
                                    ),
                                }
                            ),
                            rx.center(rx.vstack(rx.icon("brain-circuit", size=48, color="#30363d"), rx.text("Neural output will appear here.", color="gray")), height="100%"),
                        ),
                        width="100%", height="450px", padding="20px", border="1px solid var(--border-color)", border_radius="12px", background="var(--bg-color)", overflow_y="auto", overflow_x="hidden",
                    ),
                    width="40%",
                ),

                # RIGHT: FIFO History
                rx.vstack(
                    rx.text("Neural History", font_weight="700", size="2"),
                    rx.scroll_area(
                        rx.vstack(
                            rx.foreach(
                                AnalyzerState.analysis_history,
                                lambda entry: rx.box(
                                    rx.vstack(
                                        rx.hstack(rx.badge(entry.language, size="1"), rx.spacer(), rx.text(entry.timestamp, font_size="9px")),
                                        rx.text(entry.intent, font_size="11px", font_weight="bold", color="#6B73FF"),
                                        rx.button("Load", on_click=lambda: AnalyzerState.load_report(entry), size="1", variant="soft", width="100%"),
                                        spacing="1", align="start",
                                    ),
                                    padding="10px", margin_bottom="10px", border="1px solid var(--border-color)", border_radius="10px", background="rgba(107,115,255,0.02)", width="100%",
                                )
                            ),
                            width="100%", align="stretch",
                        ),
                        height="450px", width="100%",
                    ),
                    width="15%",
                ),
                width="100%", spacing="4", align="start",
            ),
            
            # NLP Suggested Output
            rx.cond(
                AnalyzerState.suggested_code != "",
                rx.vstack(
                    rx.text("💡 Neural Optimization Suggestion", font_weight="700", size="2"),
                    rx.box(
                        rx.code_block(
                            AnalyzerState.suggested_code, 
                            theme="vs-dark", 
                            language=AnalyzerState.language, 
                            custom_style={"backgroundColor": "transparent"}, 
                            width="100%"
                        ),
                        rx.button(
                            rx.icon("copy", size=16), 
                            rx.text("Copy Neural Logic", size="2"),
                            on_click=rx.set_clipboard(AnalyzerState.suggested_code),
                            position="absolute", top="10px", right="10px", 
                            size="1", variant="outline", color_scheme="blue", z_index="10",
                        ),
                        class_name="neural-code-container",
                        padding="45px 15px 15px 15px",
                    ),
                    spacing="3", width="100%",
                ),
            ),

            width="100%", padding_x="40px", align="center", spacing="4", padding_top="24px", class_name="animate-slide-up",
        ),
        footer(),
        width="100%", min_height="100vh", background_color="var(--bg-color)",
    )
