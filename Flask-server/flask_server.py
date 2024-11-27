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
    cname = "배송품 이름"# 배송품 이름
    
    sname = request.form['sname']
    dname = request.form['dname']

    new_delivery = Delivery(cname, sname, dname)
    waiting_delivery.append(new_delivery)
    # 경로 계산 로직 
    #routes.append(search_route(get_station_by_name(sname), get_station_by_name(dname)))
    # print(f"출발지 : {sname}, 목적지 : {dname}의 경로 계산 완료!")

    # 경로 전달


    return request.json


@app.route('/send_control_command', methods=['GET'])
def send_control_command():
    # 요청으로부터 제어 명령 데이터를 가져옴
    command_data = request.json

    # MQTT 클라이언트에 제어 명령 데이터 전송
    mqtt_client.publish_control_command(command_data)
    print(f"Control command sent to MQTT: {command_data}")

    return jsonify({"status": "Command sent", "command": command_data})


# 임시 현재 드론 상태를 반환하는 엔드포인트
@app.route('/drones', methods=['GET'])
def get_drones():
    drones = get_drone_status()  # 드론 상태를 가져옴

    print(f"\n{drones}\n")
    return jsonify(drones)

@app.route('/stations/flyable', methods=['GET'])
def get_all_stations_flyable():
    stations_status = [{
        'station_name': station.name,
        'is_flyable': station.is_flyable
    } for station in stations]
    
    return jsonify(stations_status)

@app.route('/drone/battery', methods=['GET'])
def get_drone_battery():
    battery_status = {}
    
    # waiting_drones 배터리 상태
    for drone in waiting_drones:
        battery_status[f"waiting_drone_{drone.id}"] = {
            "battery": drone.battery_status,
            "last_updated": time.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    # mission_drones 배터리 상태    
    for drone in mission_drones:
        battery_status[f"mission_drone_{drone.id}"] = {
            "battery": drone.battery_status,
            "last_updated": time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
    return jsonify(battery_status)

# 테스트용 엔드포인트
@app.route('/test_publish', methods=['GET'])
def test_publish():
    print("test_publish called!")
    test_command = {

        # "command": "SET_MODE",
        # "mode": "GUIDED",
        # "sys_id": 1,

        # "command": "ARM",
        # "sys_id": 1,
        # "comp_id": 1

        # "command": "TAKEOFF",
        # "sys_id": 1,
        # "comp_id": 1,
        # "altitude": 30

        # "command": "MOVE_TO",
        # "latitude": 35.360489,
        # "longitude": 149.169093,
        # "altitude": 30

        "command": "LAND",
        "sys_id": 1,
        "comp_id": 1
    }
    mqtt_client.publish_control_command(test_command)
    return jsonify({"status": "Test command sent", "command": test_command})


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