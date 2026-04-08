import reflex as rx
from .components import navbar, footer

def contact_item(icon: str, label: str, value: str, href: str = "#", color: str = "iris"):
    return rx.link(
        rx.hstack(
            rx.box(
                rx.icon(icon, size=24),
                padding="12px",
                background=f"var(--{color}-3)",
                border_radius="12px",
                color=f"var(--{color}-9)",
            ),
            rx.vstack(
                rx.text(label, font_size="12px", color="gray", font_weight="500"),
                rx.text(value, font_size="16px", font_weight="600", color="var(--text-color)"),
                spacing="0",
                align="start",
            ),
            rx.spacer(),
            rx.icon("external-link", size=18, opacity="0.5"),
            width="100%",
            padding="20px",
            background="rgba(255,255,255,0.03)",
            border="1px solid rgba(255,255,255,0.05)",
            border_radius="16px",
            transition="all 0.2s ease",
            _hover={
                "background": "rgba(255,255,255,0.07)",
                "border_color": f"var(--{color}-7)",
                "transform": "translateY(-2px)",
            },
            align="center",
        ),
        href=href,
        is_external=True,
        text_decoration="none",
        width="100%",
    )

def contact_page():
    return rx.vstack(
        navbar(active_page="Contact"),
        
        rx.vstack(
            rx.badge("Let's Connect and Build", color_scheme="iris", variant="surface", size="2"),
            rx.heading("Contact", size="8", margin_top="10px"),
            rx.text(
                "Feel free to reach out for collaborations, inquiries, or just to say hi!",
                color="gray",
                text_align="center",
                max_width="600px",
            ),
            
            rx.vstack(
                contact_item(
                    "github", 
                    "Github", 
                    "Neural-Compile Repository", 
                    "https://github.com/naveen-rondla-2005/Neural-Compile",
                    "gray"
                ),
                contact_item(
                    "linkedin", 
                    "Linkedin", 
                    "Naveen Rondla", 
                    "https://www.linkedin.com/in/naveen-rondla/",
                    "blue"
                ),
                contact_item(
                    "mail", 
                    "Email", 
                    "naveenrondla@hotmail.com", 
                    "mailto:naveenrondla@hotmail.com",
                    "amber"
                ),
                width="100%",
                max_width="500px",
                spacing="4",
                margin_top="30px",
            ),
            
            width="100%",
            padding_top="60px",
            padding_bottom="100px",
            align="center",
            class_name="page-content",
        ),
        
        footer(),
        width="100%",
        min_height="100vh",
        background_color="var(--bg-color)",
    )
