import mysql.connector
from station import Station, stations
from edge import Edge, edges
from drone import mission_drones, waiting_drones
from intersection import intersections
from take_off_landing_scheduler import check_before_take_off_for_all_drones
from utils import find_edge_by_point, haversine
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

TIME_INTERVAL = 0.3
LOW_BATTERY_LEVEL = 40


db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')

# write_lock = threading.Lock()

#routes=[]
waiting_delivery=[]

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
            station = Station(row[0],row[1],row[2],row[3],row[4],row[5],row[6])
            stations.append(station)
    finally:
        cursor.close()
        conn.close()
    return

def get_edges_by_stations() :
    n = len(stations)
    for i in range(n):
        for j in range(i+1,n):
            edges.append(Edge(stations[i], stations[j], 60))
            edges.append(Edge(stations[j], stations[i], 80))
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
    try :
        path = nx.astar_path(G, start, goal, heuristic=heuristic, weight='weight')
    except Exception as e:  # 예외 처리 추가
        print(f"없는 역 입력")
        return None

    # rsltStr=""
    # for station in path :
    #     rsltStr += station.name+" "
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
            if(distance < 0.011) : #역과의 거리가 11m 이내면 그냥 역 교점
                intersection.is_station = True
                intersection.station = station
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
    print("최종 교점 수:",len(intersections))
    
    make_graph()

    giving_or_revoking_mission_thread = threading.Thread(target=give_or_revoke_mission_to_drone_thread)
    giving_or_revoking_mission_thread.start()
    controling_drone_thread = threading.Thread(target=control_drone_thread)
    controling_drone_thread.start()

    # 날씨 체크 쓰레드 시작
    weather_check_thread = threading.Thread(target=check_weather_thread)
    # weather_check_thread.start()
    
    time.sleep(2)

    print(f"waiting_drones : {waiting_drones}")
    print(f"mission_drones : {mission_drones}")
    print("초기화 끝")

BATTERY_SPEED = 100/1200*3
def give_or_revoke_mission_to_drone_thread():
    while(True) :
        time.sleep(3)
        # print(waiting_delivery)
        for drone_idx, drone in enumerate(reversed(waiting_drones)):
            for idx, delivery in enumerate(reversed(waiting_delivery)):
                if(delivery.origin == delivery.destination):
                    waiting_delivery.remove(delivery)
                    print(f"배송 완료된 배송 : {delivery.content}")
                    continue
                # if(len(delivery.route) <= 1) :
                #     wating_delivery.remove(delivery)
                #     continue
                route = search_route(get_station_by_name(delivery.origin), get_station_by_name(delivery.destination))
                if(route is None) :
                    waiting_delivery.remove(delivery)
                    continue
                start_station = route[0]
                #print(route)# 왜 start_station이 null이 나오지?
                """
                #날씨 체크
                """
                if(not start_station.is_flyable or not route[1].is_flyable or drone.battery_status <= LOW_BATTERY_LEVEL):
                    print("날씨 or 배터리 이슈")
                    continue
                distance = haversine([drone.latitude, drone.longitude], [start_station.latitude, start_station.longitude])
                # print(f"{drone.id}까지의 거리:{distance}")
                # print(f"{drone.id}의 위치:[{drone.latitude}, {drone.longitude}]")
                if(distance < 0.01): # 10m 이내의 드론에게 배송 명령 전달
                    drone.destinations = route
                    drone.delivery = delivery
                    waiting_delivery.remove(delivery) # for each 문인데 삽입 삭제를 시행해도 되나?
                    delivery.is_reserved=False
                    delivery.drone = drone
                    mission_drones.append(drone)
                    waiting_drones.remove(drone)
                    print(f"{drone.id}에게 미션 부여 : {drone.destinations}")
                    break
        #물품은 있지만 드론이 없어서 할당받지 못한 배송들
        for idx, delivery in enumerate(reversed(waiting_delivery)):
            if(delivery.is_reserved):
                continue
            nearest_drone = find_nearest_waiting_drone(start_station)
            if(nearest_drone is None): #대기중인 드론조차 없음
                continue
            retrive_route = search_route(get_nearest_station(nearest_drone.latitude, nearest_drone.longitude) ,get_station_by_name(delivery.origin))
            #날씨 체크 및 배터리 체크
            if(not retrive_route[0].is_flyable or not retrive_route[1].is_flyable or drone.battery_status <= LOW_BATTERY_LEVEL):
                print("날씨 이슈")
                continue
            if(nearest_drone is not None) : #이건 배송이 아님 -> 배송 라우트와 배송 아닌 라우트 구분 해야겠다
                nearest_drone.destinations = retrive_route
                delivery.is_reserved = True
                mission_drones.append(nearest_drone)
                waiting_drones.remove(nearest_drone)
                print(f"{start_station}에 드론 없음. 드론{nearest_drone.id}을 보냄 ")


                    
        for drone_idx, drone in enumerate(reversed(mission_drones)):
            if(len(drone.destinations) == 0 and not drone.is_moving() and not drone.is_armed and not drone.is_operating):     
                waiting_drones.append(drone)
                mission_drones.remove(drone)
                print(f"{drone.id} 다시 대기 드론으로 전환")
        # print(f"waiting_drones : {waiting_drones}")
        # print(f"mission_drones : {mission_drones}")
        
        for drone in waiting_drones:
            drone.battery_status += BATTERY_SPEED
            drone.battery_status = 100 if drone.battery_status > 100 else drone.battery_status
        for drone in mission_drones:
            if(not drone.is_armed) :
                drone.battery_status += BATTERY_SPEED
                drone.battery_status = 100 if drone.battery_status > 100 else drone.battery_status
                continue
            drone.battery_status -= BATTERY_SPEED
            drone.battery_status = 0 if drone.battery_status < 0 else drone.battery_status
            # print(drone.id, drone.battery_status)
                    
def control_drone_thread() :
    while(True) :
        time.sleep(TIME_INTERVAL)        
        check_all_collision()
        check_before_take_off_for_all_drones()
        for drone in mission_drones:
            control_a_drone(drone)
            if(not drone.is_armed):
                drone.count_before_take_off += TIME_INTERVAL
                if(drone.count_before_take_off > 300) :
                    return_mission_of_unarmed_drone(drone)
            else:
                drone.count_before_take_off = 0
            

def control_a_drone(drone) :
    if(drone.is_operating) : 
        return
    if(drone.is_landed() and len(drone.destinations) != 0 and drone.take_off_flag == 1) : # 이륙 스케쥴링 필요

        #날씨 및 배터리 체크
        if(not drone.destinations[0].is_flyable or not drone.destinations[1].is_flyable or drone.battery_status <= LOW_BATTERY_LEVEL):
            print(drone, "악천후 혹은 배터리 부족으로 이륙 불가, 대기")
            return        
        print(drone, "착륙 상태, 배송 임무 하달, 이륙")
        taking_off_thread = threading.Thread(target=drone.take_off)
        taking_off_thread.start()
        return
    if(drone.is_armed) :
        if(len(drone.destinations) == 1 and not drone.is_moving() and drone.go_flag == 1 and drone.remaining_distance() <= 0.001) :
            print(f"{drone.id} 최종 목적지 도착")
            landing_thread = threading.Thread(target=drone.land)
            landing_thread.start()
            #착륙 끝나면 물품 반환
            return_mission_thread = threading.Thread(target=return_mission_of_unarmed_drone, args=(drone,))
            return_mission_thread.start()
            return
        if(len(drone.destinations) > 0 and drone.remaining_distance() <= 0.001): # 여기서 고도 변경 필요. move_to()로 고도 변경
            if(len(drone.destinations) != 1) :
                #다음 간선의 높이와 비교
                next_edge_altitude = find_edge_by_point(edges, drone.destinations[0], drone.destinations[1]).altitude
                if(abs(next_edge_altitude - drone.altitude) > 10) :
                    change_altitude_thread = threading.Thread(target=drone.change_altitude, args=(next_edge_altitude,))
                    change_altitude_thread.start()
                    time.sleep(0.1)
                else :
                    drone.renew_destination()
                    drone.renew_edge()
                
                print("목적지 변경")
                
                #날씨 및 배터리 체크
                if(not drone.destinations[0].is_flyable or not drone.prev_station.is_flyable or drone.battery_status <= LOW_BATTERY_LEVEL):
                    #착륙
                    landing_thread = threading.Thread(target=drone.land)
                    landing_thread.start()
                    #착륙 끝나면 물품 반환
                    return_mission_thread = threading.Thread(target=return_mission_of_unarmed_drone, args=(drone,))
                    return_mission_thread.start()

            else :
                drone.stop()
            return
            
        if(len(drone.destinations) > 0 and not drone.is_moving() and drone.go_flag == 1 and not drone.is_operating) :
            drone_move_thread = threading.Thread(target=drone.move)
            drone_move_thread.start()
            return
        if(drone.is_moving() and drone.go_flag == 0) :
            drone.stop()
            return
        
def return_mission_of_unarmed_drone(drone):
    while(drone.is_armed) :
        time.sleep(1)
    time.sleep(1.5)
    if(drone.delivery is not None) : 
        print(f"{drone.id}가 물품 반환 : {drone.delivery}")
        if(drone.prev_station is not None):
            drone.delivery.origin = drone.prev_station.name
        waiting_delivery.append(drone.delivery)
    drone.destinations=[]
    if(drone.delivery is not None):
        drone.delivery.drone=None
    drone.delivery=None
    drone.count_before_take_off = 0
    return
        
def check_weather_thread():
    while True:
        try:
            for station in stations:
                station.check_weather()
            time.sleep(3600)  # 60분마다 체크
        except Exception as e:
            time.sleep(60)  # 오류 발생시 1분 후 재시도
        


def find_nearest_waiting_drone(station):
    nearest_drone = None
    min_distance = 3#float('inf') #10km로 하는 게 낫지 않을까?
    
    for drone in waiting_drones:
        distance = haversine([drone.latitude, drone.longitude], [station.latitude, station.longitude])
        if distance < min_distance:
            min_distance = distance
            nearest_drone = drone
    
    return nearest_drone

def get_nearest_station(lat, lon):
    nearest_station = None
    min_distance = float('inf')
    
    for station in stations:  # stations는 전체 역 목록이 있는 리스트라고 가정
        distance = haversine([lat, lon], [station.latitude, station.longitude])
        if distance < min_distance:
            min_distance = distance
            nearest_station = station
    
    return nearest_station
