# flask_server.py

#import mysql.connector
from flask import Flask,render_template, jsonify, request
from drone import get_drone_status
import threading
import mqtt_client, weather_api
from dotenv import load_dotenv
import os
from path_planning import *
from delivery import Delivery

load_dotenv()

db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')

app = Flask(__name__)

# 종료 이벤트
shutdown_event = threading.Event()

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/pathfinding', methods=['POST'])
def pathfinding():
    
    cname = request.form['cname']# 배송품 이름
    sname = request.form['sname']
    dname = request.form['dname']

    new_delivery = Delivery(cname, sname, dname)
    waiting_delivery.append(new_delivery)
    # 경로 계산 로직 
    #routes.append(search_route(get_station_by_name(sname), get_station_by_name(dname)))
    # print(f"출발지 : {sname}, 목적지 : {dname}의 경로 계산 완료!")

    # 경로 전달


    return request.json


# 임시 현재 드론 상태를 반환하는 엔드포인트
# @app.route('/mission_drones', methods=['GET'])
# def get_mission_drones():
#     drones = mission_drones[:]  # 드론 상태를 가져옴
#     json = []
#     for drone in drones:
#         drone_dict = {
#          "drone_id" : drone.id,
#         }
#         json.append(drone_dict)
#     print(f"\n{drones}\n")
#     return jsonify(json)

# # 임시 현재 드론 상태를 반환하는 엔드포인트
# @app.route('/waiting_drones', methods=['GET'])
# def get_waiting_drones():
#     drones = waiting_drones[:]  # 드론 상태를 가져옴

#     print(f"\n{drones}\n")
#     return jsonify(drones)



@app.route('/stations/flyable', methods=['GET'])
def get_all_stations_flyable():
    stations_status = [{
        'station_name': station.name,
        'is_flyable': station.is_flyable
    } for station in stations]
    
    return jsonify(stations_status)


#Flask 서버를 실행
def run_flask():
    app.run(host='127.0.0.1', port=5000)
    
    

if __name__ == '__main__':
    # MQTT 클라이언트를 별도의 스레드에서 실행
    mqtt_thread = threading.Thread(target=mqtt_client.start_mqtt_client)
    mqtt_thread.start()
    # 경로 탐색 모듈 초기화
    initialize_path_planning_module()
    # Flask 서버 실행
    try:
        run_flask()
        
    except KeyboardInterrupt:
        print("Flask server shutting down...")
        shutdown_event.set()  # 종료 이벤트 설정
        mqtt_client.client.loop_stop()  # MQTT 클라이언트 정지