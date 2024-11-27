# flask_server.py

#import mysql.connector
from flask import Flask,render_template, jsonify, request
from drone import get_drone_status, get_mission_drones
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

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/delivery_info')
def delivery_info():
    return render_template('delivery_info.html')

# 임시 현재 배송 정보를 반환하는 엔드포인트
@app.route('/api/delivery_info', methods=['GET'])
def api_delivery_info():
    drone = Delivery.drone
    drone_info = {
        "id": drone.id,
        "battery_status": drone.battery_status,
        "altitude": drone.altitude - drone.home_alt,
        "waypoints": drone.destinations,
        "edge_origin_name": drone.edge.origin.name,
        "edge_destinations_name": drone.edge.destination.name,
        "delivery_content": drone.delivery.content,
        "delivery_detination": drone.delivery.destination,
        "edt": drone.edt
    }
    return jsonify(drone_info)


# 임시 현재 운행 중인 드론 상태를 반환하는 엔드포인트
@app.route('/api/mission_drones', methods=['GET'])
def get_drones():
    mission_drones = get_mission_drones()  # 드론 상태를 가져옴

    # 드론 객체를 JSON 직렬화 가능한 형태로 변환
    mission_drones_data = [drone.to_dict() for drone in mission_drones]

    print(f"\n{mission_drones_data}\n")
    return jsonify(mission_drones_data)


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