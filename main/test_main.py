'''
Created on 23.09.2021

@author: larsw
'''
from control.osmparser import OSMParser
import matplotlib.pyplot as plt 
import matplotlib.colors as mcolors
import numpy as np
from pprint import pprint

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

def main (collection):
    # Y X
    # 50.2013, 9.3796
    # 50.0338, 9.6281
    '''
    highways = collection.ways_with_tag("highway")
    
    highways = collection.ways_with_tag_value_in("highway", [
            "motorway",
            "trunk",
            "primary",
            "secondary",
            "tertiary",
            "residential",
            "motorway_link",
            "trunk_link",
            "primary_link",
            "secondary_link",
            "tertiary_link",
            "living_street",
            "service"
        ])
    '''
    highways = collection.ways_with_tag_value_in("highway", [
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
        ])
    villages = collection.nodes_with_tag_value_in("place", [
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
        ])
    
        
    highways_coords = collection.ways_with_coordinates(highways)
    highways_coords = coords_dict_to_meters_dict(highways_coords)
    root = get_normalization_root(highways_coords)
    highways_coords = normalize_meters_dict(highways_coords, root)
    
    villages_coords = collection.nodes_with_coordinates(villages)
    villages_coords = coords_dict_to_meters_dict(villages_coords)
    villages_coords = normalize_meters_dict(villages_coords, root)
    villages_array = np.flip(np.array([
            x
            for x in villages_coords.values()
        ]), axis=1)
    
    highway_types = list(set([
            highways[i].tags().get("highway", None)
            for i in highways
        ]))
    
    available_colors = list(mcolors.TABLEAU_COLORS.keys())
    highway_colors = {
            highway_type : mcolors.TABLEAU_COLORS[available_colors[i % len(available_colors)]]
            for i, highway_type in enumerate(highway_types)
        }
    
    pprint(highway_colors)
    
    all_points, adjlist = collection.ways_to_graph(highways)
    all_points = coords_dict_to_meters_dict(all_points)
    all_points = normalize_meters_dict(all_points, root)
    
    ax = plt.subplot(1, 2, 1)
    
    for highway_id in highways_coords:
        points = highways_coords[highway_id]
        color = highway_colors[highways[highway_id].tags()["highway"]]
        
        points = np.flip(points, axis=1)
        
        plt.plot(points[:,0], points[:,1], color=color)        
        
    plt.scatter(villages_array[:,0], villages_array[:,1])
    
    for village_id in villages_coords:
        points = np.flip(villages_coords[village_id])
        node = villages[village_id]
        name = node.tags()["name"]
        
        plt.text(points[0], points[1], name)    
    
    plt.subplot(1, 2, 2, sharex=ax, sharey=ax)
    
    for node_id in adjlist:
        adjs = adjlist[node_id]
        p1 = all_points[node_id]
        
        for adj in adjs:
            p2 = all_points[adj]
            
            plt.plot([p1[1], p2[1]], [p1[0], p2[0]], color="blue")
    
    
    plt.show()

def path_test (collection):
    highways = collection.ways_with_tag_value_in("highway", [
            "motorway",
            "trunk",
            "primary",
            "secondary",
            "tertiary",
            "residential",
            "motorway_link",
            "trunk_link",
            "primary_link",
            "secondary_link",
            "tertiary_link",
            "living_street",
            "service"
        ])
    first_key = list(highways.keys())[5]
    selected_highway = highways[first_key]
    
    highway_points = collection.ways_with_coordinates({first_key : selected_highway})[first_key]
    
    print("Way:\n{:s}".format(
            "\n".join(
                    "({:f}|{:f})".format(collection.nodes()[x].lat(), collection.nodes()[x].lon())
                    for x in selected_highway.noderefs()
                )
        ))
    print(highway_points)
    print(len(selected_highway.noderefs()), len(highway_points))

if __name__ == '__main__':
    PATH = "X:\\Datasets\\planet.openstreetmap\\spessart.osm"
    COLLECTION = OSMParser.parse(PATH)
    main(COLLECTION)
        