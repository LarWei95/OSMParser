'''
Created on 24.09.2021

@author: larsw
'''
import numpy as np
from xml.etree import ElementTree

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
            ref = node_dict[ref]
            
            coords[i, 0] = ref.lat()
            coords[i, 1] = ref.lon()
            
        return coords
    
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
        return {
                node_id : self.__nodes[node_id]
                for node_id in self.__nodes
                if self.__nodes[node_id].has_tag(key)
            }
        
    def nodes_with_tag_value (self, key, value):
        return {
                node_id : self.__nodes[node_id]
                for node_id in self.__nodes
                if self.__nodes[node_id].has_tag_value(key, value)
            }
        
    def ways_with_tag (self, key):
        return {
                way_id : self.__ways[way_id]
                for way_id in self.__ways
                if self.__ways[way_id].has_tag(key)
            }
        
    def ways_with_tag_value (self, key, value):
        return {
                way_id : self.__ways[way_id]
                for way_id in self.__ways
                if self.__ways[way_id].has_tag_value(key, value)
            }
        
    def relations_with_tag (self, key):
        return {
                relation_id : self.__relations[relation_id]
                for relation_id in self.__relations
                if self.__relations[relation_id].has_tag(key)
            }
        
    def relations_with_tag_value (self, key, value):
        return {
                relation_id : self.__relations[relation_id]
                for relation_id in self.__relations
                if self.__relations[relation_id].has_tag_value(key, value)
            }
        

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
            lat = node.get("lat")
            lon = node.get("lon")
            
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