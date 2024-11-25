import mysql.connector
from station import Station, stations
from edge import Edge, edges
from drone import mission_drones, waiting_drones
from intersection import intersections
from take_off_landing_scheduler import check_before_take_off_for_all_drones
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

write_lock = threading.Lock()

routes=[]

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
            edges.append(Edge(stations[i], stations[j], 90))
            edges.append(Edge(stations[j], stations[i], 120))
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
    rslt = haversine([x1,y1], [x2,y2]) + count*0.1 #교통 체증 예상 가중치
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
    
def attach_intersections_to_stations() :
    for intersection in intersections:
        for station in stations:
            distance = haversine([station.latitude, station.longitude], [intersection.latitude, intersection.longitude])
            if(distance < 0.005) : #역과의 거리가 5m 이내면 그냥 역 교점
                intersection.is_station = True
                station.intersection = intersection
        
def check_un_attached_station() :
    for station in stations:
        if(station.intersection is None) :
            print(station.name)            
        # elif(station.name == "군자(능동)") :
        #     print(station.name, "연결된 간선:", station.intersection.edges) 
    

def initialize_path_planning_module() :
    get_stations_from_db()
    get_edges_by_stations()
    find_all_intersections()
    attach_intersections_to_stations()
    check_un_attached_station()

    print("간선 수:",len(edges))
    
    make_graph()

    giving_or_revoking_mission_thread = threading.Thread(target=give_or_revoke_mission_to_drone_thread)
    giving_or_revoking_mission_thread.start()
    controling_drone_thread = threading.Thread(target=control_drone_thread)
    controling_drone_thread.start()
    
    time.sleep(2)

    print(f"waiting_drones : {waiting_drones}")
    print(f"mission_drones : {mission_drones}")
    print("초기화 끝")


def give_or_revoke_mission_to_drone_thread():
    while(True) :
        time.sleep(1)
        
        for drone_idx, drone in enumerate(reversed(waiting_drones)):
            for route_idx, route in enumerate(reversed(routes)):
                if(len(route) <= 1) :
                    routes.remove(route)
                    continue
                start_station = route[0]
                distance = haversine([drone.latitude, drone.longitude], [start_station.latitude, start_station.longitude])
                # print(f"{drone.id}까지의 거리:{distance}")
                # print(f"{drone.id}의 위치:[{drone.latitude}, {drone.longitude}]")
                if(distance < 0.01): # 10m 이내의 드론에게 배송 명령 전달
                    """
                    날씨 및 배터리 체크
                    """
                    drone.destinations = route
                    routes.pop(route_idx) # for each 문인데 삽입 삭제를 시행해도 되나?
                    with write_lock:
                        mission_drones.append(drone)
                        waiting_drones.remove(drone)
                    print(f"{drone.id}에게 미션 부여")
                    break;
                    
        for drone_idx, drone in enumerate(reversed(mission_drones)):
            # print(drone.id ,drone.is_armed, drone.is_guided)
            if(len(drone.destinations) == 0 and not drone.is_moving() and not drone.is_armed): #and not drone.is_guided) :             
                with write_lock:
                    waiting_drones.append(drone)
                    mission_drones.remove(drone)
                print(f"{drone.id} 다시 대기 드론으로 전환")
        # print(f"waiting_drones : {waiting_drones}")
        # print(f"mission_drones : {mission_drones}")
                    
def control_drone_thread() :
    while(True) :
        time.sleep(0.3)        
        check_all_collision()
        check_before_take_off_for_all_drones()
        for drone in mission_drones:
            control_a_drone(drone)

def control_a_drone(drone) :
    if(drone.is_operating) : 
        return
    if(drone.is_landed() and len(drone.destinations) != 0 and drone.take_off_flag == 1) : # 이륙 스케쥴링 필요
        """
                날씨 및 배터리 체크
        """
        print(drone, "착륙 상태, 배송 임무 하달, 이륙")
        taking_off_thread = threading.Thread(target=drone.take_off)
        taking_off_thread.start()
        return
    if(drone.is_armed) :
        if(len(drone.destinations) == 1 and not drone.is_moving() and drone.go_flag == 1 and drone.remaining_distance() <= 0.001) :
            print(f"{drone.id} 최종 목적지 도착")
            landing_thread = threading.Thread(target=drone.land)
            landing_thread.start()
            return
        if(len(drone.destinations) > 0 and drone.remaining_distance() <= 0.001): # 여기서 고도 변경 필요. move_to()로 고도 변경
            if(len(drone.destinations) != 1) :
                drone.renew_destination()
                drone.renew_edge()
                print("목적지 변경")
                """
                날씨 및 배터리 체크
                
                landing_thread = threading.Thread(target=drone.land)
                landing_thread.start()

                #타이밍 계산 필요 착륙이 완료된 다음 넘겨야 함.
                drone.destinations.insert(0, drone.prev_station)
                routes.append(drone.destinations)
                drone.destinations = []
                
                
                착륙 완료 후 destinations를 routes로 반환
                """
                if(abs(drone.edge.altitude - drone.altitude) > 10) :
                    change_altitude_thread = threading.Thread(target=drone.change_altitude, args=(drone.edge.altitude,))
                    change_altitude_thread.start()
                    time.sleep(0.1)
            else :
                drone.stop()
            return
            
        if(len(drone.destinations) > 0 and not drone.is_moving() and drone.go_flag == 1 and not drone.is_operating) :
            drone_move_thread = threading.Thread(target=drone.move)
            drone_move_thread.start()
            return
        if(drone.is_moving() and drone.go_flag == 0) :
            drone.stop()
            # print(drone.id)
            # if(drone.edge is not None) :
            #     print(drone.edge.drones_on_the_edge)
            return