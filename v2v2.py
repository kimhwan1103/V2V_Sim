import numpy as np
import random

CAM_SIZE = 190  # Cooperative Awareness Message(CAM)의 크기 (바이트 단위)
CAM_PERIODICITY = 0.1  # CAM 전송 주기 (초 단위)
SUBFRAME_DURATION = 0.001  # 서브프레임의 지속 시간 (초 단위)
TRANSMISSION_RANGE = 600  # 차량의 전송 범위 (미터 단위)

class Vehicle:
    def __init__(self, id, position, speed):
        # 차량의 초기 설정: ID, 위치, 속도 및 리소스 ID
        self.id = id
        self.position = position
        self.speed = speed
        self.resource_id = None
        self.last_cam_transmission = -CAM_PERIODICITY  # 마지막 CAM 전송 시간 초기화
    
    def transmit_cam(self, current_time, other_vehicles, simulation):
        # 현재 시간과 마지막 CAM 전송 시간을 비교하여 CAM 전송 결정
        if current_time - self.last_cam_transmission >= CAM_PERIODICITY:
            self.last_cam_transmission = current_time
            #print(f"Vehicle {self.id} transmitting CAM at {current_time} seconds.")
            for vehicle in other_vehicles:
                if vehicle.id != self.id and self.is_in_transmission_range(vehicle):
                    success = vehicle.receive_packet(self, simulation)
                    #print(f"Vehicle {vehicle.id} {'successfully received' if success else 'failed to receive'} CAM from Vehicle {self.id}.")
                else:
                    #print(f"Vehicle {vehicle.id} faild received CAM from Vehicle {self.id}.")
                    pass
                self.next_transmission_time = current_time + SUBFRAME_DURATION
            return True 
        return False
    
    def receive_packet(self, sender_vehicle, simulation):
        # 패킷을 수신하는 데 성공했는지 확인
        if self.is_in_transmission_range(sender_vehicle):
            simulation.packet_received()
            return True
        return False
    
    def is_in_transmission_range(self, other_vehicle):
        # 다른 차량이 전송 범위 내에 있는지 확인
        distance = abs(self.position - other_vehicle.position)
        return distance <= TRANSMISSION_RANGE

    # 차량 이동 및 상태 업데이트 관련 메서드들
    def move(self, time_interval):
        new_position = self.position + self.speed * time_interval / 3600
        self.position = new_position 
        #print(self.position)

    def update_status(self, doca_start, doca_end):
        if self.position < doca_start:
            #print("approaching DOCA")
            return "approaching DOCA"
        elif self.position > doca_end:
            #print("exited DOCA")
            return "exited DOCA"
        else:
            #print("in DOCA")
            return "in DOCA"

    # 리소스 관련 메서드들
    def request_resource(self, resource_pool):
        if self.resource_id is None:
            self.resource_id = resource_pool.allocate()
            print(f"Vehicle {self.id} allocated resource: {self.resource_id}")


    def release_resource(self, resource_pool):
        if self.resource_id is not None:
            print(f"Vehicle {self.id} releasing resource: {self.resource_id}")
            resource_pool.release(self.resource_id)
            self.resource_id = None

    def move_and_request_resource(self, time_interval, doca_start, doca_end, resource_pool):
        self.move(time_interval)
        if self.position >= doca_start and self.position <= doca_end and self.resource_id is None:
            self.request_resource(resource_pool)
    
    # DOCA 진입 및 탈출 시 리소스 관리
    def update_and_manage_resource(self, doca_start, doca_end, resource_pool):
        if self.position < doca_start and self.resource_id is None:
            self.request_resource(resource_pool)
        status = self.update_status(doca_start, doca_end)
        if status == "exited DOCA" and self.resource_id is not None:
            self.release_resource(resource_pool)
        return status

    def assign_resource(self, resource):
        self.resource_id = resource

# DOCA 클래스 정의
class DOCA:
    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.vehicles = []

    def add_vehicle(self, vehicle):
        self.vehicles.append(vehicle)

    def update_vehicles(self, time_interval, resource_pool):
        for vehicle in self.vehicles:
            vehicle.move_and_request_resource(time_interval, self.start, self.end, resource_pool)
            vehicle.update_and_manage_resource(self.start, self.end, resource_pool)

# 리소스 풀 클래스 정의
class ResourcePool:
    def __init__(self, num_subchannels, num_subframes):
        self.num_subchannels = num_subchannels
        self.num_subframes = num_subframes
        self.available_resources = set((sc, sf) for sc in range(num_subchannels) for sf in range(num_subframes))
    
    def allocate(self):
        if self.available_resources:
            resource = self.available_resources.pop()
            #print(f"Allocationg resource : {resource}")
            return (resource, SUBFRAME_DURATION)
        return (None, 0)

    def release(self, resource_id):
        self.available_resources.add(resource_id)
        #print(f"Releasing resource : {resource_id}")
    
    def allocate_randomly(self):
        if self.available_resources:
            return random.choice(list(self.available_resources))
        return None

# 중앙 스케줄러 클래스 정의
class CentralScheduler:
    def __init__(self, num_subchannels, num_subframes):
        self.resource_pool = ResourcePool(num_subchannels, num_subframes)
        self.vehicles = []
    
    def register_vehicle(self, vehicle):
        self.vehicles.append(vehicle)
    
    def allocate_resources_randomly(self):
        for vehicle in self.vehicles:
            if not vehicle.resource_id:
                resource = self.resource_pool.allocate_randomly()
                vehicle.assign_resource(resource)

    # 차량 상태 업데이트 (미사용)
    def update_vehicle_status(self, vehicle_id, position, speed):
        pass

    def allocate_resources(self):
        for vehicle in self.vehicles:
            resource = self.resource_pool.allocate()
            vehicle.assign_resource(resource)


# 차량 위치 초기화 함수 정의
def initialize_vehicle_positions(doca_start, num_lanes, num_vehicles_per_lane, speed):
    all_lanes_positions = {}
    for lane in range(1, num_lanes + 1):
        position = doca_start - 600
        positions = []
        for _ in range(num_vehicles_per_lane):
            position += np.random.poisson(speed * 1000 / 3600 * 2.5)
            positions.append(position)
        all_lanes_positions[lane] = positions
    return all_lanes_positions

# 시뮬레이션 클래스 정의
class Simulation:
    def __init__(self, scheduler):
        self.scheduler = scheduler
        self.num_lanes = 4
        self.num_vehicles_per_lane = 20
        self.speed = 140
        self.doca_start, self.doca_end = 500, 1000
        self.simulation_duration = 30000
        self.time_interval = 1
        self.num_subchannels = 1
        self.num_subframes = 10
        self.resource_pool = ResourcePool(self.num_subchannels, self.num_subframes)
        self.current_time = 0
        self.total_packets_transmitted = 0
        self.total_packets_received = 0
        self.doca = DOCA(self.doca_start, self.doca_end)
        vehicle_positions = initialize_vehicle_positions(self.doca_start, self.num_lanes, self.num_vehicles_per_lane, self.speed)

    def run(self):
        for _ in range(self.simulation_duration):
            self.doca.update_vehicles(self.time_interval, self.resource_pool)
            for vehicle in self.doca.vehicles:
                if vehicle.transmit_cam(self.current_time, self.doca.vehicles, self):
                    self.total_packets_transmitted += 1
                    for other_vehicle in self.doca.vehicles:
                        if other_vehicle.id != vehicle.id and other_vehicle.is_in_transmission_range(vehicle):
                            other_vehicle.receive_packet(vehicle, self)
            self.current_time += self.time_interval
            # Ensure continuous movement
            for vehicle in self.doca.vehicles:
                vehicle.move(self.time_interval)
        print(f"total_packets_received : {self.total_packets_received}")
        print(f"total_packets_transmitted : {self.total_packets_transmitted}")
    
    def calculate_prr(self):
        return self.total_packets_received / self.total_packets_transmitted if self.total_packets_transmitted > 0 else 0

# 시뮬레이션 객체 생성 및 실행
scheduler = CentralScheduler(num_subchannels=1, num_subframes=10)
simulation = Simulation(scheduler)
simulation.run()
prr = simulation.calculate_prr()
print(f"Packet Reception Ratio (PRR): {prr}")
