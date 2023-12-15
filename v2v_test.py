import simpy
import numpy as np

# 시뮬레이션 파라미터
num_vehicles = 10
vehicle_speed = 140 / 3.6  # km/h를 m/s로 변환
resource_pool_size = 10  # 사용 가능한 서브프레임 수
transmission_power = 23  # dBm
cam_size = 190  # bytes
cam_periodicity = 0.1  # seconds
subframe_duration = 0.001  # seconds
doca_length = 500  # meters
env = simpy.Environment()

# 전송 및 수신 카운터
total_packets_sent = 0
successful_packets_received = 0

# 차량 모델
class Vehicle:
    def __init__(self, env, id, speed, radio_blocks):
        self.env = env
        self.id = id
        self.speed = speed
        self.radio_blocks = radio_blocks
        self.position = 0  # 초기 위치 0으로 설정
        self.action = env.process(self.run())

    def run(self):
        global total_packets_sent, successful_packets_received
        while True:
            # 도착 시간 간격은 Poisson 분포를 따릅니다.
            yield self.env.timeout(np.random.poisson(3))
            
            # 차량 이동
            self.position += self.speed * cam_periodicity
            self.position %= doca_length  # DOCA를 벗어나면 위치를 초기화
            
            # 라디오 자원 할당 및 메시지 전송
            resource_block = np.random.choice(self.radio_blocks)
            with resource_block.request() as req:
                yield req
                total_packets_sent += 1
                yield self.env.timeout(subframe_duration)
                # 여기서는 패킷 수신이 항상 성공한다고 가정합니다.
                successful_packets_received += 1
                print(f"Time {self.env.now}: Vehicle {self.id} transmitted a message on subframe {self.radio_blocks.index(resource_block)}.")

# 라디오 자원 블록 생성
radio_blocks = [simpy.Resource(env) for _ in range(resource_pool_size)]

# 차량 생성 및 시뮬레이션 시작
vehicles = [Vehicle(env, i, vehicle_speed, radio_blocks) for i in range(num_vehicles)]
env.run(until=10)  # 시뮬레이션을 10초 동안 실행

# PRR 계산
prr = successful_packets_received / total_packets_sent if total_packets_sent > 0 else 0
print(f"PRR: {prr:.2f}")
