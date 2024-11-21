from weather_api import get_station_weather
from station import Station

def test_get_station_weather():
    # 테스트용 Station 객체 생성 (예: 장지역)
    test_station = Station(
        id="test_id",
        name="장지",
        longitude=127.126191,
        latitude=37.478703,
        capacity=10,
        grid_x=61,
        grid_y=124
    )
    
    # 날씨 정보 가져오기
    is_raining = get_station_weather(test_station)
    
    # 결과 출력
    if is_raining:
        print("비가 오고 있습니다.")
    else:
        print("비가 오지 않습니다.")

if __name__ == "__main__":
    test_get_station_weather()