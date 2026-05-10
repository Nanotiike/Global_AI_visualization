from dash import dcc, html, Input, Output, ctx
import plotly.graph_objects as go
import pandas as pd
from dotenv import load_dotenv
import os

from country_utils import get_missing_countries, CODE_TO_NAME
 
# Load data from .env
load_dotenv()
 
Data_Publications = pd.read_csv(os.getenv("PATH_TO_PUBLICATIONS"))
Data_Patents = pd.read_csv(os.getenv("PATH_TO_PATENTS"))
 
# Dataset config 
DATASETS = {
    "Number publications by country": {
        "data":     Data_Publications,
        "locations":    "Code", 
        "color":        "All", 
        "hover_name":   "Entity",
    },
    "Number of patents by country": {
        "data":         Data_Patents,
        "locations":    "Code", 
        "color":        "All", 
        "hover_name":   "Entity",
    },
}

DATASET_INFO = {
    "Number publications by country": "Country-level counts of AI-related journal articles, conference papers, working papers, and preprints (2015–2020). Covers only English-title/abstract publications; non-English and much Chinese research is excluded. A country is credited if at least one author is affiliated with an institution there.",
    "Number of patents by country": "Number of AI-related patent applications first filed in each country's patent office per year (2015–2020). Counts patent families (one invention = one entry regardless of multi-country filings). Filing location is used as a proxy for innovation activity, not inventor nationality."
}
 
 
DATASET_KEYS    = list(DATASETS.keys())
DEFAULT_DATASET = DATASET_KEYS[0]

# Button styles 
ACTIVE_STYLE = {
    "padding":         "6px 14px",
    "marginLeft":      "5px",
    "border":          "1px solid #3a7bd5",
    "borderRadius":    "4px",
    "cursor":          "pointer",
    "backgroundColor": "#3a7bd5",
    "color":           "white",
    "fontWeight":      "600",
    "fontSize":        "12px",
}
 
INACTIVE_STYLE = {
    "padding":         "6px 14px",
    "marginLeft":      "5px",
    "border":          "1px solid #cccccc",
    "borderRadius":    "4px",
    "cursor":          "pointer",
    "backgroundColor": "#f5f5f5",
    "color":           "#333333",
    "fontWeight":      "400",
    "fontSize":        "12px",
}
 
# Layout for this section.
publications_layout = html.Div(
    style={"width": "730px", "display": "inline-block",
           "marginRight": "30px", "position": "relative"},
    children=[
        dcc.Store(id="publications-selected-dataset", data=DEFAULT_DATASET),

        dcc.Graph(id="publications-graph", style={"height": "500px"}),

        html.Div(
            style={
                "display":        "flex",
                "justifyContent": "flex-end",
                "alignItems":     "center",
                "padding":        "6px 0px",
            },
            children=[
                html.Label("Datasets"),
                html.Div(
                    className="info-wrapper",
                    children=[
                        html.Span("ⓘ", className="info-icon"),
                        html.Span(
                            id="publications-info-tooltip",
                            className="info-tooltip-text",
                        ),
                    ],
                ),
            ] + [
                html.Button(
                    children=name,
                    id=f"publications-btn-{i}",
                    n_clicks=0,
                    style=ACTIVE_STYLE if name == DEFAULT_DATASET else INACTIVE_STYLE,
                )
                for i, name in enumerate(DATASET_KEYS)
            ],
        ),

        dcc.Slider(min=2015, max=2020, value=2020, id='timeline-publications')
    ],
)
 
 
# Callback. This is what connects to the main.py
def register_callbacks(app):
 
    @app.callback(
        Output("publications-graph",            "figure"),
        Output("publications-btn-0",            "style"),
        Output("publications-btn-1",            "style"),
        Output("publications-selected-dataset", "data"),
        Output("publications-info-tooltip", "children"),
        Input("publications-btn-0",             "n_clicks"),
        Input("publications-btn-1",             "n_clicks"),
        Input("publications-selected-dataset",  "data"),
        Input("timeline-publications",           "value"),
    )
    def update_publications_graph(b0, b1, stored_dataset, slider_value):
        triggered = ctx.triggered_id
 
        if triggered and triggered.startswith("publications-btn-"):
            index    = int(triggered.split("-")[-1])
            selected = DATASET_KEYS[index]
        else:
            selected = stored_dataset
        
        config = DATASETS[selected]
        df = config["data"]
        
        # Filter data by date range
        mask = (df["Year"]==slider_value)
        filtered_df = df[mask].copy()

        # Missing countries from data
        missing = get_missing_countries(df, slider_value)
        bins = [0, 100, 500, 5000, 25000, 70000]  # Upper bounds for each range
        labels = ["0-100", "100-500", "500-5000", "5000-25000", "25000+"]
        colors_list = ['#f7fbff', "#bbddfd", "#81bbf1", "#046aa1", "#0a2b42"]

        # Bin the data
        filtered_df['color_bin'] = pd.cut(
            filtered_df[config["color"]],
            bins=bins,
            labels=labels,
            right=False  # Left-inclusive ranges (0-100, 100-200, etc.)
        )

        # Create discrete colorscale with sharp transitions
        colorscale = []
        for i, color in enumerate(colors_list):
            position = i / len(colors_list)
            next_position = (i + 1) / len(colors_list)
            colorscale.append([position, color])
            colorscale.append([next_position, color])

        # Convert categories to numeric for plotting
        color_mapping = {label: i for i, label in enumerate(labels)}
        filtered_df['color_numeric'] = filtered_df['color_bin'].map(color_mapping)

        # Build the scatter figure
        fig = go.Figure()

        if missing:
            fig.add_trace(
                go.Choropleth(
                    locations=missing,
                    z=[0] * len(missing),
                    text=[CODE_TO_NAME.get(c, c) for c in missing],
                    colorscale=[[0, "#cccccc"], [1, "#cccccc"]],
                    showscale=False,
                    hovertemplate="%{text}: No data<extra></extra>",
                    marker_line_color="white",
                    marker_line_width=0.5,
                )
            )

        if selected=="Number publications by country":
            output = "Publications"
        else:
            output = "Patents"
        
        fig.add_trace(
            go.Choropleth(
                locations=filtered_df[config["locations"]],
                z=filtered_df['color_numeric'],
                colorscale=colorscale,
                text=filtered_df[config["hover_name"]],
                zmin=-0.5,
                zmax=len(labels)-0.5,
                customdata=filtered_df[config["color"]],
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    f"{output}"": %{customdata}<br>"
                    "<extra></extra>"
                ),
                colorbar=dict(
                    title="Range",
                    tickvals=[i for i in range(len(labels))],
                    ticktext=labels,
                ),
            )
        )
 
        fig.update_layout(
            title_text="Scholarly production",
            geo=dict(
                scope='world',
                projection_type='natural earth',
                showframe=False,
                showcoastlines=True,
                coastlinecolor="#cccccc",
                countrycolor="#cccccc",
                lataxis_range=[-90, 90],
                lonaxis_range=[-180, 180],
            ),
            dragmode='zoom',
        )

        button_styles = [
            ACTIVE_STYLE if DATASET_KEYS[i] == selected else INACTIVE_STYLE
            for i in range(2)
        ]

        tooltip_text = DATASET_INFO.get(selected, "")      
 
        return fig, *button_styles, selected, tooltip_text
