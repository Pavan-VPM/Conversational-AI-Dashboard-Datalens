


import dash
import requests

import pdfkit
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import pandas as pd
import base64
import io
import plotly.express as px
import plotly.graph_objects as go
import webbrowser
import threading
import nltk
import dash_bootstrap_components as dbc
import flask
from flask import render_template
from chatbot import get_gemini_response






server = flask.Flask(__name__)

# Create a Dash application

#app = dash.Dash(__name__, server=server, url_base_pathname='/dashboard/', suppress_callback_exceptions=True)

app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'])


# Route to serve the welcome HTML page
@app.server.route('/welcome')

def welcome():
    return render_template('welcome.html')





# Download NLTK data (tokenizers)
nltk.download('punkt')



# Global variable to hold the DataFrame
df = pd.DataFrame()


@server.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    # Retrieve form data
    x_axis = request.form.get('x_axis')
    y_axis = request.form.get('y_axis')
    graph_type = request.form.get('graph_type')

    # Prepare HTML content for PDF
    content_html = f"""
    <h1>Dataset Analysis</h1>
    <p>Selected X-axis: {x_axis}</p>
    <p>Selected Y-axis: {y_axis}</p>
    <p>Graph Type: {graph_type}</p>
    <p>Dataset Snapshot:</p>
    <p>Include your DataFrame snapshot or details here as needed.</p>
    """

    # Generate PDF from HTML content
    pdf = pdfkit.from_string(content_html, False)

    # Encode PDF content as base64
    pdf_base64 = base64.b64encode(pdf).decode()

    return pdf_base64





# Layout of the app
app.layout = html.Div([
    html.H1("Conversational AI Dashboard for Dataset Analysis"),

  dcc.Upload(
    id='upload-data',
    children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
    style={
        'width': '100%', 'height': '60px', 'lineHeight': '60px',
        'borderWidth': '1px', 'borderStyle': 'dashed',
        'borderRadius': '10px', 'textAlign': 'center', 'margin': '10px',
        'background-color': '#f8f9fa', 'cursor': 'pointer'
    },
    multiple=False,
    className='hover-shadow'
),



    # Message indicating successful upload
    html.Div(id='upload-message', style={'margin-top': '10px', 'color': 'green'}),

    # Div to show dataset details
    html.Div(id='dataset-details', style={'margin-top': '20px', 'font-weight': 'bold'}),

    # Dropdowns for selecting columns for X and Y axes
    dcc.Dropdown(id='x-axis', placeholder="Select X-axis"),
    dcc.Dropdown(id='y-axis', placeholder="Select Y-axis"),

    # Dropdown to select graph type
    dcc.Dropdown(
        id='graph-type',
        options=[
            {'label': 'Scatter Plot', 'value': 'scatter'},
            {'label': 'Line Chart', 'value': 'line'},
            {'label': 'Bar Chart', 'value': 'bar'},
            {'label': 'Histogram', 'value': 'histogram'},
            {'label': 'Box Plot', 'value': 'box'},
            {'label': 'Pie Chart', 'value': 'pie'}
        ],
        placeholder="Select Graph Type"
    ),

    # Input fields for X and Y axis scaling
    html.Div([
        html.Div("X-axis Scale:"),
        dcc.Input(id='x-scale-value', type='number', value=1, step=0.1, style={'width': '50px'}),
    ], style={'display': 'flex', 'align-items': 'center', 'margin': '10px'}),

    html.Div([
        html.Div("Y-axis Scale:"),
        dcc.Input(id='y-scale-value', type='number', value=1, step=0.1, style={'width': '50px'}),
    ], style={'display': 'flex', 'align-items': 'center', 'margin': '10px'}),

    # Div to show axis names before graph rendering
    html.Div(id='axis-names', style={'margin-top': '20px', 'font-weight': 'bold'}),

    # Graph to display the chosen type of plot
    dcc.Graph(id='graph-output'),

    # Input for user questions and chatbot response
    dcc.Input(id="user-question", type="text", placeholder="Ask a question about the dataset...", style={'width': '80%'}),
    html.Button('Submit', id='submit-question', n_clicks=0),
    html.Div(id='chat-output', style={'margin-top': '20px', 'font-weight': 'bold'}),

    # Button for PDF generation
    html.Button('Generate PDF', id='generate-pdf-button', n_clicks=0, style={'margin-top': '20px', 'width': '100%'}),

# Div to show the download link for the PDF
    html.Div(id='pdf-download-link')


])

# Callback to update the x-axis dropdown and show success message
@app.callback(
    [Output('x-axis', 'options'), Output('upload-message', 'children'), Output('dataset-details', 'children')],
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def update_x_axis_options(contents, filename):
    global df
    if contents is None:
        return [], "", ""
    
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    
    # Dataset details
    num_rows = df.shape[0]
    num_cols = df.shape[1]
    dataset_details = f"Dataset Name: {filename}\nNumber of Rows: {num_rows}\nNumber of Columns: {num_cols}"

    message = "Dataset uploaded successfully!"
    return [{'label': col, 'value': col} for col in df.columns], message, dataset_details

# Callback to update the y-axis dropdown
@app.callback(
    Output('y-axis', 'options'),
    Input('upload-data', 'contents')
)
def update_y_axis_options(contents):
    if contents is None:
        return []
    
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    return [{'label': col, 'value': col} for col in df.columns]

# Show selected axis names before rendering the graph
@app.callback(
    Output('axis-names', 'children'),
    Input('x-axis', 'value'),
    Input('y-axis', 'value')
)
def show_selected_axes(x_axis, y_axis):
    if x_axis and y_axis:
        return f"Selected X-axis: {x_axis}, Selected Y-axis: {y_axis}"
    return "Select both X-axis and Y-axis."

# Generate the graph with axis names and scale adjustments
@app.callback(
    Output('graph-output', 'figure'),
    Input('x-axis', 'value'),
    Input('y-axis', 'value'),
    Input('graph-type', 'value'),
    Input('upload-data', 'contents'),
    Input('x-scale-value', 'value'),
    Input('y-scale-value', 'value')
)
def update_graph(x_axis, y_axis, graph_type, contents, x_scale_value, y_scale_value):
    if contents:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        
        # Adjust the data based on scale_value if necessary
        if x_axis: df[x_axis] *= x_scale_value
        if y_axis: df[y_axis] *= y_scale_value

        # Generate the plot based on the selected graph type
        if graph_type == 'scatter':
            fig = px.scatter(df, x=x_axis, y=y_axis, title=f'Scatter Plot of {x_axis} vs {y_axis}')
        elif graph_type == 'line':
            fig = px.line(df, x=x_axis, y=y_axis, title=f'Line Chart of {x_axis} vs {y_axis}')
        elif graph_type == 'bar':
            fig = px.bar(df, x=x_axis, y=y_axis, title=f'Bar Chart of {x_axis} vs {y_axis}')
        elif graph_type == 'histogram':
            fig = px.histogram(df, x=x_axis, title=f'Histogram of {x_axis}')
        elif graph_type == 'box':
            fig = px.box(df, x=x_axis, y=y_axis, title=f'Box Plot of {x_axis} vs {y_axis}')
        elif graph_type == 'pie':
            fig = px.pie(df, names=x_axis, title=f'Pie Chart of {x_axis}')
        else:
            fig = go.Figure()

        # Update the axis titles
        fig.update_layout(
            xaxis_title=x_axis or "Default X-axis",
            yaxis_title=y_axis or "Default Y-axis"
        )

        return fig
    

    
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, 1, 2], y=[0, 1, 2], mode='lines'))
    fig.update_layout(
        title="Default Graph",
        xaxis_title="Default X-axis",
        yaxis_title="Default Y-axis"
    )
    return fig

# Callback to generate PDF link
@app.callback(
    Output('pdf-download-link', 'children'),
    Input('generate-pdf-button', 'n_clicks'),
    State('x-axis', 'value'),
    State('y-axis', 'value'),
    State('graph-type', 'value'),
)
def generate_and_display_pdf(n_clicks, x_axis, y_axis, graph_type):
    if n_clicks > 0 and x_axis and y_axis and graph_type:
        # Prepare form data for PDF generation
        form_data = {
            'x_axis': x_axis,
            'y_axis': y_axis,
            'graph_type': graph_type
        }

        # Generate PDF using requests
        response = requests.post('http://127.0.0.1:8050/generate_pdf', data=form_data)
        
        # Return link to download the generated PDF
        return html.A('Download PDF', href='data:application/pdf;base64,' + base64.b64encode(response.content).decode(), download='analysis.pdf', target='_blank')


# NLP-based query handler with dataset context
@app.callback(
    Output('chat-output', 'children'),
    Input('submit-question', 'n_clicks'),
    State('user-question', 'value')
)
def handle_question(n_clicks, user_question):
    if n_clicks == 0 or not user_question or df.empty:
        return "Please upload a dataset and ask a question."

    # Prepare dataset context to pass to the chatbot
    dataset_summary = df.describe(include='all').to_string()  # Summary statistics of the dataset

    # Call the Gemini chatbot with the user question and dataset context
    chatbot_response = get_gemini_response(user_question, dataset_context=dataset_summary)

    return chatbot_response


# Open the Dash app in the browser automatically
def open_browser():
    webbrowser.open_new("http://127.0.0.1:8050/welcome")

if __name__ == '__main__':
    threading.Timer(1, open_browser).start()  # Delay the browser opening
    app.run_server(debug=False)
