import json
import mysql.connector
import requests
from dotenv import load_dotenv
import os

load_dotenv()
# MySQL 데이터베이스 연결 정보 설정
DB_HOST = 'localhost'
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = 'drone'

# JSON 파일 경로
JSON_FILE_PATH = './station_info.json'

# 네이버 API 정보 설정
NAVER_CLIENT_ID = os.getenv('NAVER_CLIENT_ID')
NAVER_CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET')
NAVER_GEOCODE_URL = 'https://naveropenapi.apigw.ntruss.com/map-reversegeocode/v2/gc'

def get_address_from_coordinates(latitude, longitude):
    headers = {
        'X-NCP-APIGW-API-KEY-ID': NAVER_CLIENT_ID,
        'X-NCP-APIGW-API-KEY': NAVER_CLIENT_SECRET
    }
    params = {
        'coords': f'{longitude},{latitude}',
        'orders': 'addr',
        'output': 'json'
    }
    response = requests.get(NAVER_GEOCODE_URL, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        if data['results']:
            return data['results'][0]['region']['area1']['name']
    return None



# JSON 파일을 MySQL에 저장하는 함수
def store_json_to_mysql():
    connection = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    try:
        cursor = connection.cursor()

        # JSON 파일 읽기
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
            records = data['DATA']

            insert_sql = """
            INSERT INTO station (station_id, station_name, station_longitude, station_latitude, grid_x, grid_y)
            VALUES (uuid(), %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                station_name = VALUES(station_name),
                grid_x = VALUES(grid_x),
                grid_y = VALUES(grid_y)
            """

            for record in records:
                station_name = record['bldn_nm']
                longitude = float(record['lot'])
                latitude = float(record['lat'])
                grid_x = int(record['grid_x'])
                grid_y = int(record['grid_y'])  


                # 위도, 경도로 주소 가져오기
                address_area = get_address_from_coordinates(latitude, longitude)

                # 주소가 서울인 경우에만 삽입
                word="서울"
                if address_area!=None and word in address_area:
                    cursor.execute(insert_sql, (station_name, longitude, latitude, grid_x, grid_y))
        
        connection.commit()
    finally:
        cursor.close()
        connection.close()

if __name__ == '__main__':
    store_json_to_mysql()