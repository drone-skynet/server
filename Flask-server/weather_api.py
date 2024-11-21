# weather_api.py

import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import math

load_dotenv()



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

    print(f"API 요청 파라미터: {params}")  # 파라미터 출력

    try:
        res = requests.get(url=url, params=params)
        print(f"API 응답: {res.text}")  # 응답 내용을 출력
        data = res.json()['response']['body']['items']['item']
        
        for item in data:
            if item['category'] == 'PTY':  # 강수형태
                return int(item['obsrValue']) > 0  # True면 비가 옴
                
        return False  # 기본값은 비가 안옴
        
    except Exception as e:
        print(f"날씨 정보 조회 실패: {e}")
        return False