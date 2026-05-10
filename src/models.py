from dash import dcc, html, Input, Output, ctx
import plotly.graph_objects as go
import pandas as pd
from dotenv import load_dotenv
import os
from datetime import datetime
 
# Load data from .env
load_dotenv()
 
Data_Datapoints     = pd.read_csv(os.getenv("PATH_TO_DATAPOINTS"))
Data_Parameters     = pd.read_csv(os.getenv("PATH_TO_PARAMETERS"))
Data_Computation    = pd.read_csv(os.getenv("PATH_TO_COMPUTATION"))
Data_Hardware_Energy = pd.read_csv(os.getenv("PATH_TO_HARDWARE_AND_ENERGY"))
 
# Set min and max ranges for the slider
min_date = datetime(2015, 12, 2)
max_date = datetime(2025, 12, 31)

date_range = pd.date_range(start=min_date, end=max_date, freq='D')
 
# Dataset config
DATASETS = {
    "Hardware & Energy costs of training": {
        "data":     Data_Hardware_Energy,
        "x_col":    "Day",
        "y_col":    "Cost",
        "name_col": "Entity",
    },
    "Parameter Count of model": {
        "data":     Data_Parameters,
        "x_col":    "Day",
        "y_col":    "Number of parameters",
        "name_col": "Entity",
    },
    "Computation used to train": {
        "data":     Data_Computation,
        "x_col":    "Day",
        "y_col":    "Training computation (petaFLOP)",
        "name_col": "Entity",
    },
    "Datapoints used to train": {
        "data":     Data_Datapoints,
        "x_col":    "Day",
        "y_col":    "Training dataset size",
        "name_col": "Entity",
    },
}

DATASET_INFO = {
    "Hardware & Energy costs of training": "Estimated cost in inflation-adjusted 2023 USD to train individual notable AI models, covering hardware depreciation and electricity. Reflects only the final training run, not total development costs, which are typically much higher. Data from Epoch AI, covering end of 2015 to end of 2025.",
    "Parameter Count of model": "Total learnable weights in notable AI models over time. More parameters generally allow more complex pattern recognition but increase computational cost and risk of overfitting. Data from Epoch AI, covering end of 2015 to end of 2025.",
    "Computation used to train": "Training compute (in petaFLOP) for notable AI models. Estimates sourced from published literature; accurate within ~2×, or ~5× for undisclosed models like GPT-4. Data from Epoch AI, covering end of 2015 to end of 2025.",
    "Datapoints used to train": "The number of unique examples (images, words, game timesteps, etc.) used in the final training run of notable AI models. Data from Epoch AI, covering end of 2015 to end of 2025.",
}
 
DATASET_KEYS    = list(DATASETS.keys())
DEFAULT_DATASET = DATASET_KEYS[0]

VISUALIZATIONS = [
    "Scatter plot plain",
    "Scatter plot log"
]
DEFAULT_VISUALIZATION = VISUALIZATIONS[0]

for dataset in DATASETS.values():
    dataset["data"]["Day"] = pd.to_datetime(dataset["data"]["Day"])
 
 
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
model_layout = html.Div(
    style={"width": "730px", "display": "inline-block", "marginRight": "30px"},
    children=[
 
        dcc.Store(id="model-selected-dataset", data=DEFAULT_DATASET),
        dcc.Store(id="model-selected-visualization", data=DEFAULT_VISUALIZATION),
 
        dcc.Graph(id="model-graph", style={"height": "500px"}),
 
        html.Div(
            style={
                "display":        "flex",
                "justifyContent": "flex-end",
                "alignItems":     "center",
                "padding":        "6px 0px",
            },
            children=[
                html.Label("Visualizations"),
            ] + [
                html.Button(
                    children=name,
                    id=f"model-btn-vis-{i}",
                    n_clicks=0,
                    style=ACTIVE_STYLE if name == DEFAULT_VISUALIZATION else INACTIVE_STYLE,
                )
                for i, name in enumerate(VISUALIZATIONS)
            ],
        ),

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
                    className="info-wrapper",       # positions the tooltip relative to this div
                    children=[
                        html.Span("ⓘ", className="info-icon"),
                        html.Span(
                            id="model-info-tooltip",    # unique per module as before
                            className="info-tooltip-text",
                        ),
                    ],
                ),
            ] + [
                html.Button(
                    children=name,
                    id=f"model-btn-data-{i}",
                    n_clicks=0,
                    style=ACTIVE_STYLE if name == DEFAULT_DATASET else INACTIVE_STYLE,
                )
                for i, name in enumerate(DATASET_KEYS)
            ],
        ),

        dcc.RangeSlider(
            id='date-range-slider',
            min=0,
            max=len(date_range) - 1,
            step=1,
            value=[0, len(date_range)-1],
            marks={i: date_range[i].strftime('%Y') for i in range(0, len(date_range), 365*2)}, 
            dots=True,
            updatemode='drag',
            allowCross=False
        ),
    ],
)
 
# Callback. This is what connects to the main.py
def register_callbacks(app):
 
    @app.callback(
        Output("model-graph",            "figure"),
        Output("model-btn-data-0",       "style"),
        Output("model-btn-data-1",       "style"),
        Output("model-btn-data-2",       "style"),
        Output("model-btn-data-3",       "style"),
        Output("model-btn-vis-0",        "style"),
        Output("model-btn-vis-1",        "style"),
        Output("model-selected-dataset", "data"),
        Output("model-selected-visualization", "data"),
        Output("model-info-tooltip", "children"),
        Input("model-btn-data-0",        "n_clicks"),
        Input("model-btn-data-1",        "n_clicks"),
        Input("model-btn-data-2",        "n_clicks"),
        Input("model-btn-data-3",        "n_clicks"),
        Input("model-btn-vis-0",         "n_clicks"),
        Input("model-btn-vis-1",         "n_clicks"),
        Input("model-selected-dataset",  "data"),
        Input("model-selected-visualization", "data"),
        Input("date-range-slider",       "value"),
    )
    def update_model_graph(b0, b1, b2, b3, bv0, bv1, stored_dataset, stored_visualization, slider_value):
        triggered = ctx.triggered_id
 
        if triggered and triggered.startswith("model-btn-data-"):
            index    = int(triggered.split("-")[-1])
            selected_data = DATASET_KEYS[index]
        else:
            selected_data = stored_dataset
        
        if triggered and triggered.startswith("model-btn-vis-"):
            index    = int(triggered.split("-")[-1])
            selected_visualization = VISUALIZATIONS[index]
        else:
            selected_visualization = stored_visualization

        start_date = date_range[int(slider_value[0])]
        end_date = date_range[int(slider_value[1])]
        
        config = DATASETS[selected_data]
        df = config["data"]
        
        # Filter data by date range - THIS IS THE MAIN FIX
        mask = (df["Day"] >= start_date) & (df["Day"] <= end_date)
        filtered_df = df[mask].copy()
 
        # Build the scatter figure
        fig = go.Figure()
        
        fig.add_trace(
            go.Scatter(
                x=filtered_df[config["x_col"]],
                y=filtered_df[config["y_col"]],
                mode="markers",
                name=f"{selected_data}",
                text=filtered_df[config["name_col"]],
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "Date: %{x}<br>"
                    "Value: %{y:,.0f}<br>"
                    "<extra></extra>"
                ),
                marker=dict(size=7, opacity=0.8, color='blue'),
                cliponaxis=False,
            )
        )
        
        fig.update_layout(
            title=dict(text="Models", font=dict(size=16)),
            xaxis=dict(
                title=dict(text="Date", font=dict(size=13)),
                showgrid=True,
                gridcolor="#eeeeee",
            ),
            yaxis=dict(
                title=dict(text="", font=dict(size=13)),
                showgrid=True,
                gridcolor="#eeeeee",
                type="log" if selected_visualization == "Scatter plot log" else "linear",
            ),
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(t=50, r=10, b=50, l=60),
            hovermode="closest",
            showlegend=False,
        )
 
        button_styles_data = [
            ACTIVE_STYLE if DATASET_KEYS[i] == selected_data else INACTIVE_STYLE
            for i in range(4)
        ]

        button_styles_visualizations = [
            ACTIVE_STYLE if VISUALIZATIONS[i] == selected_visualization else INACTIVE_STYLE
            for i in range(2)
        ]

        tooltip_text = DATASET_INFO.get(selected_data, "")      

        return fig, *button_styles_data, *button_styles_visualizations, selected_data, selected_visualization, tooltip_text