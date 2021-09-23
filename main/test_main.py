'''
Created on 23.09.2021

@author: larsw
'''
from control.osmparser import OSMParser


if __name__ == '__main__':
    path = "X:\\Datasets\\planet.openstreetmap\\spessart.osm"
    collection = OSMParser.parse(path)
    # Y X
    # 50.2013, 9.3796
    # 50.0338, 9.6281
    
    print(len(collection.ways_with_tag("highway")))