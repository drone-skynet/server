import mysql.connector
from station import Station
from edge import Edge
from drone import Drone, mission_drones, waiting_drones
from utils import haversine
# from .intersection_finding import find_all_intersections
import networkx as nx
from dotenv import load_dotenv
import os
import threading
import time
# from .collision_check import check_all_collision
# import subprocess

# mySQL만 WSL이 아니라 host window에 있는 경우
# def get_windows_host_ip():
#     # Run the command to get the default gateway
#     result = subprocess.run(
#         ["ip", "route", "show", "default"],
#         capture_output=True,
#         text=True
#     )
#     # Extract the IP from the command output
#     if result.returncode == 0:
#         output = result.stdout.strip()
#         # Split and locate the gateway IP
#         gateway_ip = output.split()[2]
#         return gateway_ip
#     else:
#         raise RuntimeError("Failed to retrieve Windows host IP")

load_dotenv()

db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')

stations=[]
edges=[]
drones=[]
intersections=[]
routes=[]
# mission_drones=[]
# waiting_drones=[]

limitDistance = 2.0

def get_stations_from_db() :
    conn = mysql.connector.connect(
        host="172.30.1.73",
        user=db_user,
        password=db_password,
        database="drone" 
    )
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM station")

        results = cursor.fetchall()
        for row in results:
            station = Station(row[0],row[1],row[2],row[3],row[4])
            stations.append(station)
    finally:
        cursor.close()
        conn.close()
    return

def get_edges_by_stations() :
    n = len(stations)
    for i in range(n):
        for j in range(i+1,n):
            edges.append(Edge(stations[i],stations[j]))
            edges.append(Edge(stations[j],stations[i]))
            if(edges[-1].weight > limitDistance) : 
                edges.pop()
                edges.pop()
    return


# 휴리스틱(좌표 -> 거리 계산)
def heuristic(n1, n2):
    (x1, y1) = n1.longitude, n1.latitude
    (x2, y2) = n2.longitude, n2.latitude
    # 해당 좌표를 지나는 드론의 수 계산
    count = 0
    for drone in drones:
        # 드론의 목적지 리스트에서 현재 노드와 일치하는 노드가 있는지 확인
        for i in range(len(drone.destinations)-1):
            if (drone.destinations[i].latitude == y1 and drone.destinations[i].longitude == x1 ):
                count += 1
                break
    rslt = haversine([x1,y1], [x2,y2]) + count*0.01 #교통 체증 예상 가중치
    # print(rslt)
    return rslt


def make_graph() :
    global G
    G = nx.DiGraph()

    for station in stations:
        #G.add_node((station.longitude, station.latitude))
        G.add_node(station)

    # 엣지 추가
    for edge in edges:
        #G.add_edge((edge.origin.longitude, edge.origin.latitude), (edge.destination.longitude, edge.destination.latitude), weight = edge.weight)
        G.add_edge(edge.origin, edge.destination, weight = edge.weight)


def search_route(start, goal) :
    path = nx.astar_path(G, start, goal, heuristic=heuristic, weight='weight')

    rsltStr=""
    for station in path :
        rsltStr += station.name+" "
    print(rsltStr)

   
    
    return path

def get_station_by_name(name) :
    for station in stations:
        if station.name == name :
            return station
            
    return None
    



    

def initialize_path_planning_module() :
    get_stations_from_db()
    get_edges_by_stations()
    Drone.edges = edges
    Drone.drones = drones
    Drone
    Station.stations = stations
    print("간선 수:",len(edges))
    # intersections = find_all_intersections(edges)    
    make_graph()

    giving_mission_thread = threading.Thread(target=give_mission_to_drone_thread)
    giving_mission_thread.start()
    controling_drone_thread = threading.Thread(target=control_drone_thread)
    controling_drone_thread.start()
    # 날씨 체크 쓰레드 시작
    weather_check_thread = threading.Thread(target=check_weather_thread)
    weather_check_thread.start()

'''
    dest_sum = 1
    while(dest_sum > 0) :
        time.sleep(1)
        # check_all_collision(edges, intersections)
        dest_sum = 0
        for drone in drones:
            dest_sum += len(drone.destinations)
'''

def give_mission_to_drone_thread():
    while(True) :
        time.sleep(1)
        
        for drone_idx, drone in enumerate(reversed(waiting_drones)):
            for route_idx, route in enumerate(reversed(routes)):
                start_station = route[0]
                distance = haversine([drone.latitude, drone.longitude], [start_station.latitude, start_station.longitude])
                if(distance < 0.002):
                    drone.destinations = route
                    routes.pop(route_idx) # for each 문인데 삽입 삭제를 시행해도 되나?
                    drone.prev_station = drone.destinations[0]
                    drone.destinations.pop(0)
                    mission_drones.append(drone)
                    waiting_drones.pop(drone_idx)
                    print("미션 부여")
                    
def control_drone_thread() :
    while(True) :
        time.sleep(0.3)
        
        for drone in mission_drones:
            if(drone.is_landed()) : # 이륙 스케쥴링 필요 + 별도의 쓰레딩 처리 필요 대기 시간이 있어야 함.
                print(drone, "착륙 상태")
                drone.take_off()
                time.sleep(10)

            print(drone.velocity, not drone.is_moving())
            if(drone.remaining_distance() <= 0.1):
                print("목적지 변경")
                drone.stop()
                drone.prev_station = drone.destination[0]
                drone.destination.pop(0)
                drone.move()
                time.sleep(5)
            elif(not drone.is_moving()) : # flag 확인 후 움직이는 걸로 변경해야함.
                print(drone, "안 움직임")
                drone.move()
                time.sleep(5)

def check_weather_thread():
    while True:
        time.sleep(3600)  # 1시간 대기
        for station in stations:
            station.check_weather()  # 각 station의 날씨 체크