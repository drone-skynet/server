from intersection import Intersection, intersections
from edge import edges
import numpy as np
import mysql.connector


def solution_of_2_edges(edge1, edge2) :
  slope_edge1 = (edge1.destination.latitude - edge1.origin.latitude)/(edge1.destination.longitude - edge1.origin.longitude)
  slope_edge2 = (edge2.destination.latitude - edge2.origin.latitude)/(edge2.destination.longitude - edge2.origin.longitude)
  matA = np.array([[slope_edge1, -1], [slope_edge2, -1]])
  matB = np.array([edge1.origin.longitude*slope_edge1 - edge1.origin.latitude,edge2.origin.longitude*slope_edge2 - edge2.origin.latitude])
  x,y = np.linalg.solve(matA, matB)
  edge1_upper_x = max(edge1.origin.longitude, edge1.destination.longitude)
  edge1_lower_x = min(edge1.origin.longitude, edge1.destination.longitude)
  edge2_upper_x = max(edge2.origin.longitude, edge2.destination.longitude)
  edge2_lower_x = min(edge2.origin.longitude, edge2.destination.longitude)
  upper_end_x = min(edge1_upper_x, edge2_upper_x)
  lower_end_x = max(edge1_lower_x, edge2_lower_x)
  #print("점들", x,edge1.origin.longitude, edge1.destination.longitude,edge1.origin.longitude, edge1.destination.longitude)
  if(lower_end_x > upper_end_x) :
    return None
  #print("위점:",upper_end_x,"아래점:",lower_end_x)
  x = round(x, 6)
  y = round(y, 6)
  if(upper_end_x+0.000001 > x and lower_end_x - 0.000001 < x) : #선 사이에서 교점
    #print("교점 찾음 :", x, y)
    intersection = Intersection([edge1, edge2], y, x)
    return intersection
  return None


def find_all_intersections() :
  edges_len = len(edges)
  for i in range(edges_len):
    for j in range(i+1, edges_len):
      if(edges[i].origin == edges[j].destination and edges[i].destination == edges[j].origin):
        continue
      intersection = solution_of_2_edges(edges[i], edges[j])
      if(intersection is not None) :
        is_same_intersection = False
        for its in intersections :
          is_same_intersection = its.fuse_same_point(intersection)
          if(is_same_intersection) :
            break
        if(not is_same_intersection) :
          intersections.append(intersection)
  #print("중복 제거된 교점 리스트",intersections) #역도 포함됨
  print("교점 수:",len(intersections))
  return


def save_intersections_to_db(intersections):
    try:
        # MySQL 연결 설정
        connection = mysql.connector.connect(
            host='localhost',
            database='drone',
            user='your_username',
            password='your_password'
        )
        
        cursor = connection.cursor()
        
        # SQL 쿼리 준비
        sql = """INSERT INTO intersections 
                (latitude, longitude, edge_count) 
                VALUES (%s, %s, %s)"""
                
        # 각 교점에 대해 데이터 삽입
        for intersection in intersections:
            values = (
                intersection.latitude,
                intersection.longitude,
                len(intersection.edges)
            )
            cursor.execute(sql, values)
            
        # 변경사항 저장
        connection.commit()
        print(f"{len(intersections)}개의 교점이 데이터베이스에 저장되었습니다.")
        
    except mysql.connector.Error as error:
        print(f"Failed to insert record into MySQL table: {error}")
        
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed")