'''
Created on 15.10.2021

@author: larsw
'''
from control.osmparser import OSMParser
import numpy as np
from pprint import pprint
import mathcollection as mc
from multiprocessing import Pool
import datetime as dt
import matplotlib.pyplot as plt
from copy import deepcopy

def coords_dict_to_meters_dict (coords_dict):
    meters_dict = {}
    
    for k in coords_dict:
        coords = coords_dict[k]
        
        if len(coords.shape) == 2:
            lat_radians = coords[:,0] * np.pi / 180
            coords[:,0] *= 111120.0
            coords[:,1] *= 111120.0 * np.cos(lat_radians)
            meters_dict[k] = coords
        else:
            lat_radians = coords[0] * np.pi / 180
            coords[0] *= 111120.0
            coords[1] *= 111120.0 * np.cos(lat_radians)
            meters_dict[k] = coords
        
    return meters_dict

def get_normalization_root (meters_dict):
    root = np.min([
            np.min(meters_dict[k], axis=0)
            for k in meters_dict
            if len(meters_dict[k]) != 0
        ], axis=0)
    return root

def normalize_meters_dict (meters_dict, root):
    meters_dict = {
            k : meters_dict[k] - root
            for k in meters_dict
        }
    return meters_dict




class DataCollection ():
    def __init__ (self, highways, villages, highways_coords, villages_coords,
                  graph_points, graph_adjlist, weight_adjlist,
                  village_route_points):
        self.highways = highways
        self.villages = villages
        
        self.highways_coords = highways_coords
        self.villages_coords = villages_coords
        
        self.graph_points = graph_points
        self.graph_adjlist = graph_adjlist
        self.weight_adjlist = weight_adjlist
        
        self.village_route_points = village_route_points

def identify_village_closest_points (graph_points, village_coords):
    graph_point_ids = list(graph_points.keys())
    graph_points_np = np.array([
            graph_points[x]
            for x in graph_point_ids
        ])
    
    closest_points = {}
    
    for village_id in village_coords:
        village_point = village_coords[village_id]
        
        distances = graph_points_np - village_point
        distances = np.sqrt(distances[:,0] ** 2 + distances[:,1] ** 2)
        smallest = np.argmin(distances)
        closest_points[village_id] = graph_point_ids[smallest]
        
    return closest_points

def get_weight_adjlist (points, adjlist):
    weight_adjlist = {}
    
    for point_id in adjlist:
        adjs = adjlist[point_id]
        p1 = points[point_id]
        
        for adj_id in adjs:
            tup1 = (point_id, adj_id)
            
            if tup1 not in weight_adjlist:
                p2 = points[adj_id]
                
                diff = p2 - p1
                diff = np.sqrt(np.sum(diff ** 2))
                weight_adjlist[tup1] = diff
                weight_adjlist[(adj_id, point_id)] = diff
                
    return weight_adjlist

def load_data (path, highway_selector, village_selector):
    collection = OSMParser.parse(path)
    highways = collection.ways_with_tag_value_in("highway", highway_selector)
    villages = collection.nodes_with_tag_value_in("place", village_selector)
    
    highways_coords = collection.ways_with_coordinates(highways)
    highways_coords = coords_dict_to_meters_dict(highways_coords)
    root = get_normalization_root(highways_coords)
    highways_coords = normalize_meters_dict(highways_coords, root)
    
    villages_coords = collection.nodes_with_coordinates(villages)
    villages_coords = coords_dict_to_meters_dict(villages_coords)
    villages_coords = normalize_meters_dict(villages_coords, root)
    
    all_points, adjlist = collection.ways_to_graph(highways)
    all_points = coords_dict_to_meters_dict(all_points)
    all_points = normalize_meters_dict(all_points, root)
    
    weight_adjlist = get_weight_adjlist(all_points, adjlist)
    
    village_route_points = identify_village_closest_points(all_points, villages_coords)
    
    return DataCollection(highways, villages, highways_coords, villages_coords,
                          all_points, adjlist, weight_adjlist,
                          village_route_points)
    
def plot_graph (points, adjlist):
    points_coords = np.array([
            points[point_indx]
            for point_indx in points
        ])
    plt.scatter(points_coords[:,1], points_coords[:,0], color="red")
    '''
    for point_indx in points:
        coords = np.flip(points[point_indx])
        plt.text(coords[0], coords[1], str(point_indx))
    '''
    for main_point in adjlist:
        adjs = adjlist[main_point]
        start = np.flip(points[main_point])
        
        for adj in adjs:
            end = np.flip(points[adj])
            plt.plot([start[0], end[0]], [start[1], end[1]], color="blue")
    

def get_best_visit_order (data, keys_to_visit, pool):
    points = data.graph_points
    adjlist = data.graph_adjlist
    weights_adjlist = data.weight_adjlist
    
    npoints, nadjlist, rmap_dict, bmap_dict = mc.GraphTheory.remap_indices_by_dict(points, adjlist)
    weights_adjlist = {
            (rmap_dict[tup[0]], rmap_dict[tup[1]]) : weights_adjlist[tup]
            for tup in weights_adjlist
        }
    remapped_keys_to_visit = {
            x : rmap_dict[keys_to_visit[x]]
            for x in keys_to_visit
        }
    
    ax = plt.subplot(1, 2, 1)
    plot_graph(npoints, nadjlist)
    
    sub_dict = mc.GraphTheory.substitution_dict_for_adjacency_list(nadjlist, keep_verts=remapped_keys_to_visit.values())
    sadjlist = mc.GraphTheory.substitute_adjacency_list(nadjlist, sub_dict)
    sweights_adjlist = mc.GraphTheory.substitute_length_adjacency_list(weights_adjlist, sub_dict)
    
    plt.subplot(1, 2, 2, sharex=ax, sharey=ax)
    plot_graph(npoints, sadjlist)
    plt.show()
    
    results = {}
    
    start = dt.datetime.now()
    
    for key_to_visit in keys_to_visit:
        road_node = keys_to_visit[key_to_visit]
        
        nroad_node = rmap_dict[road_node]
        # (paths, distances)
        results[key_to_visit] = pool.apply_async(mc.GraphTheory.dijkstra, (sadjlist, sweights_adjlist, nroad_node))
        
    results = {
            key_to_visit : results[key_to_visit].get()
            for key_to_visit in results
        }
    
    start = dt.datetime.now() - start
    print(start)
    
    relevant_road_nodes = set([
            rmap_dict[keys_to_visit[key_to_visit]]
            for key_to_visit in keys_to_visit
        ])
    
    # pprint(results)
    
    results = {
            key_to_visit : (
                    {
                        tup : results[key_to_visit][0][tup]
                        for tup in results[key_to_visit][0]
                        if (tup[0] in relevant_road_nodes) and (tup[1] in relevant_road_nodes)
                    },
                    {
                        tup : results[key_to_visit][1][tup]
                        for tup in results[key_to_visit][1]
                        if (tup[0] in relevant_road_nodes) and (tup[1] in relevant_road_nodes)
                    }
                )
            for key_to_visit in keys_to_visit
        }
    
    
if __name__ == '__main__':
    PATH = "X:\\Datasets\\planet.openstreetmap\\spessart.osm"
    HIGHWAY_SELECTOR = [
            "motorway",
            "trunk",
            "primary",
            "secondary",
            "tertiary",
            "residential",
            "unclassified",
            "motorway_link",
            "trunk_link",
            "primary_link",
            "secondary_link",
            "tertiary_link"
        ]
    VILLAGE_SELECTOR = [
            "city",
            "borough",
            "suburb",
            "quarter",
            "neighbourhood",
            "city_block",
            "town",
            "village",
            "hamlet",
            "isolated_dwelling",
            "farm"
        ]
    DATA = load_data(PATH, HIGHWAY_SELECTOR, VILLAGE_SELECTOR)
    POOL = Pool()
    get_best_visit_order (DATA, DATA.village_route_points, POOL)