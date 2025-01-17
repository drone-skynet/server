from utils import haversine, find_edge_by_point
from edge import edges
import time
import mqtt_client
from ml_model import predict_delivery_time
import math

drone_statuses = {}
waiting_drones = [] 
mission_drones = []
the_other_drones = []

#전역 드론 상태 딕셔너리에 드론 상태 업데이트
def update_drone_status(drone):
    """
    drone_statuses[drone.id] = {
        "isArmed": drone.is_armed,
        "isGuided": drone.is_guided,
        "latitude": drone.latitude,
        "longitude": drone.longitude,
        "altitude": drone.altitude,
        "vx": drone.vx,
        "vy": drone.vy,
        "vz": drone.vz,
        "battery": drone.battery_status,
        "mission_status": drone.mission_status
    }
    """
    if(drone not in waiting_drones and drone not in mission_drones and drone.is_armed is not None and not drone.is_armed) :
      waiting_drones.append(drone)
      drone.battery_status = 100
      return
    for drone1 in waiting_drones :
      if(drone1.id == drone.id) :
        drone1.is_armed = drone.is_armed if drone.is_armed is not None else drone1.is_armed
        drone1.is_guided = drone.is_guided if drone.is_guided is not None else drone1.is_guided
        drone1.latitude = drone.latitude if drone.latitude is not None else drone1.latitude
        drone1.longitude = drone.longitude if drone.longitude is not None else drone1.longitude 
        drone1.altitude = drone.altitude if drone.altitude is not None else drone1.altitude
        drone1.vx = drone.vx if drone.vx is not None else drone1.vx
        drone1.vy = drone.vy if drone.vy is not None else drone1.vy
        drone1.vz = drone.vz if drone.vz is not None else drone1.vz
        # drone1.battery_status = drone.battery_status if drone.battery_status is not None else drone1.battery_status
        # drone1.mission_status = drone.mission_status if drone.mission_status is not None else drone1.mission_status
        return
    for drone1 in mission_drones :
      if(drone1.id == drone.id) :
        drone1.is_armed = drone.is_armed if drone.is_armed is not None else drone1.is_armed
        drone1.is_guided = drone.is_guided if drone.is_guided is not None else drone1.is_guided
        drone1.latitude = drone.latitude if drone.latitude is not None else drone1.latitude
        drone1.longitude = drone.longitude if drone.longitude is not None else drone1.longitude 
        drone1.altitude = drone.altitude if drone.altitude is not None else drone1.altitude
        drone1.vx = drone.vx if drone.vx is not None else drone1.vx
        drone1.vy = drone.vy if drone.vy is not None else drone1.vy
        drone1.vz = drone.vz if drone.vz is not None else drone1.vz
        # drone1.battery_status = drone.battery_status if drone.battery_status is not None else drone1.battery_status
        # drone1.mission_status = drone.mission_status if drone.mission_status is not None else drone1.mission_status
        return

# 현재 드론 상태 정보를 반환
def get_drone_status(): 
    return drone_statuses

def get_mission_drones():
  return mission_drones

class Drone:
  edges = []
  drones = []

  def __init__(self, id) :
    self.id = id

  def __init__(self,id, is_armed, is_guided, latitude, longitude, altitude, vx, vy, vz , battery_status, mission_status) :
    self.id = id
    self.is_armed = is_armed
    self.is_guided = is_guided
    self.longitude = longitude
    self.latitude = latitude
    self.altitude = altitude
    self.battery_status = battery_status
    self.mission_status = mission_status
    self.destinations = []
    self.vx = vx
    self.vy = vy
    self.vz = vz
    #내가 조작을 위해 넣은 것들
    self.take_off_time = None
    self.go_flag = 0
    self.prev_station = None
    self.edge = None
    self.home_alt = None
    self.is_operating = False
    self.take_off_flag = 0
    self.count_before_take_off = 0
    self.delivery = None
  

  def to_dict(self):
    return {
      "id": self.id,
      "is_armed": self.is_armed,
      "is_guided": self.is_guided,
      "latitude": self.latitude,
      "longitude": self.longitude,
      "altitude": self.altitude,
      "vx": self.vx,
      "vy": self.vy,
      "vz": self.vz,
      "battery_status": self.battery_status,
      "mission_status": self.mission_status,
      "destinations": [dest.to_dict() for dest in self.destinations]  # 목적지도 직렬화
    }

  def is_moving(self):
    if abs(self.vx) < 0.05 and abs(self.vy) < 0.05 and abs(self.vz) < 0.05 :
      return False
    return True
  
  def renew_destination(self) :
    self.prev_station = self.destinations[0]
    self.destinations.pop(0)
  
  def renew_edge(self) :
    if(self.edge is not None and self in self.edge.drones_on_the_edge) :
      self.edge.drones_on_the_edge.remove(self)
      self.edge = None
    if(len(self.destinations) < 1) :
      return 
    edge = find_edge_by_point(edges, self.prev_station, self.destinations[0])
    self.edge = edge
    print("현재 드론:", self.id, "간선:",self.prev_station.name,"-",self.destinations[0].name)
    return

  def add_to_next_edge(self): # 교점 관리할 때 호출
    if len(self.destinations) < 2:
      return None
    next_edge = find_edge_by_point(edges, self.destinations[0], self.destinations[1]) 
    if(self not in next_edge.drones_on_the_edge) :
      next_edge.drones_on_the_edge.append(self)
      print("다음 간선에 미리 추가", self.id)
    return next_edge
    
  def move(self):
    self.is_operating = True
    command = {
      "command": "SET_MODE",
      "mode": "GUIDED",
      "sys_id": self.id,
    }
    mqtt_client.publish_control_command(command)

    # self.is_moving=True
    command = {
      "command": "MOVE_TO",
      "sys_id": self.id,
      "comp_id": 190,
      "latitude": self.destinations[0].latitude,
      "longitude": self.destinations[0].longitude,
      "altitude": self.edge.altitude - self.home_alt
    }
    mqtt_client.publish_control_command(command)
    print("드론", self.id, "이동 시작")

    time.sleep(3)

    self.is_operating = False
    return
  
  def stop(self):
    command = {
      "command": "SET_MODE",
      "mode": "BREAK",
      "sys_id": self.id,
    }
    mqtt_client.publish_control_command(command)

  # def find_next_edge(self):
  #   return find_edge_by_point(edges, self.destinations[0], self.destinations[1])
  
  def take_off(self):

    self.is_operating = True
    self.home_alt = self.altitude
    self.take_off_time = time.perf_counter()
    self.add_to_next_edge()    
    self.renew_destination()
    self.renew_edge()

    while(self.go_flag == 0) :
      time.sleep(0.3)
      print("go_flag 대기 in drone.take_off")
      if(len(self.destinations) == 0) : #과잉 대기로 임무 해제
        break

    if(len(self.destinations) == 0) : #과잉 대기로 임무 해제에 대한 후 처리
      self.home_alt = None
      self.take_off_time = None
      if(self.edge is not None and self in self.edge.drones_on_the_edge):
        self.edge.drones_on_the_edge.remove(self)
      self.edge = None
      self.is_operating = False
      return


    # 드론 GUIDED 모드 설정
    command = {
      "command": "SET_MODE",
      "mode": "GUIDED",
      "sys_id": self.id,
    }
    mqtt_client.publish_control_command(command)
    

    time.sleep(2)

    # 드론 ARM
    command = {
      "command": "ARM",
      "sys_id": self.id,
      "comp_id": 1 
    }
    mqtt_client.publish_control_command(command)
    
    time.sleep(2)
    
    
    # 이륙
    command = {
      "command": "TAKEOFF",
      "sys_id": self.id,
      "comp_id": 1,
      "altitude": self.edge.altitude - self.home_alt
    }
    mqtt_client.publish_control_command(command)
    self.take_off_time = time.perf_counter()

    time.sleep(2)
    while(not self.is_moving()):
      time.sleep(1)
    #이륙 완료 후 경로 그리기
    self.draw_route()
    
    self.is_operating = False
    print("드론", self.id, "이륙")
    
  
  def remaining_distance(self):
    return haversine([self.latitude, self.longitude], [self.destinations[0].latitude, self.destinations[0].longitude])

  def land(self):
    self.stop()
    print("드론", self.id, "착륙")
    self.is_operating = True
    command = {
      "command": "LAND",
      "sys_id": self.id,
      "comp_id": 1
    }
    mqtt_client.publish_control_command(command)

    #time.sleep(20)

    while(True):
      before_alt = self.altitude
      time.sleep(1)
      # print(self.id, "1초 지남")
      after_alt = self.altitude
      if abs(before_alt - after_alt) < 0.1 and not self.is_armed:
        break
      # if not self.is_armed:
      #   break

    self.take_off_time = None
    # tmp_edge = self.edge
    self.renew_destination()
    self.renew_edge() #self.edge 제거
    #print(tmp_edge.drones_on_the_edge)
    #경로 그리기
    self.draw_route()
    self.is_operating = False

    return
  
  def change_altitude(self, new_alt) :
    self.is_operating = True
    print(self.id ,"고도 변경")
    command = {
      "command": "MOVE_TO",
      "sys_id": self.id,
      "comp_id": 190,
      "latitude": self.latitude,
      "longitude": self.longitude,
      "altitude": new_alt - self.home_alt,
    }
    mqtt_client.publish_control_command(command)
    
    time.sleep(2)

    while(True) :
      before_alt = self.altitude
      time.sleep(1)
      # print(self.id, "1초 지남")
      after_alt = self.altitude
      if abs(before_alt - after_alt) < 0.1:
        break
      

    self.renew_destination()
    self.renew_edge()
    self.is_operating = False

  def draw_route(self):
    points_of_destination = []
    prev_station = self.prev_station
    if(len(self.destinations) > 0):
      points_of_destination.append({
       "latitude" : self.latitude,
       "longitude" : self.longitude,
       "altitude" : 100#self.altitude
      })
    for destination in self.destinations:
      #altitude = find_edge_by_point(edges, prev_station, destination).altitude
      points_of_destination.append({
       "latitude" : destination.latitude,
       "longitude" : destination.longitude,
       "altitude" : 100#altitude
      })
      #prev_station = destination
    mqtt_client.publish_destinations_to_draw(self.id, [])
    mqtt_client.publish_destinations_to_draw(self.id, points_of_destination)

  @staticmethod
  def calculate_direction(coord1, coord2):
    # 위도, 경도를 라디안으로 변환
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # 경도 차이
    delta_lon = lon2 - lon1

    # 방위각 계산
    x = math.sin(delta_lon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(delta_lon)
    bearing = math.atan2(x, y)
    
    # 라디안을 도(degree)로 변환
    bearing = math.degrees(bearing)
    
    # 0~360도로 조정
    bearing = (bearing + 360) % 360
    return bearing
  

  def get_edt(self, model):
    destinations = self.destinations[:]
    if(len(destinations) == 0):
      return 0
    first_distance = haversine([self.latitude, self.longitude], [destinations[0].latitude, destinations[0].longitude])
    drone_direction = Drone.calculate_direction([self.latitude, self.longitude], [destinations[0].latitude, destinations[0].longitude])
    total_time = predict_delivery_time(model, first_distance, destinations[0].wind_speed, destinations[0].wind_direction, drone_direction)
    for idx, destination in enumerate(destinations):
      if(idx == len(destinations)-1):
        break
      edge = find_edge_by_point(edges, destinations[idx], destinations[idx+1])
      drone_direction = Drone.calculate_direction([destinations[idx].latitude, destinations[idx].longitude], [destinations[idx+1].latitude, destinations[idx+1].longitude])
      total_time += predict_delivery_time(model, edge.distance, destinations[idx+1].wind_speed, destinations[idx+1].wind_direction, drone_direction)

    return int(total_time)

  
  def is_landed(self) :
    if(self.take_off_time == None) :
      return True
    return False

  def __eq__(self, other):
    return self.id == other.id
    
  def __hash__(self):
    return hash(self.id)
  
  def __repr__(self):
    return "{"+f"id = {self.id}, is_armed = {self.is_armed}"+"}"
