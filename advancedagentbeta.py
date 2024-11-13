# Import necessary modules
import maya.cmds as cmds
import maya.utils
import random
import math
import re
try:
    import tensorflow as tf
except ImportError:
    tf = None  # TensorFlow is optional, if available

# Constants and Parameters
GRID_SIZE = 60
CELL_SIZE = 1
MAX_ENERGY = 100
POPULATION_SIZE = 10
RESOURCE_TYPES = ['food', 'water']
THREAT_TYPES = [{'type': 'predator', 'level': 1}, {'type': 'hazard', 'level': 2}]
ACTIONS = ['up', 'down', 'left', 'right']

# Lists to keep track of objects
agents = []
resources = []
threats = []
cells = []

# Initialize environment
def create_environment():
    for x in range(GRID_SIZE):
        for z in range(GRID_SIZE):
            cell = cmds.polyPlane(w=CELL_SIZE, h=CELL_SIZE, sx=1, sy=1, name=f'cell_{x}_{z}')[0]
            cmds.move(x * CELL_SIZE, 0, z * CELL_SIZE, cell)
            cmds.setAttr(f'{cell}.receiveShadows', 0)
            cmds.setAttr(f'{cell}.castsShadows', 0)
            cells.append(cell)
    create_resources(int(GRID_SIZE * GRID_SIZE * 0.05))
    create_threats(int(GRID_SIZE * GRID_SIZE * 0.03))

def create_resources(count):
    for _ in range(count):
        type = random.choice(RESOURCE_TYPES)
        x, z = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
        if not is_occupied(x, z):
            resource = create_resource(type, x, z)
            resources.append(resource)

def create_resource(type, x, z):
    color_map = {'food': 14, 'water': 6}
    res = cmds.polySphere(r=0.3, name=f'{type}_{x}_{z}')[0]
    cmds.setAttr(f'{res}.translateY', 0.3)
    cmds.setAttr(f'{res}.overrideEnabled', 1)
    cmds.setAttr(f'{res}.overrideColor', color_map[type])
    cmds.setAttr(f'{res}.translateX', x * CELL_SIZE)
    cmds.setAttr(f'{res}.translateZ', z * CELL_SIZE)
    return {'object': res, 'type': type, 'position': (x, z)}

def create_threats(count):
    for _ in range(count):
        threat_type = random.choice(THREAT_TYPES)
        x, z = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
        if not is_occupied(x, z):
            threat = create_threat(threat_type['type'], threat_type['level'], x, z)
            threats.append(threat)

def create_threat(type, level, x, z):
    color_map = {1: 13, 2: 17}
    th = cmds.polyCone(r=0.3, h=0.6, name=f'{type}_{x}_{z}')[0]
    cmds.setAttr(f'{th}.translateY', 0.3)
    cmds.setAttr(f'{th}.overrideEnabled', 1)
    cmds.setAttr(f'{th}.overrideColor', color_map[level])
    cmds.setAttr(f'{th}.translateX', x * CELL_SIZE)
    cmds.setAttr(f'{th}.translateZ', z * CELL_SIZE)
    return {'object': th, 'type': type, 'position': (x, z), 'level': level}

def is_occupied(x, z):
    for res in resources:
        if res['position'] == (x, z):
            return True
    for th in threats:
        if th['position'] == (x, z):
            return True
    return False

# Agent class
class Agent:
    def __init__(self, env, id, agents_list):
        self.env = env
        self.id = id
        self.position = [random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)]
        self.energy = MAX_ENERGY
        self.health = 100
        self.alive = True
        self.q_table = {}
        self.epsilon = 0.2
        self.alpha = 0.1
        self.gamma = 0.9
        self.communication_range = 5
        self.agents = agents_list
        self.maya_obj = cmds.polyCube(w=0.5, h=0.5, d=0.5, name=f'agent_{id}')[0]
        cmds.setAttr(f'{self.maya_obj}.translateY', 0.25)
        cmds.setAttr(f'{self.maya_obj}.overrideEnabled', 1)
        cmds.setAttr(f'{self.maya_obj}.overrideColor', 30)  # Purple
        cmds.setAttr(f'{self.maya_obj}.translateX', self.position[0] * CELL_SIZE)
        cmds.setAttr(f'{self.maya_obj}.translateZ', self.position[1] * CELL_SIZE)
        self.enable_physics()
        
        # TensorFlow model setup if available
        if tf:
            self.model = self.create_model()

    def enable_physics(self):
        if not cmds.pluginInfo('bullet', query=True, loaded=True):
            cmds.loadPlugin('bullet')
        cmds.select(self.maya_obj)
        cmds.bulletRigidBody(shapeType='box', mass=1.0)

    def create_model(self):
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(32, input_shape=(2,), activation='relu'),
            tf.keras.layers.Dense(4, activation='linear')
        ])
        model.compile(optimizer='adam', loss='mse')
        return model

    def choose_action(self, state):
        if random.random() < self.epsilon:
            return random.choice(ACTIONS)
        if state in self.q_table:
            return max(self.q_table[state], key=self.q_table[state].get)
        return random.choice(ACTIONS)

    def move(self):
        if not self.alive:
            return
        state = f"{self.position[0]},{self.position[1]}"
        action = self.choose_action(state)
        dx, dz = self.get_action_delta(action)
        self.update_position(dx, dz)
        reward = self.interact_with_environment()
        self.energy -= 1
        new_state = f"{self.position[0]},{self.position[1]}"
        self.learn(state, action, reward, new_state)
        if self.energy >= MAX_ENERGY * 0.9:
            self.reproduce()
        if self.energy <= 0 or self.health <= 0:
            self.die()

    def interact_with_environment(self):
        x, z = self.position
        reward = -0.1
        for res in resources:
            if res['position'] == (x, z):
                self.energy = min(self.energy + 20, MAX_ENERGY)
                reward = 10
                cmds.delete(res['object'])
                resources.remove(res)
                break
        for th in threats:
            if th['position'] == (x, z):
                self.health -= th['level'] * 20
                reward = -th['level'] * 10
                cmds.delete(th['object'])
                threats.remove(th)
                break
        return reward

    def update_position(self, dx, dz):
        new_x = min(max(self.position[0] + dx, 0), GRID_SIZE - 1)
        new_z = min(max(self.position[1] + dz, 0), GRID_SIZE - 1)
        self.position = [new_x, new_z]
        cmds.setAttr(f'{self.maya_obj}.translateX', new_x * CELL_SIZE)
        cmds.setAttr(f'{self.maya_obj}.translateZ', new_z * CELL_SIZE)
        self.display_status()

    def display_status(self):
        status_text = f"Energy: {self.energy}, Health: {self.health}"
        cmds.textCurves(text=status_text, name=f'status_{self.id}')

    def die(self):
        self.alive = False
        cmds.delete(self.maya_obj)

    def reproduce(self):
        new_agent = Agent(self.env, len(self.agents) + 1, self.agents)
        new_agent.position = self.position.copy()
        new_agent.energy = MAX_ENERGY / 2
        self.energy = MAX_ENERGY / 2
        self.agents.append(new_agent)

# Simulation class
class Simulation:
    def __init__(self):
        self.env = None
        self.agents = []
        self.total_steps = 0
        self.max_steps = 1000
        create_environment()
        self.initialize_agents()
        self.run_simulation()

    def initialize_agents(self):
        for i in range(POPULATION_SIZE):
            agent = Agent(self.env, i + 1, self.agents)
            self.agents.append(agent)

    def run_simulation(self):
        if self.total_steps >= self.max_steps:
            print("Simulation finished.")
            return
        self.total_steps += 1
        print(f"Step: {self.total_steps}, Agents alive: {len([a for a in self.agents if a.alive])}")
        self.update()
        maya.utils.executeDeferred(self.run_simulation)

    def update(self):
        for agent in self.agents:
            agent.move()
        self.agents = [agent for agent in self.agents if agent.alive]
        if random.random() < 0.1:
            create_resources(1)
        if random.random() < 0.05:
            create_threats(1)

# Start the simulation
simulation = Simulation()
