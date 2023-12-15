import simpy 
import numpy as np
import random 

'''
1. 각 차량의 랜덤으로 차선 변경하여 초기 위치에 생성 (완료)
2. 주행 (완료)
3. DOCA에 진입전 약 30미터에 스케줄링 
4. DOCA에 주행시 메시지 전송 (V2V)
5. 주행시 같이 TCC 점수 계산 
6. TTC점수가 일정 점수에 도달하면 주의 메시지 브로드 캐스트 
7. 브로드 캐스트 이후 리스케줄링 진행 
8. 사고 발생시 리스케줄링 된 리소스로 안전메시지 브로드 캐스트 전송 
'''

#doca 초기 설정
doca_start = 500
doca_end = 1000
#resource pool
num_subchannels = 1
num_subframes = 10
available_resources = set((sc, sf) for sc in range(num_subchannels) for sf in range(num_subframes))


def vehicle(env, name, speed, position, time_interval):
    total_position = position
    executed = False
    executed2 = False
    resource_id = None
    while True:
        total_position += speed * time_interval / 3600
        lane = random.randint(1, 4)
        #print(f"Time {env.now}: Vehicle {name} at position {total_position} in lane {lane}")
        for _ in range(300):
            total_position += position + speed * time_interval / 3600

            #print(total_position)
            if doca_start <= total_position <= doca_end:
                #print("in doca")
                print(f"Vehicle ID : {name} | Current Position: {total_position} | Lane : {lane} | DOCA State : in DOCA | Resource ID : {resource_id}")
            elif doca_start - 50 <= total_position <= doca_start:
                if not executed:
                    resource_id = allocate(available_resources)
                    print("allocation")
                    executed = True
                print(f"Vehicle ID : {name} | Current Position: {total_position} | Lane : {lane} | DOCA State : Approach DOCA | Resource ID : {resource_id}")
                #print("approach doca")
            elif doca_end < total_position:
                if not executed2:
                    release(available_resources, resource_id)
                    print(f"Release | ID : {resource_id}")
                    executed2 = True
                print(f"Vehicle ID : {name} | Current Position: {total_position} | Lane : {lane} | DOCA State : Out DOCA | Resource ID : {resource_id}")
            else:
                print(f"Vehicle ID : {name} | Current Position: {total_position} | Lane : {lane} | DOCA State : Not DOCA | Resource ID : {resource_id}")
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


# 환경 생성
env = simpy.Environment()

# 여러 차량 프로세스 생성 및 환경에 추가
for i in range(10):
    env.process(vehicle(env, f'Vehicle {i}', 140, 0, 100))

# 시뮬레이션 실행
env.run(until=70000)  # 시뮬레이션 지속 시간 설정
print(available_resources)