from drone import mission_drones
from intersection import intersections
from utils import *
from edge import edges

def check_before_take_off_for_all_drones() :
  
  for drone in mission_drones:
    drone.take_off_flag = 1
    #이륙 고려 대상 드론이 아님
    if(not drone.is_landed()):
      drone.take_off_flag = 0
      continue
    if(len(drone.destinations) < 2) :
      drone.take_off_flag = 0
      continue

    start_station = drone.destinations[0]
    #지금 진입중인 드론이 있음
    if(len(start_station.intersection.drone_queue) != 0):
      drone.take_off_flag = 0
      continue
    #진입할 간선의 맨 뒷 드론이 교점 통과 안했음
    first_edge = find_edge_by_point(edges, drone.destinations[0], drone.destinations[1])
    if(len(first_edge.drones_on_the_edge) != 0):
      last_drone_of_the_edge = first_edge.drones_on_the_edge[-1]
      if(last_drone_of_the_edge.destinations[0] == first_edge.origin) :
        drone.take_off_flag = 0
        continue
      #진입하는 간선의 맨 뒷 드론과의 거리가 5m 이내일 때
      if(find_distance_between_2_drones(drone ,last_drone_of_the_edge)<0.005) :
        drone.take_off_flag = 0
        continue
    
    