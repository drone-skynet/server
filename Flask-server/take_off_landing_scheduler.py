from drone import waiting_drones, mission_drones
from intersection import intersections
from utils import *

def check_before_take_off_for_all_drones() :
  for drone in mission_drones:
    if(not drone.is_landed()):
      continue
    
    start_station = drone.destination[0]
    #지금 진입중인 드론이 있음
    if(len(start_station.intersection.drone_queue) != 0):
      continue

    first_edge = find_edge_by_point(drone.destinations[0], drone.destinations[1])
    if(first_edge.drones_on_the_edge[-1].destination[0] != first_edge.origin) :
      continue
    
    