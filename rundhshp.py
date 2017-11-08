import os
import dhmin
import dhmintools
import geopandas
import pyomo.environ
from pyomo.opt.base import SolverFactory

# config
base_directory = os.path.join('data', 'angusplant')
building_shapefile = os.path.join(base_directory, 'building')
edge_file = os.path.join(base_directory, 'edge')
vertex_file = os.path.join(base_directory, 'vertex')
params = {}  # only specify changed values
timesteps = [(155, 0.543), (616, 0.281), (1386, 0.158), (2618, 0.096),
             (2703, 0.035)]  # list of (duration [hours], scaling_factor) tuples
# annual fullLoad hours = sum(t, duration[t]*sf[t]) = 1800

# read vertices and edges from shapefiles...
vertex = geopandas.read_file(vertex_file + '.shp')
edge = geopandas.read_file(edge_file + '.shp')

# ... and set indices to agree with Excel format
vertex.set_index(['Vertex'], inplace=True)
edge.set_index(['Edge', 'Vertex1', 'Vertex2'], inplace=True)

# at this point, rundh.py and rundhshp.py work identically!
# dhmin.create_model must not rely on vertex/edge DataFrames to contain any
# geometry information

# get model
# create instance
# solver interface (Gurobi)
prob = dhmin.create_model(vertex, edge, params, timesteps)
prob.write('prob.lp', io_options={'symbolic_solver_labels': True})

solver = SolverFactory('gurobi')
result = solver.solve(prob, tee=True)
prob.solutions.load_from(result)

# create result directory if not existing already
result_dir = os.path.join('result', os.path.basename(base_directory))
if not os.path.exists(result_dir):
    os.makedirs(result_dir)

# use special-purpose function to plot power flows (works unchanged!)
dhmintools.plot_flows_min(prob)

# read time-independent variable values to DataFrame
# (list all variables using dhmin.list_entities(instance, 'variables')
caps = dhmin.get_entities(prob, ['Pmax', 'x'])
costs = dhmin.get_entity(prob, 'costs')
print(costs)

# remove Edge from index, so that edge and caps are both indexed on
# (vertex, vertex) tuples, i.e. their indices match for identical edges
edge.reset_index('Edge', inplace=True)

# change index names to 'Vertex1', 'Vertex2' from auto-inferred labels 
# 'vertex','vertex_'
caps.index.names = edge.index.names.copy()

# join optimal capacities with edge for geometry
edge_w_caps = edge.join(caps, lsuffix='Pmax')
edge_w_caps.to_file('result/angus/edge_w_caps.shp')

# Create plots
dhmintools.plot(prob, 'Pin', plot_demand=True, buildings=(building_shapefile, True), result_dir=result_dir)

# Save problem to file
rivus.save(prob, os.path.join(result_dir, 'prob.pgz'))
