from utils import haversine

edges=[]

class Edge:
  def __init__(self, origin, destination):
    self.origin = origin
    self.destination = destination
    self.weight = haversine([origin.latitude, origin.longitude], [destination.latitude, destination.longitude])
    self.drones_on_the_edge = []
  def __repr__(self):
    return (f"edge(origin={self.origin.name}, destination={self.destination.name}, "
            f"weight={self.weight})")
  def __eq__(self, other):
    return self.origin == other.origin and self.destination == other.destination