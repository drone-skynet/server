import mysql.connector
from station import Station, stations
from edge import Edge, edges
from drone import mission_drones, waiting_drones
from utils import haversine
from intersection_finding import find_all_intersections
from collision_check import check_all_collision
import networkx as nx
from dotenv import load_dotenv
import os
import threading
import time
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



routes=[]
# mission_drones=[]
# waiting_drones=[]

limitDistance = 2.0

def get_stations_from_db() :
    conn = mysql.connector.connect(
        host="172.21.160.1",
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
    for drone in mission_drones:
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
    find_all_intersections()
    print("간선 수:",len(edges))
    
    # intersections = find_all_intersections(edges)    
    make_graph()

    giving_or_revoking_mission_thread = threading.Thread(target=give_or_revoke_mission_to_drone_thread)
    giving_or_revoking_mission_thread.start()
    controling_drone_thread = threading.Thread(target=control_drone_thread)
    controling_drone_thread.start()

    print("초기화 끝")


def give_or_revoke_mission_to_drone_thread():
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
        for drone_idx, drone in enumerate(reversed(mission_drones)):
            if(len(drone.destinations) == 0 and not drone.is_moving() and not drone.is_armed) :
                waiting_drones.append(drone)
                mission_drones.pop(drone_idx)
                    
def control_drone_thread() :
    while(True) :
        time.sleep(0.3)        
        for drone in mission_drones:
            check_all_collision()
            control_a_drone(drone)

def control_a_drone(drone) :
    if(drone.is_operating) : 
        return
    if(drone.is_landed() and len(drone.destinations) != 0) : # 이륙 스케쥴링 필요
        print(drone, "착륙 상태, 배송 임무 하달, 이륙")
        taking_off_thread = threading.Thread(target=drone.take_off)
        taking_off_thread.start()
        return
    if(drone.is_armed) :
        if(len(drone.destinations) == 0) :
            print("최종 목적지 도착")
            drone.land()
            return
        if(drone.remaining_distance() <= 0.1):
            print("목적지 변경")
            drone.stop()
            drone.prev_station = drone.destinations[0]
            drone.destinations.pop(0)
            if(len(drone.destinations) == 0) :
                return
        if(not drone.is_moving() and time.time() - drone.take_off_time > 10 and drone.go_flag == 1) :
            drone.move()
        if(drone.is_moving() and time.time() - drone.take_off_time > 10 and drone.go_flag == 0) :
            drone.stop()