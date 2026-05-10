from dash import dcc, html, Input, Output, ctx
import plotly.graph_objects as go
import pandas as pd
from dotenv import load_dotenv
import os

from country_utils import get_missing_countries, CODE_TO_NAME, ALL_COUNTRY_CODES

# Load data from .env
load_dotenv()

Data_Bills        = pd.read_csv(os.getenv("PATH_TO_BILLS"))
Data_Ai_Incidents = pd.read_csv(os.getenv("PATH_TO_AI_INCIDENTS"))
Data_Views        = pd.read_csv(os.getenv("PATH_TO_VIEWS"))

# Dataset config 
DATASETS = {
    "Bills related to AI passed into law since 2016": {
        "data":      Data_Bills,
        "locations": "Code",
        "color":     "Cumulative AI-related bills passed into law since 2016, as of 2024",
        "hover_name":"Entity",
    },
    "Global AI Incidents": {
        "data":  Data_Ai_Incidents,
        "x_col": "Year",
        "y_col": "Annual reported artificial intelligence incidents and controversies",
    },
    "Views concerning the future of AI": {
        "data":        Data_Views,
        "code_col":    "Code",
        "hover_name":  "Entity",
        "help_col":    "Mostly help",
        "harm_col":    "Mostly harm",
        "neither_col": "Neither",
        "no_resp_col": "No response",
        "no_op_col":   "No opinion or don't know",
    },
}

DATASET_INFO = {
    "Bills related to AI passed into law since 2016": "Tracks the total number of national laws mentioning \"artificial intelligence\" passed since 2016, across 116 countries and territories. Sourced from Stanford's AI Index Report (2025). Note: large omnibus bills with multiple AI provisions (e.g. the US NDAA) count as a single law.",
    "Global AI Incidents": "Yearly count of global AI-related ethical misuse cases, such as fatal accidents or wrongful arrests, logged in the AI Incident Database from 2012 to 2024. Based on public media reports, so true totals are likely higher than recorded.",
    "Views concerning the future of AI": "Public opinion survey data asking respondents across many countries: \"Will AI help or harm people in the next 20 years?\" Allows cross-country comparison of optimism vs. pessimism about AI's societal impact.",
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

# Layout for this section. Buttons first, then graph 
safety_layout = html.Div(
    style={"width": "730px", "display": "inline-block",
           "marginRight": "30px", "position": "relative"},
    children=[
        dcc.Store(id="safety-selected-dataset", data=DEFAULT_DATASET),

        dcc.Graph(id="safety-graph", style={"height": "500px"}),
        
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
                            id="safety-info-tooltip",
                            className="info-tooltip-text",
                        ),
                    ],
                ),
            ] + [
                html.Button(
                    children=name,
                    id=f"safety-btn-{i}",
                    n_clicks=0,
                    style=ACTIVE_STYLE if name == DEFAULT_DATASET else INACTIVE_STYLE,
                )
                for i, name in enumerate(DATASET_KEYS)
            ],
        ),
    ],
)

# Callback. This is what connects to the main.py
def register_callbacks(app):

    @app.callback(
        Output("safety-graph",            "figure"),
        Output("safety-btn-0",            "style"),
        Output("safety-btn-1",            "style"),
        Output("safety-btn-2",            "style"),
        Output("safety-selected-dataset", "data"),
        Output("safety-info-tooltip", "children"),
        Input("safety-btn-0",             "n_clicks"),
        Input("safety-btn-1",             "n_clicks"),
        Input("safety-btn-2",             "n_clicks"),
        Input("safety-selected-dataset",  "data"),
    )
    def update_safety_graph(b0, b1, b2, stored_dataset):

        triggered = ctx.triggered_id

        if triggered and triggered.startswith("safety-btn-"):
            index    = int(triggered.split("-")[-1])
            selected = DATASET_KEYS[index]
        else:
            selected = stored_dataset

        fig    = go.Figure()
        config = DATASETS[selected]

        if selected == "Bills related to AI passed into law since 2016" or selected == "Views concerning the future of AI":
            df=config["data"]

            if selected=="Bills related to AI passed into law since 2016":
                bins = [0, 1, 5, 10, 20, 40] 
                labels = ["0-1", "1-5", "5-10", "10-20", "20+"]
                missing = get_missing_countries(df, 2023)
                colors_list = ['#f7fbff', "#bbddfd", "#81bbf1", "#046aa1", "#0a2b42"]

                # Bin the data
                df['color_bin'] = pd.cut(
                    df[config["color"]],
                    bins=bins,
                    labels=labels,
                    right=False
                )
            else:
                mask = (df["Year"]==2021)
                df = df[mask].copy()

                bins = [-100, -1, 0, 1, 100, 1000]
                labels = ["(-100)-(-50)", "(-50)-0", "0-50", "50-100", "100+"]
                opinion_cols = [
                    config["help_col"], config["harm_col"],
                    config["neither_col"], config["no_resp_col"], config["no_op_col"],
                ]
                df[opinion_cols] = df[opinion_cols].fillna(0)

                df["score"] = df[config["help_col"]] - df[config["harm_col"]]

                missing = list(ALL_COUNTRY_CODES - set(df[config["code_col"]].dropna()))
                colors_list = ["#fd0000", "#fc8a8a", "#ffffff", "#82d3ff", "#0095ff"]

                # Bin the data
                df['color_bin'] = pd.cut(
                    df["score"],
                    bins=bins,
                    labels=labels,
                    right=False
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
            df['color_numeric'] = df['color_bin'].map(color_mapping)

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

            if selected == "Bills related to AI passed into law since 2016" :
                fig.add_trace(
                    go.Choropleth(
                        locations=df[config["locations"]],
                        z=df['color_numeric'],
                        colorscale=colorscale,
                        text=df[config["hover_name"]],
                        zmin=-0.5,
                        zmax=len(labels)-0.5,
                        customdata=df[config["color"]],
                        hovertemplate=(
                            "<b>%{text}</b><br>"
                            "Bills related to AI:: %{customdata}<br>"
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
                    title_text="Safety",
                    geo=dict(
                        scope="world",
                        projection_type="natural earth",
                        showframe=False,
                        showcoastlines=True,
                        coastlinecolor="#cccccc",
                        countrycolor="#cccccc",
                        lataxis_range=[-90, 90],
                        lonaxis_range=[-180, 180],
                    ),
                    dragmode="zoom",
                )
                
            elif selected == "Views concerning the future of AI":

                hover_text = (
                    "Mostly help: "               + df[config["help_col"]].round(1).astype(str)    + "%<br>"
                    + "Neither: "                 + df[config["neither_col"]].round(1).astype(str) + "%<br>"
                    + "No response: "             + df[config["no_resp_col"]].round(1).astype(str) + "%<br>"
                    + "No opinion or don't know: "+ df[config["no_op_col"]].round(1).astype(str)   + "%<br>"
                    + "Mostly harm: "             + df[config["harm_col"]].round(1).astype(str)    + "%"
                )

                fig.add_trace(
                    go.Choropleth(
                        locations=df[config["code_col"]],
                        z=df["score"],
                        text=df[config["hover_name"]],
                        customdata=hover_text,
                        colorscale="RdBu",
                        zmin=-100,
                        zmid=0,
                        zmax=100,
                        hovertemplate=(
                            "<b>%{text}</b><br>"
                            "%{customdata}"
                            "<extra></extra>"
                        ),
                        marker_line_color="white",
                        marker_line_width=0.5,
                        colorbar=dict(
                            title=dict(text="← Harm / Help →", side="right"),
                            tickvals=[-100, -50, 0, 50, 100],
                            ticktext=["-100", "-50", "0", "50", "100"],
                        ),
                    )
                )

                fig.update_layout(
                    title_text="Safety",
                    geo=dict(
                        scope="world",
                        projection_type="natural earth",
                        showframe=False,
                        showcoastlines=True,
                        coastlinecolor="#cccccc",
                        countrycolor="#cccccc",
                        lataxis_range=[-90, 90],
                        lonaxis_range=[-180, 180],
                    ),
                    dragmode="zoom",
                )


        else:
            df = config["data"]

            fig.add_trace(
                go.Bar(
                    x=df[config["x_col"]],
                    y=df[config["y_col"]],
                    hovertemplate=(
                        "AI incidents: %{y}<br>"
                        "<extra></extra>"
                    ),
                )
            )

            fig.update_layout(
                title_text="Safety",
                xaxis=dict(
                    title=dict(text="Year", font=dict(size=13)),
                    showgrid=True,
                    gridcolor="#eeeeee",
                ),
                yaxis=dict(
                    title=dict(text="AI Incidents", font=dict(size=13)),
                    showgrid=True,
                    gridcolor="#1f77b4",
                    gridwidth=1,
                ),
                plot_bgcolor="white",
                paper_bgcolor="white",
                margin=dict(t=50, r=10, b=50, l=60),
                hovermode="closest",
                showlegend=False,
            )

        button_styles = [
            ACTIVE_STYLE if DATASET_KEYS[i] == selected else INACTIVE_STYLE
            for i in range(3)
        ]

        tooltip_text = DATASET_INFO.get(selected, "") 

        return fig, *button_styles, selected, tooltip_text