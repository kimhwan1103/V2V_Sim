import simpy 
import numpy as np
import random 

'''
1. 각 차량의 랜덤으로 차선 변경하여 초기 위치에 생성 (완료)
2. 주행 (완료)
3. DOCA에 진입전 약 30미터에 스케줄링 (완료)
4. DOCA 탈출 후 리소스 해제 (완료)(검토 필요)
5. DOCA에 주행시 메시지 전송 (V2V) (진행중)
6. 주행시 같이 TCC 점수 계산 (완료)
7. TTC점수가 일정 점수에 도달하면 주의 메시지 브로드 캐스트 
8. 브로드 캐스트 이후 리스케줄링 진행 
9. 사고 발생시 리스케줄링 된 리소스로 안전메시지 브로드 캐스트 전송
10. 사고 발생시 차량 정지 
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

vehicle_states = {}

def vehicle(env, name, position, time_interval):
    global vehicle_states
    total_position = position
    executed = False
    executed2 = False
    resource_id = None
    other_vehicle = None
    speed = random.randint(100, 120)
    lane = random.randint(1, 4)
    crashed = False
    while True:
        ttc_value = None
        if not crashed:
            total_position += speed * time_interval / 3600
        #lane = random.randint(1, 4)
        #print(f"Time {env.now}: Vehicle {name} at position {total_position} in lane {lane}")
       
        total_position += position + speed * time_interval / 3600
        
        vehicle_states[name] = {'position': total_position, 'speed': speed, 'lane': lane}

        for other_name, other_state in vehicle_states.items():
            if name != other_name and lane == other_state['lane']:
                ttc_value = calculate_ttc(total_position, speed, other_state['position'], other_state['speed'])
                other_vehicle = other_name
                if ttc_value < 0.4:
                    print(f"{bcolors.WARNING}Emergency TTC Vehicle : {name} | Other Vehicle : {other_name}{bcolors.ENDC}")
                if ttc_value <= 0.3:
                    print(f"{bcolors.FAIL}Vehicle Crash {name} : {other_name}{bcolors.ENDC}")
                    #crashed = True
                    #speed = 0
                    

        #print(total_position)
        if doca_start <= total_position <= doca_end:
            #print("in doca")
            print(f"Vehicle ID : {name} | Current Position: {int(total_position)} | Lane : {lane} | DOCA State : in DOCA | Resource ID : {resource_id} | SPEED : {speed} | TTC_State : {ttc_value} | Other Vehicle : {other_vehicle} | Crashed : {crashed}")
        elif doca_start - 50 <= total_position <= doca_start:
            if not executed:
                resource_id = allocate(available_resources)
                print("allocation")
                executed = True
            print(f"Vehicle ID : {name} | Current Position: {int(total_position)} | Lane : {lane} | DOCA State : Approach DOCA | Resource ID : {resource_id} | SPEED : {speed} | TTC_State : {ttc_value} | Other Vehicle : {other_vehicle}  | Crashed : {crashed}")
    
        #elif doca_end < total_position:
        #    if not executed2:
        #        release(available_resources, resource_id)
        #        resource_id = None
        #        print(f"Release | ID : {resource_id}")
        #        executed2 = True
        #    print(f"Vehicle ID : {name} | Current Position: {total_position} | Lane : {lane} | DOCA State : Out DOCA | Resource ID : {resource_id}")
        elif total_position > doca_end and not executed2:
            if resource_id is not None:
                release(available_resources, resource_id)
                print(f"Release | Vehicle ID : {name} | Resource ID : {resource_id}")
                resource_id = None
            executed2 = True
        else:
            print(f"Vehicle ID : {name} | Current Position: {int(total_position)} | Lane : {lane} | DOCA State : Not DOCA | Resource ID : {resource_id} | SPEED : {speed} | TTC_State : {ttc_value} | Other Vehicle : {other_vehicle} | Crashed : {crashed}")
        #yield env.timeout(time_interval)  # 시간 간격 만큼 대기
        yield env.timeout(random.expovariate(1.0 / (2.5 * time_interval)))

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

#CAM 메시지 전송
def CAM_send(CAM_size, periodicity):
    pass

#스케줄링
def scheduling():
    pass
    


# 환경 생성
env = simpy.Environment()

# 여러 차량 프로세스 생성 및 환경에 추가
for i in range(10):
    env.process(vehicle(env, f'Vehicle {i}', 0, 100))

# 시뮬레이션 실행
env.run(until=51000)  # 시뮬레이션 지속 시간 설정
print(available_resources)