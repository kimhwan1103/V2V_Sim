import simpy 
import numpy as np
import random
import time

'''
1. 각 차량의 랜덤으로 차선 변경하여 초기 위치에 생성 (완료)
2. 주행 (완료)
3. DOCA에 진입전 약 30미터에 스케줄링 (완료)
4. DOCA 탈출 후 리소스 해제 (완료)
5. DOCA에 주행시 메시지 전송 (V2V) (완료)
6. 주행시 같이 TCC 점수 계산 (완료)
7. TTC점수가 일정 점수에 도달하면 주의 메시지 브로드 캐스트 
8. 브로드 캐스트 이후 리스케줄링 진행 
9. 사고 발생시 리스케줄링 된 리소스로 안전메시지 브로드 캐스트 전송
10. 사고 발생시 차량 정지 (진행 중)
11. PRR 값 계산 (완료)
'''

#print문 색깔
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

#doca 초기 설정
doca_start = 500
doca_end = 1000
#resource pool
num_subchannels = 1
num_subframes = 10
available_resources = set((sc, sf) for sc in range(num_subchannels) for sf in range(num_subframes))

total_packet = 0
sucess_packet = 0

vehicle_states = {}

def vehicle(env, name, initial_position, time_interval):
    global vehicle_states, total_packet, sucess_packet

    #초기 설정
    position = initial_position
    speed = random.randint(100, 120)
    lane = random.randint(1,4)
    crashed = False
    resource_id = False
    other_vehicle = None
    executed = False
    executed2 = False
    cam = None

    while True:
        #충돌이 없는 경우 위치 업데이트
        if not crashed:
            position += speed * time_interval / 3600

        vehicle_states[name] = {'position' : position, 'speed' : speed, 'lane' : lane}
        cam = send_cam(name, vehicle_states[name])

        #다른 차량과의 충돌 및 TTC 계산
        ttc_value = None
        for other_name, other_state in vehicle_states.items():
            if name != other_name and lane == other_state['lane']:
                ttc_value = calculate_ttc(position, speed, other_state['position'], other_state['speed'])
                other_vehicle = other_name
                if ttc_value < 0.4:
                    print(f"{bcolors.WARNING}Emergency TTC Vehicle : {name} | Other Vehicle : {other_name}{bcolors.ENDC}")
                if ttc_value <= 0.3:
                    print(f"{bcolors.FAIL}Vehicle Crash {name} : {other_name}{bcolors.ENDC}")
        
        #OOC 구역 함수
        if doca_start <= position <= doca_end:
            print_vehicle_status(name, position, lane, "in DOCA", resource_id, speed, ttc_value, other_vehicle, crashed)
            #cam = send_cam(name, vehicle_states[name])
            #total_packet += 1

        elif doca_start - 50 <= position <= doca_start:
            if not executed:
                resource_id = allocate(available_resources)
                executed = True
            print_vehicle_status(name, position, lane, "Approach DOCA", resource_id, speed, ttc_value, other_vehicle, crashed)
        elif position > doca_end and not executed2:
            if resource_id is not None:
                release(available_resources, resource_id)
                resource_id = None
            executed2 = True
        else:
            print_vehicle_status(name, position, lane, "Not DOCA", resource_id, speed, ttc_value, other_vehicle, crashed)
        
        for other_name, other_state in vehicle_states.items():
            if other_name != name:
                receive_cam(name, other_name, other_state, 300)
            else:
                print(f"{bcolors.FAIL} cam recive FAIL {bcolors.ENDC}")

        # 시간 간격에 따라 대기
        yield env.timeout(random.expovariate(1.0 / (2.5 * time_interval)))

#로그 출력 함수
def print_vehicle_status(name, position, lane, doca_state, resource_id, speed, ttc_value, other_vehicle, crashed):
    print(f"Vehicle ID : {name} | Current Position: {int(position)} | Lane : {lane} | DOCA State : {doca_state} | Resource ID : {resource_id} | SPEED : {speed} | TTC_State : {ttc_value} | Other Vehicle : {other_vehicle} | Crashed : {crashed}")
   
def allocate(resources):
    if resources:
        resource = resources.pop()
        #print(resource)
        return resource
    return (None, 0)

def release(resources, resource_id):
    resources.add(resource_id)

#TTC 계산
def calculate_ttc(pos1, speed1, pos2, speed2):
    distance = abs(pos2 - pos1)
    relative_speed = abs(speed2 - speed1)
    if relative_speed == 0:
        return float('inf')
    return distance / relative_speed

#긴급 메시지 
def Emergency_msg():
    pass

#거리 계산
def calculate_distance(position1, position2):
    return abs(position1 - position2)

#차량 수신 범위 판단
def is_within_range(position1, position2, max_range):
    distance = calculate_distance(position1, position2)
    return distance <= max_range

received_messages = set()

#메시지 수신 처리
def receive_cam(receiver_name, sender_name, message, max_range):
    global sucess_packet
    #sender_position = message['position']
    #메시지 식별자 생성 
    message_id = (sender_name, message['position'])

    #중복 방지
    if message_id in received_messages:
        return 
    
    sender_position = message['position']
    receiver_position = vehicle_states[receiver_name]['position']
    if is_within_range(receiver_position, sender_position, max_range):
        print(f"{receiver_name} received a CAM from {sender_name}: {message}")
        sucess_packet += 1
        received_messages.add(message_id)

#CAM 생성 
def create_cam(vehicle_id, state):
    return {'vehicle_id': vehicle_id, 'position': state['position'], 'speed': state['speed'], 'lane': state['lane']}

#CAM 전송
def send_cam(vehicle_id, state):
    global total_packet
    cam_msg = create_cam(vehicle_id, state)
    print(f"CAM : {cam_msg}")
    total_packet += 1
    return cam_msg

#CAM 메시지 수신
def CAM_receive(cam_msg):
    print(cam_msg)

#PRR값 계산 
def prr():
    global sucess_packet, total_packet
    if total_packet == 0:
        return 0
    packet = (sucess_packet / total_packet) * 100
    print(f"PRR value : {packet}")
    return packet

#스케줄링
def scheduling():
    pass

# 환경 생성
env = simpy.Environment()

# 여러 차량 프로세스 생성 및 환경에 추가
for i in range(10):
    env.process(vehicle(env, f'Vehicle {i}', 0, 100))

# 시뮬레이션 실행
env.run(until=100000)  # 시뮬레이션 지속 시간 설정
print(available_resources)
print(f"total packet : {total_packet} | sucess packet : {sucess_packet}")
packet = prr()
print(f"PRR : {packet}")