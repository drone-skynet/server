from utils import haversine
intersections=[]

class Intersection :
  def __init__(self, edges, latitude, longitude) :
    self.edges = edges
    self.latitude = latitude
    self.longitude = longitude
    self.drone_queue = []
    self.is_station = False
    self.station = None

  def __repr__(self):
    return "{Intersection " + str(self.latitude) + ", " + str(self.longitude) + "}"
  
  def __eq__(self, other) :
    if(self.latitude == other.latitude and self.longitude == other.longitude) :
      return True
    return False
  
  def __hash__(self):
      return hash((self.latitude, self.longitude))
  
  def fuse_same_point(self, other) : 
    if haversine([self.latitude, self.longitude], [other.latitude, other.longitude]) < 0.01 : #10m 이내의 교점은 하나로 뭉치기 #self.__eq__(other) :
      #self.edges.extend(other.edges)
      for new_edge in other.edges:
        if new_edge not in self.edges : #하나의 경로가 두 개의 경로와 교점을 만들어도, 중복된 경로는 한 번만 들어가게
          self.edges.append(new_edge)
      return True
    return False
    