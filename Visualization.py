import os
import json
import geopandas as gpd
import pandas as pd
import time

from bokeh.plotting import figure, save, curdoc
from bokeh.models import ColumnDataSource, HoverTool, LogColorMapper, Circle, MultiLine, NodesAndLinkedEdges
from bokeh.models.widgets import Button
from bokeh.models.graphs import from_networkx
from bokeh.layouts import column, row
from bokeh.palettes import BuPu9, PuBuGn9, Viridis11, Plasma11
gpalette = npalette = Viridis11
gpalette = gpalette[-1::-1]
# npalette.reverse()

# Read amount of each destinated province
with open(os.path.join(os.getcwd(), "province-count.json"), 'r') as fp:
    province_count = json.load(fp)

with open(os.path.join(os.getcwd(), "province-paths.json"), 'r') as fp:
    province_paths = json.load(fp)

# Create the color mapper
color_mapper = LogColorMapper(palette=gpalette)

# Read Thailand shapefile
grid_fp = os.path.join(os.getcwd(), "thai-provinces",
                       "tha_admbnda_adm1_rtsd_20190221.shp")

# Read files
grid = gpd.read_file(grid_fp, driver="shapefile")
grid["geometry"] = grid["geometry"].apply(
    lambda x: list(x) if "Multi" in str(type(x)) else x)
grid = grid.set_index(['ADM1_EN'])['geometry'].apply(
    pd.Series).stack().reset_index()  # Expanding list to rows
grid.drop("level_1", axis=1, inplace=True)
grid.rename(columns={'ADM1_EN': 'name', 0: 'geometry'}, inplace=True)


def getPolyCoords(row, geom, coord_type):
    """Returns the coordinates ('x' or 'y') of edges of a Polygon exterior"""

    # Parse the exterior of the coordinate
    exterior = row[geom].exterior

    if coord_type == 'x':
        # Get the x coordinates of the exterior
        return list(exterior.coords.xy[0])
    elif coord_type == 'y':
        # Get the y coordinates of the exterior
        return list(exterior.coords.xy[1])


# Get the Polygon x and y coordinates
grid['x'] = grid.apply(getPolyCoords, geom='geometry', coord_type='x', axis=1)
grid['y'] = grid.apply(getPolyCoords, geom='geometry', coord_type='y', axis=1)
grid['amount'] = grid["name"].apply(
    lambda x: province_count[x] if x in province_count else 0)

# Make a copy, drop the geometry column and create ColumnDataSource
g_df = grid.drop('geometry', axis=1).copy()
gsource = ColumnDataSource(g_df)

# Initialize main figure
tools = "pan, wheel_zoom, box_zoom, reset, tap, save"
main_plot = figure(title="Thailand Map", plot_width=480, plot_height=800,
                   tooltips=[("Name", "@name"), ("Amount", "@amount")],
                   tools=tools)


def gcallback(attr, old, new):
    global bokeh_graph, ngraph, side_plot
    selected_province = gsource.data['name'][gsource.selected.indices[0]]

    # Update main plot
    def loadProvincePath(x):
        if ("Bangkok" in x) or (selected_province in x):
            maximum = max(
                province_paths[selected_province], key=province_paths[selected_province].get)
            return province_paths[selected_province][maximum]
        elif x in province_paths[selected_province]:
            return province_paths[selected_province][x]
        else:
            return 0
    gsource.data['amount'] = list(grid["name"].apply(loadProvincePath))

    # Update side plot
    for prov, graph in bokeh_graph.items():
        if selected_province in prov:
            # Set node hover
            node_hover_tool = HoverTool(renderers=[graph], tooltips=[
                                        ("Province", "@index"), ("Degree", "@degree")])
            side_plot.add_tools(node_hover_tool)
            graph.node_renderer.visible = True
            graph.edge_renderer.visible = True

        else:
            graph.node_renderer.visible = False
            graph.edge_renderer.visible = False


# Plot grid
pglyph = main_plot.patches('x', 'y', source=gsource,
                           fill_color={'field': 'amount',
                                       'transform': color_mapper},
                           fill_alpha=1.0, line_color="black", line_width=0.05, hover_color="pink", hover_alpha=0.8)
pglyph.nonselection_glyph = None

# Add callback when grid is selected
gsource.selected.on_change('indices', gcallback)

# Network Graph -------------------------------------------------
import networkx as nx

# Initialize side figure
side_plot = figure(title="Travel Network", x_range=(
    97, 106), y_range=(5, 21), plot_width=480, plot_height=800)

# Plot Thailand map layout
spglyph = side_plot.patches('x', 'y', source=gsource, fill_color=None,
                            line_color="black", line_width=0.5, line_alpha=0.5)
spglyph.nonselection_glyph = None

read_province = pd.read_csv(os.path.join(os.getcwd(), "thai-provinces", "thai-provinces_point.csv"))
provinces = list(read_province["province_EN"])


# Initialize graph for each province
graph_dict = dict()
for province in provinces:
    graph_dict[province] = nx.Graph(name=province)

# Build graph (nodes & edges)
paths_folder = os.path.join(os.getcwd(), "DA_OD", "Paths")
for path_file in os.listdir(paths_folder):
    print(path_file)
    with open(os.path.join(paths_folder, path_file), 'r') as fp:
        paths = json.load(fp)
    for _id, id_path in paths.items():
        for province in provinces:
            if "Bangkok" in province:
                continue
            try:
                pathToProv = id_path[:id_path.index(province)+1]
                pathToProv = [
                    prov for prov in pathToProv if str(prov) != 'nan']
                graph_dict[province].add_edges_from(
                    [(pathToProv[x], pathToProv[x+1]) for x in range(len(pathToProv)-1)])
            except:
                pass

# Read thai provinces coordination file
prov_info = pd.read_csv(os.path.join(
    os.getcwd(), "thai-provinces", "thai-provinces_point.csv"), index_col=1)
prov_info = prov_info.to_dict()

# Create network glyph for each graph
bokeh_graph = dict()
for prov in provinces:

    if "Bangkok" in prov:
        continue

    graph = graph_dict[prov]

    # Add extra attributes to nodes for display in a hover
    nx.set_node_attributes(
        graph, {k: v for k, v in dict(graph.degree).items()}, "degree")
    nx.set_node_attributes(
        graph, {k: v for k, v in dict(graph.degree).items()}, "size")
    nx.set_node_attributes(graph, prov_info["lat"], "lat")
    nx.set_node_attributes(graph, prov_info["lon"], "lon")

    # Create ColumnDataSource for glyph
    nsource = ColumnDataSource(pd.DataFrame.from_dict(
        {k: v for k, v in graph.nodes(data=True)}, orient='index'))

    # Color mapper
    color_mapper = LogColorMapper(palette=npalette)

    # Graph renderer using nx
    ngraph = from_networkx(graph, {k: v for k, v in zip(
        nsource.data['index'], zip(nsource.data['lon'], nsource.data['lat']))})

    # Style node
    ngraph.node_renderer.data_source.data.update(
        nsource.data)  # Tell glyph to use our source
    ngraph.node_renderer.glyph = Circle(size='size', line_width=0.5, fill_color={
                                        'field': 'degree', 'transform': color_mapper})

    # Style edge
    ngraph.edge_renderer.glyph = MultiLine(line_alpha=1, line_width=0.5)

    # Set default visibility
    ngraph.node_renderer.visible = False
    ngraph.edge_renderer.visible = False

    # Add glyph to side plot
    side_plot.renderers.append(ngraph)

    # Collect each province glyph(graph) for the use in a callback function
    bokeh_graph[prov] = ngraph

curdoc().add_root(row([main_plot, side_plot]))

# Reset button


def bcallback():
    # Reset main plot
    gsource.data['amount'] = list(grid["name"].apply(
        lambda x: province_count[x] if x in province_count else 0))

    # Reset side plot
    for index, graph in bokeh_graph.items():
        graph.node_renderer.visible = False
        graph.edge_renderer.visible = False


button = Button(label="Reset", button_type='success', width=100)
button.on_click(bcallback)
curdoc().add_root(button)
