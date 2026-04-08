import os

import reflex as rx

config = rx.Config(
    app_name="JLPT_generator",
    api_url=os.getenv("API_URL") or "http://localhost:8000",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
)
