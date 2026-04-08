import reflex as rx
import os
import subprocess
from rxconfig import config

from .home_module import home_page, about_page, help_page
from .analyzer_module import analyzer_page
from .editor_module import editor_page, cfg_page
from .visualizer_module import visualizer_page
from .history_module import history_page
from .ast_module import ast_page
from .contact_module import contact_page
from .models import DeviceProfile, HistoryEntry  # ensure tables are created
from .fingerprint import DeviceState

app = rx.App(
    theme=rx.theme(
        accent_color="iris",
        radius="medium",
    ),
    head_components=[
        rx.el.link(rel="icon", type="image/png", href="/logo.png")
    ],
    stylesheets=["/custom.css"],
)

app.add_page(home_page,       route="/",           title="Neural Compile - Home",       on_load=DeviceState.check_or_create_id)
app.add_page(analyzer_page,   route="/analyze",    title="Neural Compile - Analyzer",   on_load=DeviceState.check_or_create_id)
app.add_page(editor_page,     route="/editor",     title="Neural Compile - Editor",     on_load=DeviceState.check_or_create_id)
app.add_page(cfg_page,        route="/cfg",        title="Neural Compile - CFG",        on_load=DeviceState.check_or_create_id)
app.add_page(ast_page,        route="/ast",        title="Neural Compile - AST",        on_load=DeviceState.check_or_create_id)
app.add_page(visualizer_page, route="/visualizer", title="Neural Compile - Visualizer", on_load=DeviceState.check_or_create_id)
app.add_page(history_page,    route="/history",    title="Neural Compile - History",    on_load=DeviceState.check_or_create_id)
app.add_page(contact_page,     route="/contact",    title="Neural Compile - Contact",   on_load=DeviceState.check_or_create_id)
app.add_page(about_page,      route="/about",      title="Neural Compile - About",      on_load=DeviceState.check_or_create_id)
app.add_page(help_page,       route="/help",       title="Neural Compile - Help",       on_load=DeviceState.check_or_create_id)

# Database Initialization (for Reflex Cloud SQLite defaults)
# When deployed, ephemeral environments may fail to auto-migrate. This guarantees
# that our SQLModel tables exist immediately before routing any events.
from sqlmodel import SQLModel
from sqlalchemy import create_engine

db_url = config.db_url if config.db_url is not None else "sqlite:///reflex.db"
if db_url.startswith("sqlite"):
    engine = create_engine(db_url)
    SQLModel.metadata.create_all(engine)
