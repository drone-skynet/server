import joblib
import math
import pandas as pd

# 학습된 모델 로드
def load_model(model_path):
    return joblib.load(model_path)

# 효율 점수 계산 함수
def calculate_efficiency_score(drone_direction, wind_direction, wind_speed):
    # 상대각도 계산
    relative_angle = (wind_direction - drone_direction + 360) % 360 
    relative_angle = math.radians(relative_angle) # 라디안으로 변환

    # 효율점수 계산
    efficiency_score = -math.cos(relative_angle) * wind_speed
    return efficiency_score

# 예측 함수
def predict_delivery_time(model, distance, wind_speed, wind_direction, drone_direction):
    efficiency_score = calculate_efficiency_score(drone_direction, wind_direction, wind_speed)
    input_data = pd.DataFrame([[distance, efficiency_score]], columns=['distance', 'efficiency_score'])
    return model.predict(input_data)[0]
