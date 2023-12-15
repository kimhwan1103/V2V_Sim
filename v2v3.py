import random 
import numpy as np 
import simpy 
import threading
from collections import deque

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

'''

'''

vehicles = deque(maxlen=10)
doca_start = 500
doca_end = 1000
vehicle_id = 0

def vehicle(speed, position, time_interval, vehicle_id):
    lane = random.randint(1, 4)
    total_position = 0
    vehicle_id += 1
    for _ in range(300):
        total_position += position + speed * time_interval / 3600
        vehicles.append((total_position, lane))

        #print(total_position)
        if doca_start <= total_position <= doca_end:
            #print("in doca")
            print(f"Vehicle ID : {vehicle_id} | Current Position: {vehicles[-1]} | Lane : {lane} | DOCA State : in DOCA")
        elif doca_start - 50 <= total_position <= doca_start:
            print(f"Vehicle ID : {vehicle_id} | Current Position: {vehicles[-1]} | Lane : {lane} | DOCA State : Approach DOCA")
            #print("approach doca")
        else:
            print(f"Vehicle ID : {vehicle_id} | Current Position: {vehicles[-1]} | Lane : {lane} | DOCA State : Out DOCA")
            #print("out doca")
        #vehicles.append(total_position)
        #print(total_position)


threads = []
for vehicle_id in range(1, 11):
    t = threading.Thread(target=vehicle, args=(140, 0, 100, vehicle_id))
    threads.append(t)
    t.start()
'''
for _ in range(10):
    t = threading.Thread(target=vehicle, args=(140, 0, 100, vehicle_id))
    threads.append(t)
    t.start()
'''
for t in threads:
    t.join()