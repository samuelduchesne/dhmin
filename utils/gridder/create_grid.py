import matplotlib.pyplot as plt
import numpy as np
from itertools import product as iter_product
from shapely.geometry import Point, LineString
from geopandas import GeoSeries, GeoDataFrame
from ..utils import pandashp as pdshp


def _gen_grid_edges(point_matrix):
    '''Connecting vertices in a chessboard manner'''
    lines = []
    for row in point_matrix:
        lines.extend([LineString(coords) for coords in zip(row[:-1], row[1:])])
    for row in np.transpose(point_matrix, (1, 0, 2)):
        lines.extend([LineString(coords) for coords in zip(row[:-1], row[1:])])

    return lines


def _check_input(origo_xy, num_edge_x, num_edge_y, dx, dy, noise_prop):
    if len(origo_xy) != 2 or not all([isinstance(c, (int, float)) for c in origo_xy]):
        raise TypeError('origo_xy has nan element(s)')
    if any([a < 1 for a in (num_edge_x, num_edge_y)]):
        raise ValueError('number of edges must be 1<')
    if any([a < 0 for a in (dx, dy, noise_prop)]):
        raise ValueError('dx, dy, noise_prop must be positive numbers')


def create_square_grid(origo_xy=(0, 0), num_edge_x=1, num_edge_y=None, dx=100, dy=None, noise_prop=0.0, epsg=32632):
    '''Create chessboard grid with edges and vertices
    
    Parameters
    ----------
    origo_xy : tuple, optional
        Charthesian coords from where the grid will be built
    num_edge_x : int, optional
        how many edges horizontally
    num_edge_y : None, optional
        How many edgey vertically
    dx : int, optional
        length of the horizontal edges (in meters)
    dy : None, optional
        length of the vertical edges (in meters)
    noise_prop : float, optional
        0.0 to MAX_NOISE < 1.0 effectively a relative missplacement radius
    epsg : 32632, optional
        The carthesian CRS in which the grid should be created,
        defaults to the UTM zone in which Munich is located

    Return : [vertices, edges] As GeoDataFrames
        vertices : [geometry, Vertex]
        edges : [geometry, Edge, Vertex1, Vertex2]
    '''
    # variable init
    MAX_NOISE = 0.45  # relative to dx dy
    xx, yy = origo_xy
    dy = dx if not dy else dy
    num_edge_y = num_edge_x if not num_edge_y else num_edge_y
    num_vert_x = num_edge_x + 1
    num_vert_y = num_edge_y + 1
    fuzz_radius_x = dx * noise_prop
    fuzz_radius_y = dy * noise_prop
    if noise_prop > MAX_NOISE:
        fuzz_radius_x = MAX_NOISE * dx
        fuzz_radius_y = MAX_NOISE * dy
    crstext = 'epsg:{}'.format(epsg)
    crsinit = {'init': crstext}

    _check_input(origo_xy, num_edge_x, num_edge_y, dx, dy, noise_prop)

    # generate offsetted point coordinates
    coords = []
    for ind, ori in enumerate(origo_xy):
        dc, num = (dx, num_vert_x) if ind == 0 else (dy, num_vert_y)
        coords.append([coo for coo in np.arange(ori, ori + (dc * num), dc)])
    coords_x, coords_y = coords
    points = [p for p in iter_product(coords_x, coords_y, repeat=1)]

    # Add fuzz
    if noise_prop > 0.0:
        def _fuzz(xy):
            return [xy[ii] + lim * (2 * np.random.rand() - 1)
                    for ii, lim in enumerate((fuzz_radius_x, fuzz_radius_y))]

        points = list(map(lambda xy: _fuzz(xy), points))

    # Create Shapely objects
    vertices = [Point(coo) for coo in points]
    point_matrix = np.array(points).reshape(num_vert_x, num_vert_y, 2)
    edges = _gen_grid_edges(point_matrix)

    # Create GeoDataFrames
    vdf = GeoDataFrame(geometry=vertices, crs=crsinit)
    vdf['Vertex'] = vdf.index
    vdf.set_index('Vertex')
    edf = GeoDataFrame(geometry=edges, crs=crsinit)
    edf['Edge'] = edf.index
    edf.set_index('Edge')
    pdshp.match_vertices_and_edges(vdf, edf)
    return (vdf, edf)


# Run Examples / Tests if script is executed directly
if __name__ == '__main__':
    test0ver, test0edg = create_square_grid(num_edge_x=6, noise_prop=0.0, epsg=32632)
    # test1ver, test1edg = create_square_grid(num_edge_x=6, noise_prop=0.1, epsg=32632)
    # test2ver, test2edg = create_square_grid(num_edge_x=6, noise_prop=0.2)
    # test3ver, test3edg = create_square_grid(num_edge_x=6, noise_prop=0.3)
    # test4ver, test4edg = create_square_grid(num_edge_x=6, noise_prop=0.4)
    # test5ver, test5edg = create_square_grid(num_edge_x=6, noise_prop=.45)

    fig, axes = plt.subplots(2, 3, figsize=(10, 6))
    for ij in iter_product(range(2), repeat=2):
        axes[ij].set_aspect('equal')
    test0ver.plot(ax=axes[0, 0], marker='o', color='red', markersize=5)
    test0edg.plot(ax=axes[0, 0], color='blue')
    # test1ver.plot(ax=axes[0, 1], marker='o', color='red', markersize=5)
    # test1edg.plot(ax=axes[0, 1], color='blue')
    # test2ver.plot(ax=axes[0, 2], marker='o', color='red', markersize=5)
    # test2edg.plot(ax=axes[0, 2], color='blue')
    # test3ver.plot(ax=axes[1, 0], marker='o', color='red', markersize=5)
    # test3edg.plot(ax=axes[1, 0], color='blue')
    # test4ver.plot(ax=axes[1, 1], marker='o', color='red', markersize=5)
    # test4edg.plot(ax=axes[1, 1], color='blue')
    # test5ver.plot(ax=axes[1, 2], marker='o', color='red', markersize=5)
    # test5edg.plot(ax=axes[1, 2], color='blue')
