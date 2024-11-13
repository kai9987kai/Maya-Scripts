# Import necessary modules
import maya.cmds as cmds
import maya.utils
import random
import math
import sys
import re

# Enable the Evaluation Manager in Parallel mode
cmds.evaluationManager(mode='parallel')

# Enable Cached Playback
cmds.optionVar(iv=('cachedPlaybackEnable', 1))

# Constants
GRID_SIZE = 60
CELL_SIZE = 1  # Adjust as needed
MAX_ENERGY = 100
POPULATION_SIZE = 10
RESOURCE_TYPES = ['food', 'water']
THREAT_TYPES = ['predator', 'hazard']
ACTIONS = ['up', 'down', 'left', 'right']

# Lists to keep track of objects
agents = []
resources = []
threats = []
cells = []

# Initialize the environment
def create_environment():
    # Create a grid of cells
    for x in range(GRID_SIZE):
        for z in range(GRID_SIZE):
            cell = cmds.polyPlane(w=CELL_SIZE, h=CELL_SIZE, sx=1, sy=1, name=f'cell_{x}_{z}')[0]
            cmds.move(x * CELL_SIZE, 0, z * CELL_SIZE, cell)
            cmds.setAttr(f'{cell}.receiveShadows', 0)
            cmds.setAttr(f'{cell}.castsShadows', 0)
            cells.append(cell)
    # Create initial resources and threats
    create_resources(int(GRID_SIZE * GRID_SIZE * 0.05))
    create_threats(int(GRID_SIZE * GRID_SIZE * 0.03))

def create_resources(count):
    for _ in range(count):
        type = random.choice(RESOURCE_TYPES)
        x = random.randint(0, GRID_SIZE - 1)
        z = random.randint(0, GRID_SIZE - 1)
        if not is_occupied(x, z):
            resource = create_resource(type, x, z)
            resources.append(resource)

def create_resource(type, x, z):
    if type == 'food':
        res = cmds.polySphere(r=0.3, name=f'food_{x}_{z}')[0]
        cmds.setAttr(f'{res}.translateY', 0.3)
        cmds.setAttr(f'{res}.overrideEnabled', 1)
        cmds.setAttr(f'{res}.overrideColor', 14)  # Green
    elif type == 'water':
        res = cmds.polyCylinder(r=0.3, h=0.2, name=f'water_{x}_{z}')[0]
        cmds.setAttr(f'{res}.translateY', 0.1)
        cmds.setAttr(f'{res}.overrideEnabled', 1)
        cmds.setAttr(f'{res}.overrideColor', 6)  # Blue
    # Set X and Z positions directly
    cmds.setAttr(f'{res}.translateX', x * CELL_SIZE)
    cmds.setAttr(f'{res}.translateZ', z * CELL_SIZE)
    return {'object': res, 'type': type, 'position': (x, z)}

def create_threats(count):
    for _ in range(count):
        type = random.choice(THREAT_TYPES)
        x = random.randint(0, GRID_SIZE - 1)
        z = random.randint(0, GRID_SIZE - 1)
        if not is_occupied(x, z):
            threat = create_threat(type, x, z)
            threats.append(threat)

def create_threat(type, x, z):
    if type == 'predator':
        th = cmds.polyCone(r=0.3, h=0.6, name=f'predator_{x}_{z}')[0]
        cmds.setAttr(f'{th}.translateY', 0.3)
        cmds.setAttr(f'{th}.overrideEnabled', 1)
        cmds.setAttr(f'{th}.overrideColor', 13)  # Red
    elif type == 'hazard':
        th = cmds.polyCylinder(r=0.3, h=0.6, name=f'hazard_{x}_{z}')[0]
        cmds.setAttr(f'{th}.translateY', 0.3)
        cmds.setAttr(f'{th}.overrideEnabled', 1)
        cmds.setAttr(f'{th}.overrideColor', 17)  # Orange
    # Set X and Z positions directly
    cmds.setAttr(f'{th}.translateX', x * CELL_SIZE)
    cmds.setAttr(f'{th}.translateZ', z * CELL_SIZE)
    return {'object': th, 'type': type, 'position': (x, z)}

def is_occupied(x, z):
    # Check if a resource or threat is already at this position
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
        self.alive = True
        self.q_table = {}
        self.epsilon = 0.2  # Exploration rate
        self.alpha = 0.1    # Learning rate
        self.gamma = 0.9    # Discount factor
        self.communication_range = 5
        self.agents = agents_list  # Reference to other agents
        # Create visual representation in Maya
        self.maya_obj = cmds.polyCube(w=0.5, h=0.5, d=0.5, name=f'agent_{id}')[0]
        cmds.setAttr(f'{self.maya_obj}.translateY', 0.25)
        cmds.setAttr(f'{self.maya_obj}.overrideEnabled', 1)
        cmds.setAttr(f'{self.maya_obj}.overrideColor', 30)  # Purple
        # Set initial position
        cmds.setAttr(f'{self.maya_obj}.translateX', self.position[0] * CELL_SIZE)
        cmds.setAttr(f'{self.maya_obj}.translateZ', self.position[1] * CELL_SIZE)
        # Physics attributes
        self.enable_physics()

    def enable_physics(self):
        # Enable Bullet physics simulation for the agent
        if not cmds.pluginInfo('bullet', query=True, loaded=True):
            cmds.loadPlugin('bullet')
        # Create a rigid body using Bullet
        cmds.select(self.maya_obj)
        cmds.bulletRigidBody(shapeType='box', mass=1.0)
        print(f"Enabled Bullet physics for {self.maya_obj}.")

    def get_state(self):
        return f"{self.position[0]},{self.position[1]}"

    def move(self):
        if not self.alive:
            return

        current_state = self.get_state()
        action = self.choose_action(current_state)
        dx, dz = self.get_action_delta(action)

        self.update_position(dx, dz)
        reward = self.interact_with_environment()
        self.energy -= 1  # Decrease energy on each move

        new_state = self.get_state()
        self.learn(current_state, action, reward, new_state)

        if self.energy >= MAX_ENERGY * 0.9:
            self.reproduce()

        if self.energy <= 0:
            self.alive = False
            cmds.delete(self.maya_obj)

    def get_action_delta(self, action):
        return {
            'up': (0, -1),
            'down': (0, 1),
            'left': (-1, 0),
            'right': (1, 0)
        }.get(action, (0, 0))

    def update_position(self, dx, dz):
        new_x = min(max(self.position[0] + dx, 0), GRID_SIZE - 1)
        new_z = min(max(self.position[1] + dz, 0), GRID_SIZE - 1)
        self.position = [new_x, new_z]
        # Set the X and Z translation attributes directly
        cmds.setAttr(f'{self.maya_obj}.translateX', new_x * CELL_SIZE)
        cmds.setAttr(f'{self.maya_obj}.translateZ', new_z * CELL_SIZE)

    def interact_with_environment(self):
        x, z = self.position
        reward = -0.1  # Small movement penalty

        # Check for resources
        for res in resources:
            if res['position'] == (x, z):
                self.energy = min(self.energy + 20, MAX_ENERGY)
                reward = 10
                cmds.delete(res['object'])
                resources.remove(res)
                break  # Only one resource per cell

        # Check for threats
        for th in threats:
            if th['position'] == (x, z):
                self.energy -= 30
                reward = -20
                # Optionally remove threat
                cmds.delete(th['object'])
                threats.remove(th)
                break

        # Communicate with nearby agents
        self.communicate()

        return reward

    def communicate(self):
        for agent in self.agents:
            if agent.id != self.id and agent.alive:
                distance = math.hypot(self.position[0] - agent.position[0], self.position[1] - agent.position[1])
                if distance <= self.communication_range:
                    self.merge_q_tables(agent)

    def merge_q_tables(self, other_agent):
        for state, actions in other_agent.q_table.items():
            if state not in self.q_table:
                self.q_table[state] = actions.copy()
            else:
                for action, value in actions.items():
                    if action not in self.q_table[state]:
                        self.q_table[state][action] = value
                    else:
                        self.q_table[state][action] = (self.q_table[state][action] + value) / 2

    def choose_action(self, state):
        if random.random() < self.epsilon or state not in self.q_table:
            return random.choice(ACTIONS)
        else:
            return self.get_best_action(state)

    def get_best_action(self, state):
        q_values = self.q_table.get(state, {})
        max_value = max(q_values.values(), default=0)
        best_actions = [action for action, value in q_values.items() if value == max_value]
        if best_actions:
            return random.choice(best_actions)
        else:
            return random.choice(ACTIONS)

    def learn(self, state, action, reward, next_state):
        if state not in self.q_table:
            self.q_table[state] = {}
        if next_state not in self.q_table:
            self.q_table[next_state] = {}
        q_predict = self.q_table[state].get(action, 0)
        q_next_max = max(self.q_table[next_state].values(), default=0)
        q_target = reward + self.gamma * q_next_max
        self.q_table[state][action] = q_predict + self.alpha * (q_target - q_predict)

    def reproduce(self):
        new_agent = Agent(self.env, len(self.agents) + 1, self.agents)
        new_agent.position = self.position.copy()
        new_agent.energy = MAX_ENERGY / 2
        self.energy = MAX_ENERGY / 2
        # Slight mutation
        new_agent.epsilon = min(max(self.epsilon + (random.random() - 0.5) * 0.02, 0), 1)
        new_agent.alpha = min(max(self.alpha + (random.random() - 0.5) * 0.02, 0), 1)
        new_agent.gamma = min(max(self.gamma + (random.random() - 0.5) * 0.02, 0), 1)
        self.agents.append(new_agent)

# VFX Modules for advanced effects
def add_fire(obj_name):
    if not cmds.objExists(obj_name):
        print(f"Object {obj_name} does not exist.")
        return
    # Add fire effect to an object (Placeholder implementation)
    # Create a fire effect using Maya's fluid effects
    cmds.select(obj_name)
    cmds.loadPlugin('Mayatomr', quiet=True)
    fire_effect = cmds.effects(fire=True)
    print(f"Added fire effect to {obj_name}.")

def fracture_object(obj_name):
    if not cmds.objExists(obj_name):
        print(f"Object {obj_name} does not exist.")
        return
    # Apply a fracture effect to an object (Placeholder implementation)
    print(f"Applied fracture effect to {obj_name}.")

def make_object_mirror(obj_name):
    if not cmds.objExists(obj_name):
        print(f"Object {obj_name} does not exist.")
        return
    # Change the object's material to a mirror-like material
    shader = cmds.shadingNode('blinn', asShader=True, name=f'{obj_name}_mirrorShader')
    cmds.setAttr(shader + '.color', 1, 1, 1, type='double3')
    cmds.setAttr(shader + '.eccentricity', 0)
    cmds.setAttr(shader + '.specularRollOff', 1)
    cmds.setAttr(shader + '.reflectivity', 1)
    shading_group = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=f'{obj_name}_mirrorSG')
    cmds.connectAttr(shader + '.outColor', shading_group + '.surfaceShader', force=True)
    cmds.sets(obj_name, e=True, forceElement=shading_group)
    print(f"Changed {obj_name} to a mirror-like material.")

def make_object_bigger(obj_name, scale_factor):
    if not cmds.objExists(obj_name):
        print(f"Object {obj_name} does not exist.")
        return
    # Scale the object by the given factor
    cmds.scale(scale_factor, scale_factor, scale_factor, obj_name, relative=True)
    print(f"Scaled {obj_name} by a factor of {scale_factor}.")

# Function to process natural language instructions
def process_instruction(instruction):
    # Remove articles for accurate object names
    instruction = re.sub(r'\b(the|a|an)\b', '', instruction)
    if 'make' in instruction and 'mirror' in instruction:
        # Find object to apply mirror effect
        obj_name_match = re.search(r'make\s+(\w+)\s+look\s+like\s+mirror', instruction)
        if obj_name_match:
            obj_name = obj_name_match.group(1).strip()
            make_object_mirror(obj_name)
    elif 'make' in instruction and 'bigger' in instruction:
        obj_name_match = re.search(r'make\s+(\w+)\s+bigger', instruction)
        if obj_name_match:
            obj_name = obj_name_match.group(1).strip()
            make_object_bigger(obj_name, 1.5)
    elif 'insert' in instruction:
        obj_name_match = re.search(r'insert\s+(\w+)', instruction)
        if obj_name_match:
            obj_type = obj_name_match.group(1).strip()
            insert_object(obj_type)
    elif 'drop' in instruction:
        obj_name_match = re.search(r'drop\s+(\w+)', instruction)
        if obj_name_match:
            obj_name = obj_name_match.group(1).strip()
            drop_object(obj_name)
    elif 'add fire' in instruction:
        obj_name_match = re.search(r'add fire to\s+(\w+)', instruction)
        if obj_name_match:
            obj_name = obj_name_match.group(1).strip()
            add_fire(obj_name)
    else:
        print(f"No valid instruction found in: '{instruction}'")
    # Add more parsing rules as needed

def insert_object(obj_type):
    # Insert a new object into the scene
    if obj_type == 'basketball':
        obj = cmds.polySphere(r=0.5, name='basketball')[0]
        cmds.setAttr(f'{obj}.translateY', 10)
        # Enable Bullet physics
        if not cmds.pluginInfo('bullet', query=True, loaded=True):
            cmds.loadPlugin('bullet')
        cmds.select(obj)
        cmds.bulletRigidBody()
        print(f"Inserted a {obj_type} into the scene.")
    elif obj_type == 'pikachu':
        # Assuming a Pikachu model is available
        # For demonstration, we'll create a placeholder
        obj = cmds.polySphere(r=0.5, name='pikachu')[0]
        cmds.setAttr(f'{obj}.translateY', 1)
        print(f"Inserted a {obj_type} into the scene.")
    else:
        print(f"Unknown object type: {obj_type}")

def drop_object(obj_name):
    if not cmds.objExists(obj_name):
        print(f"Object {obj_name} does not exist.")
        return
    # Drop an object from a height
    cmds.setAttr(f'{obj_name}.translateY', 10)
    # Enable Bullet physics
    if not cmds.pluginInfo('bullet', query=True, loaded=True):
        cmds.loadPlugin('bullet')
    cmds.select(obj_name)
    cmds.bulletRigidBody()
    print(f"Dropped {obj_name} from height.")

# Simulation class
class Simulation:
    def __init__(self):
        self.env = None  # Placeholder, not used in this context
        self.agents = []
        self.total_steps = 0
        self.max_steps = 1000  # Set a maximum number of steps
        self.create_simulation()

    def create_simulation(self):
        # Initialize environment
        create_environment()
        # Initialize agents
        for i in range(POPULATION_SIZE):
            agent = Agent(self.env, i + 1, self.agents)
            self.agents.append(agent)
        # Start simulation
        self.run_simulation()

    def run_simulation(self):
        if self.total_steps >= self.max_steps:
            print("Simulation finished.")
            return
        self.total_steps += 1
        print(f"Step: {self.total_steps}, Agents alive: {len([a for a in self.agents if a.alive])}")
        self.update()
        # Schedule next step using executeDeferred
        maya.utils.executeDeferred(self.run_simulation)

    def update(self):
        # Update agents
        for agent in self.agents:
            agent.move()
        # Remove dead agents
        self.agents = [agent for agent in self.agents if agent.alive]
        # Regenerate resources and threats
        self.regenerate_environment()
        # Process any pending instructions
        if self.total_steps % 50 == 0:
            instruction = get_user_instruction()
            print(f"Processing instruction: '{instruction}'")
            process_instruction(instruction)

    def regenerate_environment(self):
        # Regenerate resources
        if random.random() < 0.1:
            create_resources(1)
        # Regenerate threats
        if random.random() < 0.05:
            create_threats(1)

def get_user_instruction():
    # Placeholder for getting user instruction
    # For demonstration, we use a preset instruction
    instructions = [
        "Make agent_1 look like mirror",
        "Insert basketball",
        "Drop basketball",
        "Make agent_2 bigger",
        "Add fire to agent_3"
    ]
    return random.choice(instructions)

# Start the simulation
simulation = Simulation()
