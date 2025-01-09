# Example file showing a circle moving on screen
import pygame
import user_interface

UI = user_interface.UserInterface()
UI.environment.create(60, 4) #create an environment with 30 people and 4 drones, 1 rescuer
UI.run()