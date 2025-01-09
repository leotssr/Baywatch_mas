import pygame
import random as rd
import numpy as np

class Environment:
    def __init__(self, userInterface, environment_size):
        self.UI = userInterface
        self.size = environment_size
        self.surface = pygame.Surface(self.size)
        self.persons = []
        self.drone_squad = None
        self.rescuer = None
    
    def create(self, nof_people, nof_drones):
        for i in range(nof_people):
            self.add_people()
        
        self.drone_squad = Drone_sqad(self, nof_drones)
            
        self.add_rescuer()
        
        # drone_fov = self.size[0]/nof_drones
        # position_y = 0,75*self.size[1]
        # for i in range(nof_drones):
        #     position_x = (i+0.5)*drone_fov
        #     add_drone(position_x, position_y)
    
    def add_people(self):
        position_x = rd.randint(0, self.size[0]-1)
        position_y = rd.randint(0, self.size[1]//2-1)
        new_person = Person(self, [position_x, position_y])
        self.persons.append(new_person)
    
    def add_rescuer(self):
        position_x = self.size[0]/2
        position_y = 10
        self.rescuer = Rescuer(self, [position_x, position_y])

    def update(self, dt, update_speed):
        self.drone_squad.update(dt, update_speed)
        self.update_person(dt, update_speed)
        self.update_rescuer(dt, update_speed)
    
    def update_rescuer(self, dt, update_speed):
        if self.rescuer.state == "watch":
            if self.rescuer.messages != []:
                self.rescuer.go_to_rescue()

        elif self.rescuer.state == "go_to_rescue":
            direction = find_direction(self.rescuer.followed_drone.position, self.rescuer.position)
            if distance(self.rescuer.followed_drone.position, self.rescuer.position) > 4:
                self.rescuer.position[0] += direction[0]*self.rescuer.speed*dt*update_speed
                self.rescuer.position[1] += direction[1]*self.rescuer.speed*dt*update_speed
            else:
                self.rescuer.position = self.rescuer.followed_drone.position.copy()
                self.rescuer.rescue()
        
        elif self.rescuer.state == "rescue":
            if self.rescuer.person_to_rescue.position[1] > 5*self.size[1]/8:
                delta_position_y = 10*dt*update_speed
                self.rescuer.position[1]-=delta_position_y
                self.rescuer.person_to_rescue.position[1]-=delta_position_y

            else :
                self.rescuer.person_to_rescue.end_rescue()
                self.rescuer.end_rescue()
        
        elif self.rescuer.state == "go_back_watch":
            if self.rescuer.messages != []:
                self.rescuer.go_to_rescue()
            else :
                direction = find_direction(self.rescuer.initial_position, self.rescuer.position)
                if direction[1] < 0:
                    self.rescuer.position[0] += direction[0]*self.rescuer.speed*dt*update_speed
                    self.rescuer.position[1] += direction[1]*self.rescuer.speed*dt*update_speed
                else:
                    self.rescuer.position = self.rescuer.initial_position.copy()
                    self.rescuer.watch()

    def update_person(self, dt, update_speed):
        for person in self.persons:
            if person.state == "on_beach":
                if rd.random()<(2e-3*dt*update_speed):
                    person.go_swimming()

            elif person.state == "going_water":
                if person.position[1] < person.swimming_position[1] : 
                    person.position[1] += 50*dt*person.speed_ratio*update_speed
                else :
                    person.position[1] = person.swimming_position[1]
                    person.swim()

            elif person.state == "in_water":
                new_position_x = person.position[0]+person.swimming_direction*20*dt*person.speed_ratio*update_speed
                if new_position_x >= 0 and new_position_x < self.size[0]:
                    if abs(new_position_x-person.swimming_position[0]) < person.swimming_length:
                        person.position[0] = new_position_x
                    else:
                        person.swimming_direction *= -1
                else:
                    person.swimming_direction *= -1

                if rd.random()<(5e-4*dt*update_speed):
                    person.has_problem()
                else :
                    if rd.random()<(5e-3*dt*update_speed):
                        person.go_back_beach()                

            elif person.state == "going_back_beach":
                direction = find_direction(person.towel_position, person.position)

                if direction[1] < 0:
                    person.position[0] += direction[0]*person.speed_ratio*50*dt*update_speed
                    person.position[1] += direction[1]*person.speed_ratio*50*dt*update_speed
                else:
                    person.position = person.towel_position.copy()
                    person.on_beach()

    def display(self, camera_x):
        bouey_image = pygame.image.load("baywatch_mas/bouey.png").convert_alpha()
        rescuer_image = pygame.image.load("baywatch_mas/secuer.png").convert_alpha()
        beach_image = pygame.image.load("baywatch_mas/beach.png")  

        beach_image = pygame.transform.scale(beach_image, (self.size[0], self.size[1]))
        self.surface.blit(beach_image, (0,0))

        for person in self.persons:
            if person.state == "has_problem":
                pygame.draw.circle(self.surface, "red", person.position, 4)
                font = pygame.font.Font(None, 30)
                text = font.render("!", True, "red")
                self.surface.blit(text, (person.position[0] + 5, person.position[1] - 20))
            elif person.state == "being_rescued":
                bouey_image = pygame.transform.scale(bouey_image, (20, 20))
                self.surface.blit(bouey_image, person.position)

            else:
                pygame.draw.circle(self.surface, "black", person.position, 4)
        
        self.drone_squad.display_squad()

        rescuer_image = pygame.transform.scale(rescuer_image, self.rescuer.size)
        self.surface.blit(rescuer_image, (self.rescuer.position[0]-self.rescuer.size[0]/2, self.rescuer.position[1]-self.rescuer.size[1]/2))
        
        self.UI.screen.blit(self.surface, (-camera_x, 0))

class Person:
    def __init__(self, environment, initial_position):
        self.position = initial_position
        self.towel_position = initial_position.copy()
        self.swimming_position = None
        self.swimming_direction = None
        self.swimming_length = None
        self.environment =  environment
        self.state = "on_beach" # "on_beach", "going_water", "in_water", "has_problem", "going_back_beach"
        self.speed_ratio = rd.choice([0.3, 0.6, 1])

    def go_swimming(self):
        swimming_position_y = rd.randint(3*self.environment.size[1]//4, self.environment.size[1]-2)
        self.swimming_position = [self.towel_position[0], swimming_position_y]
        self.state = "going_water"
    
    def swim(self):
        self.state = "in_water"
        self.swimming_direction = rd.choice([1, -1])
        self.swimming_length = rd.randint(30, 150)

    def go_back_beach(self):
        self.state="going_back_beach"   
    
    def on_beach(self):
        self.state = "on_beach"
    
    def has_problem(self):
        self.state="has_problem"

    def end_rescue(self):
        self.state = "going_back_beach"
    

class Drone:
    def __init__(self, environment, squad, position, direction, watch_bounds):
        self.environment = environment
        self.squad=squad
        self.position=position
        self.direction=direction
        self.size = [35, 30]
        self.watch_bounds = watch_bounds
        self.fov_width = environment.size[1]/8
        self.state = "patrol" 
        self.person_to_rescue = None
        self.bouey_diameter = 20
        self.speed = 50
    
    def patrol(self):
        for person in self.environment.persons:
            if self.person_on_view(person) and person.state == "has_problem" and not person in self.squad.rescued_people.keys():
                self.state = "go_to_rescue"
                self.squad.reconfigure()
                self.person_to_rescue = person
                self.squad.rescued_people[person]=self
                self.call_rescuer()

    def person_on_view(self, person):
        if abs(person.position[0] - self.position[0]) < self.fov_width:
            if abs(person.position[1] - self.position[1]) < self.fov_width:
                return True
    
    def rescue(self):
        self.state = "rescue"
        self.person_to_rescue.state = "being_rescued"

    def end_rescue(self):
        self.state = "go_back_patrol"
        del self.squad.rescued_people[self.person_to_rescue]
        self.person_to_rescue = None
    
    def call_rescuer(self):
        self.environment.rescuer.messages.append(self)
    
    def back_patrol(self):
        self.state = "patrol" 
        self.squad.reconfigure()      

    def update(self, dt, update_speed):
        if self.state == "patrol":
            new_position_x = self.position[0]+self.direction*self.speed*dt*update_speed
            if new_position_x >= self.size[0]/2+self.watch_bounds[0] and new_position_x < self.watch_bounds[1]-self.size[0]/2:
                self.position[0] = new_position_x
            else :
                self.direction *= -1

            self.patrol()
        
        if self.state == "go_to_rescue":
            direction = find_direction(self.person_to_rescue.position, self.position)
            if distance(self.person_to_rescue.position, self.position) > self.bouey_diameter:
                self.position[0] += direction[0]*self.speed*dt*update_speed
                self.position[1] += direction[1]*self.speed*dt*update_speed
            else:
                self.rescue()
            
        if self.state == "go_back_patrol":
            target_position = [self.position[0], 7*self.environment.size[1]/8]
            direction = find_direction(target_position, self.position)
            if distance(target_position, self.position) > 5:
                self.position[1] += direction[1]*self.speed*dt*update_speed
            else :
                self.position[1] = 7*self.environment.size[1]/8
                self.back_patrol() 


class Rescuer():
    def __init__(self, environment, initial_position):
        self.environment = environment
        self.initial_position = initial_position
        self.position = initial_position.copy()
        self.size = (20, 20)
        self.state = "watch"
        self.messages = []
        self.person_to_rescue = None
        self.followed_drone = None
        self.speed = 50

    def go_to_rescue(self):
        self.followed_drone = self.messages.pop(0)
        self.state = "go_to_rescue"
    
    def rescue(self):
        self.state="rescue"
        self.person_to_rescue = self.followed_drone.person_to_rescue
        self.followed_drone.end_rescue()
        self.followed_drone=None
    
    def end_rescue(self):
        self.state = "go_back_watch"
        self.person_to_rescue = None
    
    def watch(self):
        self.state = "watch"

class Drone_sqad():
    def __init__(self, environment, nof_drones):
        self.environment = environment
        self.drones = []
        self.create(nof_drones)
        self.state  = "patrol"
        self.image = pygame.image.load("baywatch_mas/drone.png").convert_alpha()
        self.rescued_people = {}


    def create(self, nof_drones):
        position_y = 7*self.environment.size[1]/8
        sector_size = self.environment.size[0]/nof_drones
        for i in range(nof_drones):
            position_x = (i+0.5)*sector_size
            watch_bounds = [i*sector_size, (i+1)*sector_size]
            self.add_drone([position_x, position_y], watch_bounds)

    def add_drone(self, position, watch_bounds):
        direction = 1
        new_drone = Drone(self.environment, self, position, direction, watch_bounds)
        self.drones.append(new_drone)
    
    def display_squad(self):
        for drone in self.drones :
            rectangle_surface = pygame.Surface((2*drone.fov_width, 2*drone.fov_width), pygame.SRCALPHA)  
            rectangle_surface.fill((*(50, 50, 50), 30))  
            self.environment.surface.blit(rectangle_surface, (drone.position[0] - drone.fov_width, drone.position[1] - drone.fov_width)) 
            drone_image = pygame.transform.scale(self.image, drone.size)
            self.environment.surface.blit(drone_image, (drone.position[0]-drone.size[0]/2, drone.position[1]-drone.size[1]/2))

            if drone.state == "patrol":
                watch_limit_0 = pygame.Rect(drone.watch_bounds[0]-2, 7*self.environment.size[1]/8 +10, 4, 20) 
                watch_limit_1 = pygame.Rect(drone.watch_bounds[1]-2, 7*self.environment.size[1]/8 +10, 4, 20) 
                pygame.draw.rect(self.environment.surface, "black", watch_limit_0) 
                pygame.draw.rect(self.environment.surface, "black", watch_limit_1)  

    def reconfigure(self):
        self.state="reconfigure"
        nof_active_drones = 0
        for drone in self.drones:
            if drone.state == "patrol":
                nof_active_drones += 1

        sector_size = self.environment.size[0]/nof_active_drones                

        i = 0
        for drone in self.drones:
            if drone.state == "patrol":
                drone.watch_bounds = [i*sector_size, (i+1)*sector_size]
                i+=1

    def update(self, dt, update_speed):
        if self.state == "reconfigure":
            nof_drone_ok = 0
            nof_active_drones = 0
            for drone in self.drones:
                if drone.state=="patrol":
                    nof_active_drones += 1
                    if drone.position[0]< drone.watch_bounds[0]+drone.size[0]: 
                        drone.direction =1
                        drone.position[0] += drone.direction*drone.speed*dt*update_speed
                    elif drone.position[0]>drone.watch_bounds[1]-drone.size[0]:
                        drone.direction =-1
                        drone.position[0] += drone.direction*drone.speed*dt*update_speed
                    else:
                        nof_drone_ok += 1
                        drone.update(dt, update_speed)
            else:
                drone.update(dt, update_speed)

            if nof_drone_ok == nof_active_drones:
                self.state = "patrol"   

        else :
            for i, drone in enumerate(self.drones):
                drone.update(dt, update_speed)


def find_direction(objectif_position, actual_position):
    direction_x = objectif_position[0]-actual_position[0]
    direction_y = objectif_position[1]-actual_position[1]
    norm_direction = np.sqrt(direction_x**2+direction_y**2)
    direction_x /= norm_direction
    direction_y /= norm_direction
    return [direction_x, direction_y]


def distance(positionA, positionB):
    distance_x = positionA[0]-positionB[0]
    distance_y = positionA[1]-positionB[1]
    return np.sqrt(distance_x**2+distance_y**2)

    