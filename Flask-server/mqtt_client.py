# mqtt_client.py

import paho.mqtt.client as mqtt
import drone
import json

from pymavlink.dialects.v20 import common as mavlink2
from pymavlink import mavutil

# MQTT 브로커 정보
MQTT_BROKER = 'localhost'
# PUB_TOPIC = '/Mobius/SJ_Skynet/GCS_Data/TestDrone1/sitl'
SUB_TOPIC = '/Mobius/SJ_Skynet/Drone_Data/#'

def pub_topic(sys_id) :
    return f'/Mobius/SJ_Skynet/GCS_Data/TestDrone{251-int(sys_id)}/sitl'

# 기본값 설정
"""
drone_info = {
    'drone_id': None,
    'isArmed': None,
    'isGuided': None,
    'latitude': None,
    'longitude': None,
    'altitude': None,
    'vx' : None,
    'vy' : None,
    'vz' : None,
    'battery_status': None,
    'mission_status': None
}
"""

# MQTT 클라이언트 설정
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

# 연결 시 호출되는 콜백 함수
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("\n\nSuccess Connect!\n\n")
        client.subscribe(SUB_TOPIC)  # 토픽을 구독합니다.

    if reason_code > 0:
        print(f'\n\nConnected with result code {reason_code}\n\n')


# 메시지를 수신할 때 호출되는 콜백 함수 수정
def on_message(client, userdata, message):
    topic = message.topic  # 수신된 메시지의 토픽
    payload = message.payload  

    #print(f"\nReceived message on topic '{topic}': {payload}\n")
    
    # 각 토픽에 따라 get_drone_status 호출
    get_drone_status(payload)


# 수신받은 드론 정보를 저장
def get_drone_status(payload):
    drone_info = {
        'drone_id': None,
        'isArmed': None,
        'isGuided': None,
        'latitude': None,
        'longitude': None,
        'altitude': None,
        'vx' : None,
        'vy' : None,
        'vz' : None,
        'battery_status': None,
        'mission_status': None
    }
    # 바이너리 메시지를 디코딩하여 MAVLink 메시지 객체 생성
    msg = decode_mavlink_message(bytearray(payload))
    # print(f"type of msg : {type(msg)}\ndecoded msg : {msg}")
    # 메시지 유형에 따라 정보 저장
    drone_info['drone_id'] = msg.get_srcSystem()
    if isinstance(msg, mavlink2.MAVLink_heartbeat_message):
        drone_info['isArmed'] = (msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED) != 0
        drone_info['isGuided'] = (msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_GUIDED_ENABLED) != 0

    elif isinstance(msg, mavlink2.MAVLink_global_position_int_message):
        drone_info['latitude'] = msg.lat / 1e7  # 위도
        drone_info['longitude'] = msg.lon / 1e7  # 경도
        drone_info['altitude'] = msg.alt / 1000.0  # 고도
        drone_info['vx'] = msg.vx / 100.0  # X 방향 속도 (m/s)
        drone_info['vy'] = msg.vy / 100.0  # Y 방향 속도 (m/s)
        drone_info['vz'] = msg.vz / 100.0  # Z 방향 속도 (m/s)

    elif isinstance(msg, mavlink2.MAVLink_battery_status_message):
        drone_info['battery_status'] = msg.battery_remaining

    elif isinstance(msg, mavlink2.MAVLink_mission_current_message):
        drone_info['mission_status'] = msg.seq  # 현재 미션 시퀀스

    # print(f"All drone_info init check : \n")
    # for value in drone_info.values():
    #     print(f"{value}  ")

    # 모든 정보가 수집된 경우에만 드론 객체 생성
    if (drone_info['drone_id'] != 0):
        drone_obj = drone.Drone(
            drone_info['drone_id'],
            drone_info['isArmed'],
            drone_info['isGuided'],
            drone_info['latitude'],
            drone_info['longitude'],
            drone_info['altitude'],
            drone_info['vx'],
            drone_info['vy'],
            drone_info['vz'],
            drone_info['battery_status'],
            drone_info['mission_status']
        )
        # print(f"\nCall update_drone\n")
        drone.update_drone_status(drone_obj)
        # 드론 정보 초기화


# MAVLink 메시지 디코딩 함수
def decode_mavlink_message(mav_msg_byte):

    mav = mavlink2.MAVLink(None)  # 연결 없이 MAVLink 객체 생성
    try:
        # 메시지 파싱
        msg = mav.decode(mav_msg_byte)
        return msg
    except Exception as e:
        return f"Failed to decode message: {e}"

# # MAVLink 메시지 디코딩 함수
# def decode_mavlink_message(mav_msg_byte):

#     mav = mavlink2.MAVLink(None)  # 연결 없이 MAVLink 객체 생성

#     # MAVLink 메시지의 헤더를 디코드 (6바이트)
#     header_format = '<BBBBBB'  # MAVLink 헤더 구조
#     header_size = struct.calcsize(header_format)

#     # 헤더와 페이로드 분리
#     header = mav_msg_byte[:header_size]
#     message_id, system_id, component_id, mav_msg_byte_length, msg_sequence, system_time = struct.unpack(header_format, header)

#     try:
#         # 메시지 파싱
#         msg = mav.decode(mav_msg_byte)
#         return system_id, msg
#     except Exception as e:
#         return f"Failed to decode message: {e}"


# 제어 명령을 발행하는 함수
def publish_control_command(command_data):
    command = command_data.get("command")
    mav_msg = None

    # print(f"\ncommand : {command}\n")


    if command == "SET_MODE":
        # SET_MODE 명령 (GUIDED 또는 MANUAL 모드 전환)
        sys_id = command_data.get("sys_id")
        comp_id = command_data.get("comp_id")
        mode = command_data.get("mode")
        if(mode == "GUIDED") :
            custom_mode = 4   # GUIDED 모드: custom_mode=4, MANUAL 모드: custom_mode=0
        
        elif(mode == "BREAK") :
            custom_mode = 17
            
        base_mode = mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED  # custom_mode 사용 플래그 설정

        mav_msg = mavlink2.MAVLink_set_mode_message(
            target_system=sys_id,
            base_mode=base_mode,
            custom_mode=custom_mode
        )


    elif command == "ARM":
        # ARM 명령
        sys_id = command_data.get("sys_id")
        comp_id = command_data.get("comp_id")

        mav_msg = mavutil.mavlink.MAVLink_command_long_message(
            target_system = sys_id,             # 시스템 ID (드론의 고유 식별자)
            target_component = comp_id,         # 컴포넌트 ID
            command=mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,   # 명령: ARM
            confirmation=0,
            param1=1,  # 1은 ARM, 0은 DISARM
            param2=0, param3=0, param4=0, param5=0, param6=0, param7=0
        )

    elif command == "TAKEOFF":
        # TAKEOFF 명령
        sys_id = command_data.get("sys_id")
        comp_id = command_data.get("comp_id")
        altitude = command_data.get("altitude", 10)  # 기본 이륙 고도

        mav_msg = mavutil.mavlink.MAVLink_command_long_message(
            target_system=sys_id,
            target_component=comp_id,
            command=mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
            confirmation=0,
            param1=0, param2=0, param3=0, param4=0,
            param5=0, param6=0,  # 위도/경도는 생략
            param7=altitude  # 목표 고도
        )

    elif command == "MOVE_TO":
        # 특정 위치로 이동하는 MOVE_TO 명령
        sys_id = command_data.get("sys_id")
        comp_id = command_data.get("comp_id")

        mav_msg = mavutil.mavlink.MAVLink_set_position_target_global_int_message(
            0,  # time_boot_ms (ignored)
            sys_id,
            comp_id,
            mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,  # frame
            0b0000111111111000,  # type_mask (only positions enabled)
            int(command_data['latitude'] * 1e7),  # 위도
            int(command_data['longitude'] * 1e7),  # 경도
            command_data['altitude'],  # 고도
            0, 0, 0,  # x, y, z velocity (not used)
            0, 0, 0,  # x, y, z acceleration (not used)
            0, 0  # yaw, yaw_rate (not used)
        )

    elif command == "LAND":
        # LAND 명령
        sys_id = command_data.get("sys_id")
        comp_id = command_data.get("comp_id")

        mav_msg = mavutil.mavlink.MAVLink_command_long_message(
            target_system=sys_id,
            target_component=comp_id,
            command=mavutil.mavlink.MAV_CMD_NAV_LAND,
            confirmation=0,
            param1=0, param2=0, param3=0, param4=0,
            param5=0, param6=0, param7=0
        )

    # print(f"\nmav_msg : \n{mav_msg}")
    pub_topic1 = pub_topic(command_data.get("sys_id"))
    if mav_msg:
        mavlink_msg_bytes = mav_msg.pack(mavutil.mavlink.MAVLink('', 255, 190))    # 파라미터 : 연결객체, MAVLink Version, system_id
        client.publish(pub_topic1, mavlink_msg_bytes)

        # # 비트 문자열 변환
        # mavlink_message_bits = ''.join(format(byte, '08b') for byte in mavlink_msg_bytes)

        # # 4비트 단위 띄어쓰기
        # formatted_bits = ' '.join(mavlink_message_bits[i:i+4] for i in range(0, len(mavlink_message_bits), 4))
        # print("\nFormatted bits:", formatted_bits)

        # 디코딩
        # decoded_msg = decode_mavlink_message(bytearray(mavlink_msg_bytes))
        # print("\nDecoded message:", decoded_msg)

        #print(f"\nPublished MAVLink command to {pub_topic1}: {mavlink_msg_bytes}")
    else:
        print(f"\nUnknown command: {command}")


#MQTT 클라이언트를 시작
def start_mqtt_client():
    print("\n\nStart MQTT Client\n\n")
    client.on_connect = on_connect
    client.on_message = on_message  
    client.connect(MQTT_BROKER)
    client.loop_start()
    