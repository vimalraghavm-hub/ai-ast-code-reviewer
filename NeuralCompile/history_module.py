import reflex as rx
from pydantic import BaseModel
from .models import HistoryEntry
from .fingerprint import DeviceState
from .components import navbar, footer


class HistoryDisplay(BaseModel):
    """UI-friendly wrapper for a HistoryEntry with pre-formatted timestamp."""
    id: int = 0
    title: str = ""
    code: str = ""
    result: str = ""
    language: str = "python"
    category: str = "execution"
    timestamp_str: str = ""   # Pre-formatted on the backend


class HistoryState(rx.State):
    """Manages session-isolated history retrieval from SQLite."""

    @rx.var(deps=[DeviceState.device_id])
    async def history_list(self) -> list[HistoryDisplay]:
        """Reactive retrieval of the top 10 logs for the current device."""
        device_state = await self.get_state(DeviceState)
        uuid = device_state.safe_uuid
        if not uuid:
            return []
        with rx.session() as session:
            results = (
                session.query(HistoryEntry)
                .filter(HistoryEntry.device_uuid == uuid)
                .order_by(HistoryEntry.timestamp.desc())
                .limit(10)
                .all()
            )
            print(f"[History] Retrieved {len(results)} entries for UUID: {uuid[:12]}...")
            return [
                HistoryDisplay(
                    id=r.id or 0,
                    title=r.title,
                    code=r.code,
                    result=r.result,
                    language=r.language,
                    category=r.category,
                    timestamp_str=r.timestamp.isoformat() + "Z" if r.timestamp else "",
                )
                for r in results
            ]

    async def clear_history(self):
        device_state = await self.get_state(DeviceState)
        uuid = device_state.safe_uuid
        with rx.session() as session:
            session.query(HistoryEntry).filter(
                HistoryEntry.device_uuid == uuid
            ).delete()
            session.commit()


def history_page():
    return rx.vstack(
        navbar(active_page="History"),
        rx.vstack(
            rx.badge("🕒 Execution History", color_scheme="blue"),
            rx.heading("Your Past Sessions", size="8"),
            rx.text(
                "Access and review your 10 most recent execution and analysis logs. "
                "Data is hardware-isolated and stored locally.",
                color="gray",
            ),
            rx.cond(
                HistoryState.history_list.length() > 0,
                rx.vstack(
                    rx.button(
                        "Clear My History",
                        on_click=HistoryState.clear_history,
                        color_scheme="red", variant="outline", size="2",
                    ),
                    rx.foreach(
                        HistoryState.history_list,
                        lambda item: rx.box(
                            rx.vstack(
                                rx.hstack(
                                    rx.badge(item.category, color_scheme="blue", variant="soft"),
                                    rx.badge(item.language, color_scheme="violet", variant="soft"),
                                    rx.text(item.title, font_weight="bold", font_size="16px", color="#6B73FF"),
                                    rx.spacer(),
                                    rx.hstack(
                                        rx.icon("clock", size=14, color="gray"),
                                        rx.moment(
                                            item.timestamp_str,
                                            format="MMM DD, YYYY  h:mm A",
                                            font_size="12px", color="gray", font_family="monospace"
                                        ),
                                        spacing="1", align="center",
                                    ),
                                    width="100%", align="center",
                                ),
                                rx.divider(),
                                rx.hstack(
                                    rx.box(
                                        rx.code_block(
                                            item.code,
                                            language=item.language,
                                            theme="vs-dark",
                                            show_line_numbers=True,
                                            width="100%",
                                            custom_style={"backgroundColor": "transparent", "padding": "0"},
                                        ),
                                        rx.button(
                                            rx.icon("copy", size=12), 
                                            rx.text("Copy", size="1"),
                                            on_click=rx.set_clipboard(item.code), 
                                            position="absolute", top="8px", right="8px", 
                                            size="1", variant="soft", color_scheme="blue", z_index="200",
                                        ),
                                        class_name="neural-code-container",
                                        padding="40px 15px 15px 10px",
                                        width="55%",
                                    ),
                                    rx.vstack(
                                        rx.text("Execution Result:", font_weight="bold", size="2"),
                                        rx.box(
                                            rx.markdown(item.result),
                                            padding="15px",
                                            background="rgba(107,115,255,0.06)",
                                            border="1px solid rgba(107,115,255,0.1)",
                                            border_radius="8px",
                                            width="100%",
                                            max_height="450px",
                                            overflow_y="auto",
                                        ),
                                        width="45%",
                                        align="start",
                                    ),
                                    spacing="6", align="start", width="100%",
                                ),
                                spacing="3",
                            ),
                            width="100%",
                            padding="20px",
                            border="1px solid var(--border-color)",
                            border_radius="10px",
                            background="var(--card-bg)",
                        )
                    ),
                    width="100%", spacing="5", padding_top="20px",
                ),
                rx.center(
                    rx.vstack(
                        rx.icon("history", size=64, color="#30363d"),
                        rx.text("No history found for this device yet.", color="gray"),
                        rx.text("Run some code to start building your history!", color="gray", size="2"),
                        align="center", spacing="4",
                    ),
                    height="50vh", width="100%",
                )
            ),
            width="100%", padding_x="40px",
            align="center", spacing="4", padding_top="24px",
        ),
        footer(),
        width="100%",
        min_height="100vh",
        background_color="var(--bg-color)",
    )
