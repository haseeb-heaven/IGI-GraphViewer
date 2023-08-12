"""
This is Project IGI Graph Generator GUI which generate the 3D graph of the game using the graph data file.
This also has the option to export the graph data to JSON file.
This is wriiten in Streamlit framework which is used to create the web app.
date : 12-08-2023
author : HeavenHM
"""

import os
import streamlit as st
import plotly.graph_objects as go
import json
import logging
from graph_data_parser import select_file
from graph_const import material_colors, material_mapping
import tempfile
import pandas as pd

logging.basicConfig(filename='graph_gen_app.log', level=logging.DEBUG)

def get_edges(data):
    edge_x = []
    edge_y = []
    edge_z = []
    for item in data:
        if "edges" in item:
            for edge in item["edges"]:
                target_node = next((node for node in data if node["id"] == edge), None)
                if target_node:
                    edge_x.extend([item["x"], target_node["x"], None])
                    edge_y.extend([item["y"], target_node["y"], None])
                    edge_z.extend([item["z"], target_node["z"], None])
    return edge_x, edge_y, edge_z

def prepare_node_colors_and_sizes(data, node_radius_size):
    colors = []
    sizes = []
    for item in data:
        material = item['material']
        color = material_colors.get(material_mapping.get(material, 'UNKNOWN'), 'purple')
        colors.append(color)
        sizes.append(item['radius'] * node_radius_size)
    return colors, sizes

def prepare_hover_text(data, show_links, show_material, show_gamma_radius, show_criteria):
    text_data = []
    for item in data:
        text = f"Node ID: {item['id']}"
        if show_links:
            text += f"<br>Links: {', '.join(map(str, item['edges']))}"
        if show_material:
            text += f"<br>Material: {item['material']}"
        if show_gamma_radius:
            text += f"<br>Gamma: {item['gamma']}<br>Radius: {item['radius']}"
        if show_criteria:
            text += f"<br>Criteria: {item['criteria']}"
        text_data.append(text)
    return text_data

def plot_3d(data, plot_type='scatter', symbol=None, show_links=False, show_material=False, show_gamma_radius=False, show_criteria=False, node_radius_size=50):
    logging.info(f"Generating 3D {plot_type} plot")
    x_data = [item['x'] for item in data]
    y_data = [item['y'] for item in data]
    z_data = [item['z'] for item in data]
    
    # Get edges only if show_links is True
    edge_x, edge_y, edge_z = get_edges(data) if show_links else ([], [], [])
    
    hover_texts = prepare_hover_text(data, show_links, show_material, show_gamma_radius, show_criteria)
    colors, sizes = prepare_node_colors_and_sizes(data, node_radius_size)
    
    fig = go.Figure()
    fig.update_layout(scene=dict(xaxis=dict(title=dict(text='X')), yaxis=dict(title=dict(text='Y')), zaxis=dict(title=dict(text='Z'))))
    #fig.layout.scene.aspectmode = 'cube' # Make the plot aspect ratio 1:1:1
    fig.layout.scene.aspectmode = 'data' # Make the plot scalt to data along the axes
    fig.layout.width = 800
    fig.layout.height = 600
    
    if plot_type == 'scatter':
        fig.add_trace(go.Scatter3d(x=x_data, y=y_data, z=z_data, mode='markers', marker=dict(color=colors, size=sizes, symbol=symbol, sizemode='diameter'), text=hover_texts, hoverinfo='text'))
    elif plot_type == 'surface':
        fig.add_trace(go.Scatter3d(x=x_data, y=y_data, z=z_data, mode='markers', marker=dict(color=colors, size=sizes, sizemode='diameter'), text=hover_texts, hoverinfo='text'))
    elif plot_type == 'line':
        fig.add_trace(go.Scatter3d(x=x_data, y=y_data, z=z_data, mode='lines+markers', marker=dict(color=colors, size=sizes, sizemode='diameter'), line=dict(color='red'), text=hover_texts, hoverinfo='text'))
    elif plot_type == 'mesh':
        intensity = list(range(len(colors)))
        fig.add_trace(go.Mesh3d(x=x_data, y=y_data, z=z_data, opacity=0.5, hoverinfo='text', hovertext=hover_texts, intensity=intensity, colorscale='Viridis', cmin=0, cmax=len(colors)-1))
        fig.add_trace(go.Scatter3d(x=x_data, y=y_data, z=z_data, mode='markers', marker=dict(color=colors, size=sizes, sizemode='diameter'), text=hover_texts, hoverinfo='text'))
    else:
        logging.error(f"Invalid plot type: {plot_type}")
        return

    # Add edges only if show_links is True
    if show_links:
        fig.add_trace(go.Scatter3d(x=edge_x, y=edge_y, z=edge_z, mode='lines', line=dict(color='red')))
    
    # Embed the Plotly graph in the Streamlit app
    st.plotly_chart(fig)

    logging.info(f"3D {plot_type} plot generated successfully")



def adjust_node_height_data(data, node_height):
    if not node_height:
        for item in data:
            item["z"] = 0  # Set Z position to 0 or any other default value
    return data

def main():
    st.title('IGI 3D Graph Generator - HM')

    # Initialize session state variables if they don't exist
    if 'show_links' not in st.session_state:
        st.session_state.show_links = False
    if 'show_material' not in st.session_state:
        st.session_state.show_material = False
    if 'show_gamma_radius' not in st.session_state:
        st.session_state.show_gamma_radius = False
    if 'show_criteria' not in st.session_state:
        st.session_state.show_criteria = False
    if 'show_table_data' not in st.session_state:
        st.session_state.show_table_data = False
    if 'node_height' not in st.session_state:
        st.session_state.node_height = False
    if 'node_radius_size' not in st.session_state:
        st.session_state.node_radius_size = 50
    if 'graph_type' not in st.session_state:
        st.session_state.graph_type = '3D Scatter'
    if 'node_symbol' not in st.session_state:
        st.session_state.node_symbol = 'circle'

    st.sidebar.header('IGI 3D Graph Generator')
    st.sidebar.markdown('This is Project IGI Graph Generator GUI which generate the 3D graph of the game using the graph data file.')

    # Sidebar settings
    with st.sidebar.expander('Settings',expanded=True):
        st.header('Settings')
        st.session_state.show_links = st.checkbox('Node Links', st.session_state.show_links)
        st.session_state.show_material = st.checkbox('Node Material', st.session_state.show_material)
        st.session_state.show_gamma_radius = st.checkbox('Node Gamma/Radius', st.session_state.show_gamma_radius)
        st.session_state.show_criteria = st.checkbox('Node Criteria', st.session_state.show_criteria)
        st.session_state.show_table_data = st.checkbox('Table View', st.session_state.show_table_data)
        st.session_state.node_height = st.checkbox('Node Height', st.session_state.node_height)
        st.session_state.node_radius_size = st.slider("Node Radius Size:", 10, 100, st.session_state.node_radius_size)
        st.session_state.graph_type = st.selectbox('Graph Type', ['3D Scatter', '3D Surface', '3D Line', '3D Mesh'], index=['3D Scatter', '3D Surface', '3D Line', '3D Mesh'].index(st.session_state.graph_type))
        st.session_state.node_symbol = st.selectbox('Node Symbol', ['circle', 'circle-open', 'cross', 'diamond', 'diamond-open', 'square', 'square-open', 'x'], index=['circle', 'circle-open', 'cross', 'diamond', 'diamond-open', 'square', 'square-open', 'x'].index(st.session_state.node_symbol))
        
    uploaded_file = st.file_uploader('Upload Graph File', type=['dat'])

    if uploaded_file:
        # Save the uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(uploaded_file.getvalue())
            uploaded_path = temp_file.name

        try:
            json_data = select_file(uploaded_path)
            if not json_data:
                st.error("Failed to parse the uploaded file.")
            else:
                # Adjust data based on user's input
                data = json.loads(json_data)
                data = adjust_node_height_data(data, st.session_state.node_height)

                # Display the data in a table if the checkbox is checked
                if st.session_state.show_table_data:
                    df = pd.DataFrame(data)
                    st.subheader('Graph Data')
                    st.dataframe(df)

                # Automatically generate the graph when any of the settings change
                if st.session_state.graph_type == "3D Scatter":
                    plot_3d(data, plot_type='scatter', symbol=st.session_state.node_symbol, show_links=st.session_state.show_links, show_material=st.session_state.show_material, show_gamma_radius=st.session_state.show_gamma_radius, show_criteria=st.session_state.show_criteria, node_radius_size=st.session_state.node_radius_size)
                elif st.session_state.graph_type == "3D Surface":
                    plot_3d(data, plot_type='surface', symbol=st.session_state.node_symbol, show_links=st.session_state.show_links, show_material=st.session_state.show_material, show_gamma_radius=st.session_state.show_gamma_radius, show_criteria=st.session_state.show_criteria, node_radius_size=st.session_state.node_radius_size)
                elif st.session_state.graph_type == "3D Line":
                    plot_3d(data, plot_type='line', symbol=st.session_state.node_symbol, show_links=st.session_state.show_links, show_material=st.session_state.show_material, show_gamma_radius=st.session_state.show_gamma_radius, show_criteria=st.session_state.show_criteria, node_radius_size=st.session_state.node_radius_size)
                elif st.session_state.graph_type == "3D Mesh":
                    plot_3d(data, plot_type='mesh', symbol=st.session_state.node_symbol, show_links=st.session_state.show_links, show_material=st.session_state.show_material, show_gamma_radius=st.session_state.show_gamma_radius, show_criteria=st.session_state.show_criteria, node_radius_size=st.session_state.node_radius_size)
        finally:
            # Clean up the temporary file
            os.remove(uploaded_path)
    else:
        st.info('Upload a graph file to generate a graph.')

if __name__ == "__main__":
    main()
