'''
Created on 24.09.2021

@author: larsw
'''
import numpy as np
from xml.etree import ElementTree
from collections import defaultdict

class OSMObject ():
    def __init__ (self, objid, tags):
        self.__id = objid
        self.__tags = tags
        
    def id (self):
        return self.__id
    
    def tags (self):
        return self.__tags
    
    def has_tag (self, key):
        return key in self.__tags
    
    def has_tag_value (self, key, value):
        if not self.has_tag(key):
            return False
        else:
            return self.__tags[key] == value
        
    def has_tag_value_in (self, key, values):
        if not self.has_tag(key):
            return False
        else:
            return self.__tags[key] in values
        
    @classmethod
    def filter_by_tag (cls, object_dict, tag):
        return {
                obj_id : object_dict[obj_id]
                for obj_id in object_dict
                if object_dict[obj_id].has_tag(tag)
            }
        
    @classmethod
    def filter_by_tag_value (cls, object_dict, tag, value):
        return {
                obj_id : object_dict[obj_id]
                for obj_id in object_dict
                if object_dict[obj_id].has_tag_value(tag, value)
            }
        
    @classmethod
    def filter_by_tag_value_in (cls, object_dict, tag, values):
        return {
                obj_id : object_dict[obj_id]
                for obj_id in object_dict
                if object_dict[obj_id].has_tag_value_in(tag, values)
            }
    
class OSMNode (OSMObject):
    def __init__ (self, objid, tags, lat, lon):
        super().__init__(objid, tags)
        
        self.__lat = lat
        self.__lon = lon
        
    def lat (self):
        return self.__lat
    
    def lon (self):
        return self.__lon
    
class OSMWay (OSMObject):
    def __init__ (self, objid, tags, noderefs):
        super().__init__(objid, tags)
        
        self.__noderefs = noderefs
        
    def noderefs (self):
        return self.__noderefs
    
    def coordinates (self, node_dict):
        coords = np.empty((len(self.__noderefs), 2), dtype=np.float)
        
        for i in range(len(self.__noderefs)):
            ref = self.__noderefs[i]
            
            if ref in node_dict:
                ref = node_dict[ref]
                
                coords[i, 0] = ref.lat()
                coords[i, 1] = ref.lon()
            else:
                i -= 1
                break
        
        if i != 0:
            coords = coords[:i+1]
        else:
            coords = None
        
        return coords
    
    def adjacency_list (self, symmetric=True):
        adjlist = defaultdict(set)
        
        node_count = len(self.__noderefs)
        
        for i in range(1, node_count):
            last = self.__noderefs[i-1]
            current = self.__noderefs[i]
            
            adjlist[last].add(current)
            
            if symmetric:
                adjlist[current].add(last)
        
        return adjlist
        
    
class OSMMember ():
    def __init__ (self, member_type, ref, role):
        self.__type = member_type
        self.__ref = ref
        self.__role = role
        
    def type (self):
        return self.__type
    
    def ref (self):
        return self.__ref
    
    def role (self):
        return self.__role
    
class OSMRelation (OSMObject):
    def __init__ (self, objid, tags, members):
        super().__init__(objid, tags)
        
        self.__members = members
        
    def members (self):
        return self.__members
        

class OSMCollections ():
    def __init__ (self, nodes, ways, relations):
        self.__nodes = nodes
        self.__ways = ways
        self.__relations = relations
        
    def nodes (self):
        return self.__nodes
    
    def ways (self):
        return self.__ways
    
    def relations (self):
        return self.__relations
    
    def nodes_with_tag (self, key):
        return OSMObject.filter_by_tag(self.__nodes, key)
        
    def nodes_with_tag_value (self, key, value):
        return OSMObject.filter_by_tag_value(self.__nodes, key, value)
    
    def nodes_with_tag_value_in (self, key, values):
        return OSMObject.filter_by_tag_value_in(self.__nodes, key, values)
        
    def ways_with_tag (self, key):
        return OSMObject.filter_by_tag(self.__ways, key)
        
    def ways_with_tag_value (self, key, value):
        return OSMObject.filter_by_tag_value(self.__ways, key, value)
    
    def ways_with_tag_value_in (self, key, values):
        return OSMObject.filter_by_tag_value_in(self.__ways, key, values)
    
    def relations_with_tag (self, key):
        return OSMObject.filter_by_tag(self.__relations, key)
        
    def relations_with_tag_value (self, key, value):
        return OSMObject.filter_by_tag_value(self.__relations, key, value)
    
    def relations_with_tag_value_in (self, key, values):
        return OSMObject.filter_by_tag_value_in(self.__relations, key, values)
        
    def nodes_with_coordinates (self, nodes=None):
        if nodes is None:
            nodes = self.__nodes
            
        coords = {
                node_id : np.array([nodes[node_id].lat(), nodes[node_id].lon()])
                for node_id in nodes
            }
        return coords
        
    def ways_with_coordinates (self, ways=None):
        if ways is None:
            ways = self.__ways
        
        coords = {
                way_id : ways[way_id].coordinates(self.__nodes)
                for way_id in ways
            }
        coords = {
                way_id : coords[way_id]
                for way_id in coords
                if coords[way_id] is not None
            }
        
        return coords
    
    def ways_to_graph (self, ways=None, symmetric=True):
        if ways is None:
            ways = self.__ways
        
        all_noderefs = set()
        adjlist = defaultdict(set)
        
        for way_id in ways:
            way = ways[way_id]
            
            c_adjlist = way.adjacency_list(symmetric)
            
            for node_id in c_adjlist:
                if node_id in self.__nodes:
                    all_noderefs.add(node_id)
                    adjs = c_adjlist[node_id]
                    
                    for adj in adjs:
                        if adj in self.__nodes:
                            all_noderefs.add(adj)
                            adjlist[node_id].add(adj)
            
        all_noderefs = {
                x : np.array([self.__nodes[x].lat(), self.__nodes[x].lon()])
                for x in all_noderefs
            }
        return all_noderefs, adjlist

class OSMParser():
    @classmethod
    def _parse_tags (cls, elem):
        tags = {}
        
        for tag_elem in elem.findall("tag"):
            tags[tag_elem.get("k")] = tag_elem.get("v")
            
        return tags
    
    @classmethod
    def _parse_nodes (cls, root):
        nodes = {}
        
        for node in root.findall("node"):
            node_id = node.get("id")
            lat = np.round(float(node.get("lat")), 6)
            lon = np.round(float(node.get("lon")), 6)
            
            tags = cls._parse_tags(node)
                
            nodes[node_id] = OSMNode(node_id, tags, lat, lon)
            
        return nodes
            
    @classmethod
    def _parse_ways (cls, root):
        ways = {}
        
        for way in root.findall("way"):
            way_id = way.get("id")
            
            tags = cls._parse_tags(way)
            node_refs = [
                    nd.get("ref")
                    for nd in way.findall("nd")
                ]
            
            ways[way_id] = OSMWay(way_id, tags, node_refs)
            
        return ways
    
    @classmethod
    def _parse_relations (cls, root):
        relations = {}
        
        for relation in root.findall("relation"):
            relation_id = relation.get("id")
            
            tags = cls._parse_tags(relation)
            members = [
                    OSMMember(member.get("type"), member.get("ref"), member.get("role"))
                    for member in relation.findall("member")
                ]
            relations[relation_id] = OSMRelation(relation_id, tags, members)
            
        return relations
    
    @classmethod
    def parse (cls, filepath):
        root = ElementTree.parse(filepath).getroot()
        
        nodes = cls._parse_nodes(root)
        ways = cls._parse_ways(root)
        relations = cls._parse_relations(root)
        
        return OSMCollections(nodes, ways, relations)