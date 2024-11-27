stations = []

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


    self.intersection = None

  def __repr__(self):
    return self.name
    #return (f"Station(id={self.id}, name={self.name}, "
    #       f"latitude={self.latitude}, longitude={self.longitude}, capacity={self.capacity})")
  def __eq__(self, other):
    return self.id == other.id #내용 비교
  def __hash__(self):
    return hash((self.longitude, self.latitude))

  def check_weather(self):
    """현재 날씨 상태를 확인하고 비행 가능 여부를 업데이트"""
    from weather_api import get_station_weather
    is_raining = get_station_weather(self)  # self를 전달
    self.is_flyable = not is_raining
