# weather_api.py

import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os


load_dotenv()



import os
import requests
from datetime import datetime, timedelta

def get_station_weather(station):
    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
    service_key = os.getenv('WEATHER_API_KEY')

    now = datetime.now()

    # 자정인 경우 전날 23시 데이터 사용
    if now.hour == 0:
        base_date = (now - timedelta(days=1)).strftime('%Y%m%d')
        base_time = '2300'
    else:
        base_date = now.strftime('%Y%m%d')
        base_time = f'{now.hour:02d}00'

    params = {
        'serviceKey': service_key,
        'numOfRows': 10,
        'pageNo': 1,
        'dataType': 'JSON',
        'base_date': base_date,
        'base_time': base_time,
        'nx': station.grid_x,
        'ny': station.grid_y
    }

    try:
        res = requests.get(url=url, params=params)
        data = res.json()['response']['body']['items']['item']
        
        weather_info = {
            'is_raining': False,  # 비가 오는지 여부
            'wind_direction': 0,  # 풍향 (VEC)
            'wind_speed': 0  # 풍속 (WSD)
        }
        
        for item in data:
            if item['category'] == 'PTY':  # 강수 형태
                weather_info['is_raining'] = int(item['obsrValue']) > 0
            elif item['category'] == 'VEC':  # 풍향
                weather_info['wind_direction'] = float(item['obsrValue'])
            elif item['category'] == 'WSD':  # 풍속
                weather_info['wind_speed'] = float(item['obsrValue'])
            #print(weather_info)
        return weather_info

    except Exception as e:
        print(f"날씨 정보 조회 실패: {e}")
        return {
            'is_raining': False,
            'wind_direction': 0,
            'wind_speed': 0
        }
