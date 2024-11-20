stations = []

class Station:
  def __init__(self, id, name, longitude, latitude, capacity):
    self.id = id
    self.name = name
    self.longitude = float(longitude)
    self.latitude = float(latitude)
    self.capacity = capacity
    self.intersection = None

  def __repr__(self):
    return self.name
    #return (f"Station(id={self.id}, name={self.name}, "
    #       f"latitude={self.latitude}, longitude={self.longitude}, capacity={self.capacity})")
  def __eq__(self, other):
    return self.id == other.id #내용 비교
  def __hash__(self):
    return hash((self.longitude, self.latitude))

