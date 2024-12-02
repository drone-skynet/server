from utils import haversine, find_distance_between_2_drones
from station import stations
from drone import mission_drones
from edge import edges
from intersection import intersections

def check_collision_of_one_intersection(intersection): #겹치는 직선 제거 필요 or 교점 위 모든 드론에게 안전거리 계산 근데 뭐 부터 보낼지 고려
                                                      #closest drone 부활 필요
    leading_drones = []  # 각 간선의 leading 드론 저장
    intersection_pos = [intersection.latitude, intersection.longitude]
    
    # 각 간선의 leading 드론 찾기
    for edge in intersection.edges:
        if not edge.drones_on_the_edge:
            continue
            
        # 교점을 지나지 않은 첫 번째 드론 찾기
        for drone in edge.drones_on_the_edge:
            # 드론의 현재 위치
            drone_pos = [drone.latitude, drone.longitude]
            # 드론의 다음 목적지 위치
            if(len(drone.destinations)==0):
               continue
            next_dest = [drone.destinations[0].latitude, drone.destinations[0].longitude]
            
            # 교점까지의 거리와 다음 목적지까지의 거리 비교
            # 교점까지의 방향 벡터 계산
            direction_to_intersection = [
                intersection_pos[0] - drone_pos[0],
                intersection_pos[1] - drone_pos[1]
            ]
            
            # 목적지까지의 방향 벡터 계산 
            direction_to_dest = [
                next_dest[0] - drone.prev_station.latitude,  #drone에서 목적지 벡터를 이전역에서 다음역 벡터로 바꿈
                next_dest[1] - drone.prev_station.longitude
            ]
            
            # 두 방향 벡터의 내적이 음수이면 서로 반대 방향
            dot_product = (direction_to_intersection[0] * direction_to_dest[0] + 
                         direction_to_intersection[1] * direction_to_dest[1])
            
            # 반대 방향이면 이미 교점을 지난 것이므로 다음 드론 확인
            distance_to_intersection = haversine([drone.latitude, drone.longitude], intersection_pos)
            if dot_product > 0 or (dot_product <=0 and distance_to_intersection < 0.020): # 10m 정도는 지나야 다음 차례 넘김 착륙 때문 
              leading_drones.append(drone)
              break  # 해당 간선의 leading 드론을 찾았으므로 다음 간선으로
            
            # 교점까지의 거리가 다음 목적지까지의 거리보다 크면 아직 교점을 지나지 않은 것
                
    # Leading 드론 간에 우선순위 부여 필요. -> 출발 시간 기준으로
    # leading 드론들끼리 거리 비교
    # 교점과의 거리가 0.03km(30m) 이상인 드론 제외
    filtered_drones = []
    for drone in leading_drones:
        distance_to_intersection = haversine([drone.latitude, drone.longitude], intersection_pos)
        #print(f"{drone.id}의 교점까지의 거리 : {distance_to_intersection}")
        if distance_to_intersection < 0.1:
            filtered_drones.append(drone)
    leading_drones = filtered_drones
    #drone_queue에 복사 (이륙 스케쥴링을 위함)
    intersection.drone_queue = leading_drones[:]
    # 교점과 가장 가까운 드론 찾기
    if len(leading_drones) > 0:
      closest_drone = min(leading_drones, 
                          key=lambda drone: haversine([drone.latitude, drone.longitude], intersection_pos))
      prior_drone = closest_drone
      if haversine([prior_drone.latitude, prior_drone.longitude], intersection_pos) >= 0.06:
      # prior_drone = leading_drones[0]
        if len(leading_drones) > 0:
          prior_drone = min(leading_drones, key=lambda drone: drone.take_off_time) # 이륙한지 오래된 드론 부터 통과
      # 통과 드론 제외하고 나머지 드론들 정지
      for drone in leading_drones:
        if drone != prior_drone:
          drone.go_flag = 0
      prior_drone.go_flag *= 1
      if(intersection.is_station and prior_drone.go_flag == 1 and intersection.station == prior_drone.destinations[0]) :
         #통과하는 교점이 역이고, 통행권을 얻은 경우
          prior_drone.add_to_next_edge()


def check_collision_of_all_intersections() :
  for intersection in intersections:
    check_collision_of_one_intersection(intersection)



def check_collision_in_edge(edge) :
  if(len(edge.drones_on_the_edge) == 0) :
    return
  i=1
  while True:
    if(i>=len(edge.drones_on_the_edge)) :
      break
    distance = find_distance_between_2_drones(edge.drones_on_the_edge[i], edge.drones_on_the_edge[i-1])
    if distance < 0.02 :
      edge.drones_on_the_edge[i].go_flag = 0
    else :
      edge.drones_on_the_edge[i].go_flag *= 1
    i+=1

def check_collision_in_all_edges() :
  for edge in edges :
    check_collision_in_edge(edge)


def check_all_collision() :
  for drone in mission_drones :
    if(drone.take_off_time is not None) :
      drone.go_flag = 1
  check_collision_in_all_edges()
  check_collision_of_all_intersections()
  return