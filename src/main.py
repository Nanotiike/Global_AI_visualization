from dash import Dash, dcc, html

import models
import publications
import finances
import safety

# Start the app
app = Dash(__name__)

models.register_callbacks(app)
publications.register_callbacks(app)
finances.register_callbacks(app)
safety.register_callbacks(app)

app.layout = html.Div([
    html.Div(
        className="app-banner",
        children=[
            html.H1("OVERVIEW OF GLOBAL AI SITUATION", className="banner-title"),
            html.P(
                """This visualization is meant to bring general awareness of the global AI situation. The visualization is split into four sections:
                
                Scholarly publications, which looks at the countries scientific contributions towards AI. This includes the publications and patents related to AI that the country has produced.
                Finances, which looks at the countries financial strength in AI. This includes the number of large AI systems in the country, as well as the external funding recieved by AI companies.
                Models, which looks at the various models made and how much it took to train them, computationally, datapoint wise, as well as hardware and energy cost wise.
                Safety, which looks at the safety side of AI, how many bills relate to it, how many incidents there have been because of AI, as well as the views people have on how helpful and harmful it might be.""",
                className="banner-intro",
            ),
            html.P(
                """The use of the visualization is simple. There are multiple datasets you can choose from at the bottom of each visualization. The datasets have a tooltip on the left which shows more information about the currently chosen dataset when you hover over it. The models section also includes two types of visualizations to choose from. You can freeky zoom and pan the maps around. With the scatter plots you can zoom by default, but can also choose to pan or do other actions by clicking on the choices that appear in the top left. You can always reset the visualization by pressing the options at the bottom of the visualization. """,
                className="banner-intro",
            ),
        ],
    ),
    html.Div(
        className="app-body",
        children=[

            html.Div(className="panel-box", children=[
                publications.publications_layout,
            ]),

            html.Div(className="panel-box", children=[
                finances.finances_layout,
            ]),

            html.Div(className="panel-box", children=[
                models.model_layout,
            ]),

            html.Div(className="panel-box", children=[
                safety.safety_layout,
            ]),

        ],
    ),

])


if __name__ == "__main__":
    app.run(debug=True)