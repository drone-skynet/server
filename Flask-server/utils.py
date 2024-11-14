from math import sin, cos, sqrt, atan2, radians

def haversine(coord1, coord2):
  # 지구의 반지름 (단위: km)
  R = 6371.0

  # 위도와 경도를 라디안으로 변환
  lat1, lon1 = radians(coord1[0]), radians(coord1[1])
  lat2, lon2 = radians(coord2[0]), radians(coord2[1])

  # 위도와 경도의 차이 계산
  dlat = lat2 - lat1
  dlon = lon2 - lon1

  # Haversine 공식
  a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
  c = 2 * atan2(sqrt(a), sqrt(1 - a))

  # 거리 계산
  distance = R * c
  return distance

def find_distance_between_2_drones(drone1, drone2) :
  return haversine([drone1.latitude, drone1.longitude], [drone2.latitude, drone2.longitude])

def find_edge_by_point(edges, origin, destination) :
  for edge in edges :
    if(edge.origin == origin and edge.destination == destination) :
      return edge
  return None