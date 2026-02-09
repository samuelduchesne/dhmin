import pyomo.environ  # noqa: F401 (registers solvers)
from pyomo.opt.base import SolverFactory

import dhmin
from dhmin import utils

# config
data_file = "mnl.xlsx"
params = {"r_heat": 0.07}  # only specify changed values
timesteps = [
    (1600, 0.8),
    (1040, 0.5),
]  # list of (duration [hours], scaling_factor) tuples
# annual fulload hours = sum(t, duration[t]*sf[t]) = 1800


# read vertices and edges from Excel data_file
data = dhmin.read_excel(data_file)
vertex, edge = data["Vertex"], data["Edge"]

# get model
# create instance
# solver interface (GLPK)
edge = edge.reset_index("Edge")
vertex["c_heatvar"] = 0.010
vertex["c_heatfix"] = 0
prob = dhmin.create_model(vertex, edge, params, timesteps)
optim = SolverFactory("glpk")
prob.write("rundh.lp", io_options={"symbolic_solver_labels": True})
result = optim.solve(prob, timelimit=30, tee=True)
prob.solutions.load_from(result)

# use special-purpose function to plot power flows
utils.plot_flows_min(prob)
