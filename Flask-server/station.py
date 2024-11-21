class Station:
  stations = []
  def __init__(self, id, name, longitude, latitude, capacity,grid_x,grid_y):
    self.id = id
    self.name = name
    self.longitude = float(longitude)
    self.latitude = float(latitude)
    self.capacity = capacity
    self.grid_x=grid_x
    self.grid_y=grid_y
    self.is_flyable = True  # 비행 가능 여부 기본값



  def __repr__(self):
    return self.name
    #return (f"Station(id={self.id}, name={self.name}, "
    #       f"latitude={self.latitude}, longitude={self.longitude}, capacity={self.capacity})")
  def __eq__(self, other):
    return self.id == other.id #내용 비교
  def __hash__(self):
    return hash((self.longitude, self.latitude))

