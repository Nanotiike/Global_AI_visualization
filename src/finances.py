from dash import dcc, html, Input, Output, ctx
import plotly.graph_objects as go
import pandas as pd
from dotenv import load_dotenv
import os

from country_utils import get_missing_countries, CODE_TO_NAME

# Load data from .env
load_dotenv()
 
Data_Ai_Systems = pd.read_csv(os.getenv("PATH_TO_AI_SYSTEMS"))
Data_Funding = pd.read_csv(os.getenv("PATH_TO_FUNDING"))
 
# Dataset config 
DATASETS = {
    "Number of large AI systems by country": {
        "data":     Data_Ai_Systems,
        "locations":    "Code", 
        "color":        "Cumulative number of large-scale AI systems by country", 
        "hover_name":   "Entity",
    },
    "External funding to AI companies by country": {
        "data":         Data_Funding,
        "locations":    "Code", 
        "color":        "All", 
        "hover_name":   "Entity",
    },
}

DATASET_INFO = {
    "Number of large AI systems by country": "Running total of compute-intensive AI models (requiring >10²³ FLOP to train, costing hundreds of thousands of dollars or more) attributed to each country by the primary institution of their authors. Data from Epoch AI, covering 2019–2024.",
    "External funding to AI companies by country": "Annual private investment into AI companies by country (2019–2024), covering venture capital, private equity, and M&A. Excludes publicly traded firms and internal R&D. ~40% of undisclosed deal values are estimated by CSET. Expressed in inflation-adjusted 2021 USD.",
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

def human_format(num, round_to=2):
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num = round(num / 1000.0, round_to)
    return '{:.{}f}{}'.format(num, round_to, ['', 'K', 'M', 'B', 'T', 'P'][magnitude])
 
# Layout for this section. Buttons first, then graph 
finances_layout = html.Div(
    style={"width": "730px", "display": "inline-block",
           "marginRight": "30px", "position": "relative"},
    children=[
        dcc.Store(id="finances-selected-dataset", data=DEFAULT_DATASET),
 
        dcc.Graph(id="finances-graph", style={"height": "500px"}),
        
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
                            id="finances-info-tooltip",
                            className="info-tooltip-text",
                        ),
                    ],
                ),
            ] + [
                html.Button(
                    children=name,
                    id=f"finances-btn-{i}",
                    n_clicks=0,
                    style=ACTIVE_STYLE if name == DEFAULT_DATASET else INACTIVE_STYLE,
                )
                for i, name in enumerate(DATASET_KEYS)
            ],
        ),

        dcc.Slider(min=2019, max=2024, value=2024, id='timeline-finances')
    ],
)
 
 
# Callback. This is what connects to the main.py
def register_callbacks(app):
 
    @app.callback(
        Output("finances-graph",            "figure"),
        Output("finances-btn-0",            "style"),
        Output("finances-btn-1",            "style"),
        Output("finances-selected-dataset", "data"),
        Output("finances-info-tooltip", "children"),
        Input("finances-btn-0",             "n_clicks"),
        Input("finances-btn-1",             "n_clicks"),
        Input("finances-selected-dataset",  "data"),
        Input("timeline-finances",           "value"),
    )
    def update_finances_graph(b0, b1, stored_dataset, slider_value):
        triggered = ctx.triggered_id
 
        if triggered and triggered.startswith("finances-btn-"):
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

        if selected=="Number of large AI systems by country":
            output = "Large AI systems"
            bins = [0, 5, 10, 20, 100, 500] 
            labels = ["0-5", "5-10", "10-20", "20-100", "100+"]
        else:
            output = "Funding for AI companies"
            bins = [0, 100000, 10000000, 1000000000, 15000000000, 1000000000000]
            labels = ["0-100K", "100K-1M", "1M-1B", "1B-15B", "15B+"]
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
 
        fig.add_trace(
            go.Choropleth(
                locations=filtered_df[config["locations"]],
                z=filtered_df['color_numeric'],
                colorscale=colorscale,
                text=filtered_df[config["hover_name"]],
                zmin=-0.5,
                zmax=len(labels)-0.5,
                customdata=filtered_df[config["color"]].apply(human_format),
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
            title_text="Finances",
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
