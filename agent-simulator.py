import maya.cmds as cmds
import random
import numpy as np
import json

# Simulation constants
GRID_SIZE = 10
CELL_SIZE = 2
POPULATION_SIZE = 5
MAX_ENERGY = 100
MUTATION_RATE = 0.05
EPSILON_DECAY = 0.995
MIN_EPSILON = 0.01
ALPHA_DECAY = 0.99
MIN_ALPHA = 0.01

# Initialize the environment with obstacles and rewards
class Environment3D:
    def __init__(self):
        self.grid_size = GRID_SIZE
        self.state = self.create_state()
        self.obstacles = self.create_obstacles()

    def create_state(self):
        """Generate a grid with random rewards and penalties."""
        return [[random.choice([-1, 10]) for _ in range(self.grid_size)] for _ in range(self.grid_size)]

    def create_obstacles(self):
        """Place obstacles as 3D cubes."""
        obstacles = []
        for _ in range(int(self.grid_size ** 2 * 0.1)):
            x, z = random.randint(0, self.grid_size - 1), random.randint(0, self.grid_size - 1)
            obstacle_name = f"obstacle_{x}_{z}"
            if not cmds.objExists(obstacle_name):
                cmds.polyCube(name=obstacle_name, width=CELL_SIZE, depth=CELL_SIZE, height=1)
                cmds.setAttr(f"{obstacle_name}.translateX", x * CELL_SIZE)
                cmds.setAttr(f"{obstacle_name}.translateZ", z * CELL_SIZE)
            obstacles.append((x, z))
        return obstacles

# Agent class with basic Q-learning and neural network components
class Agent3D:
    def __init__(self, env, agent_id):
        self.env = env
        self.agent_id = agent_id
        self.position = [GRID_SIZE // 2, 0, GRID_SIZE // 2]
        self.q_table = self.init_q_table()
        self.model = self.init_neural_network()
        self.energy = MAX_ENERGY
        self.epsilon = 0.1
        self.alpha = 0.1
        self.gamma = 0.9
        self.total_reward = 0
        self.agent_name = f"agent_{agent_id}"
        self.create_agent()

    def init_q_table(self):
        """Initialize Q-Table."""
        return {(x, z): {'up': 0, 'down': 0, 'left': 0, 'right': 0} for x in range(GRID_SIZE) for z in range(GRID_SIZE)}

    def init_neural_network(self):
        """Initialize a simple neural network."""
        return np.random.rand(2, 4)

    def create_agent(self):
        """Create agent's 3D representation."""
        if not cmds.objExists(self.agent_name):
            cmds.polySphere(name=self.agent_name, radius=0.5)
        cmds.setAttr(f"{self.agent_name}.translateX", self.position[0] * CELL_SIZE)
        cmds.setAttr(f"{self.agent_name}.translateZ", self.position[2] * CELL_SIZE)

    def choose_action(self):
        """Choose an action with Q-learning or neural network."""
        x, z = self.position[0] // CELL_SIZE, self.position[2] // CELL_SIZE
        state = (x, z)
        if random.random() < self.epsilon:
            return random.choice(['up', 'down', 'left', 'right'])
        if self.energy > MAX_ENERGY * 0.5:
            predictions = np.dot(np.array([x / GRID_SIZE, z / GRID_SIZE]), self.model)
            actions = ['up', 'down', 'left', 'right']
            return actions[np.argmax(predictions)]
        else:
            return max(self.q_table[state], key=self.q_table[state].get)

    def update_q_table(self, action, reward, new_state):
        """Update Q-Table using Q-learning."""
        current_pos = (self.position[0] // CELL_SIZE, self.position[2] // CELL_SIZE)
        best_future_q = max(self.q_table[new_state].values())
        self.q_table[current_pos][action] += self.alpha * (reward + self.gamma * best_future_q - self.q_table[current_pos][action])

    def move(self, action):
        """Move agent based on chosen action."""
        dx, dz = 0, 0
        if action == 'up': dz = CELL_SIZE
        elif action == 'down': dz = -CELL_SIZE
        elif action == 'left': dx = -CELL_SIZE
        elif action == 'right': dx = CELL_SIZE
        new_x = max(0, min(self.env.grid_size - 1, self.position[0] + dx))
        new_z = max(0, min(self.env.grid_size - 1, self.position[2] + dz))
        self.position = [new_x, 0, new_z]
        cmds.setAttr(f"{self.agent_name}.translateX", self.position[0])
        cmds.setAttr(f"{self.agent_name}.translateZ", self.position[2])

# Simulation manager for UI and control
class Simulation3D:
    def __init__(self):
        self.env = Environment3D()
        self.agents = [Agent3D(self.env, i + 1) for i in range(POPULATION_SIZE)]
        self.running = False
        self.init_ui()

    def init_ui(self):
        """Create UI window for simulation control."""
        if cmds.window("SimulationWindow", exists=True):
            cmds.deleteUI("SimulationWindow", window=True)
        
        self.window = cmds.window("SimulationWindow", title="3D Simulation Controls", widthHeight=(300, 150))
        cmds.columnLayout(adjustableColumn=True)
        cmds.button(label="Run Simulation", command=lambda x: self.run())
        cmds.button(label="Reset Simulation", command=lambda x: self.reset())
        cmds.button(label="Save State", command=lambda x: self.save_state())
        cmds.button(label="Load State", command=lambda x: self.load_state())
        cmds.showWindow(self.window)
        print("UI initialized.")

    def run(self):
        """Run the simulation loop."""
        print("Starting simulation...")
        self.running = True
        while self.running:
            self.step()
            cmds.refresh()
            if all(agent.energy <= 0 for agent in self.agents):
                print("All agents out of energy. Stopping simulation.")
                self.stop()

    def stop(self):
        """Stop the simulation."""
        print("Stopping simulation...")
        self.running = False

    def step(self):
        """Perform a single simulation step."""
        for agent in self.agents:
            x, z = int(agent.position[0] // CELL_SIZE), int(agent.position[2] // CELL_SIZE)
            action = agent.choose_action()
            reward = self.env.state[z][x]
            agent.update_q_table(action, reward, (x, z))
            agent.move(action)
            agent.total_reward += reward
            agent.energy -= 1
            print(f"Agent {agent.agent_id} - Reward: {agent.total_reward}, Energy: {agent.energy}")

    def reset(self):
        """Reset environment and agents to initial state."""
        print("Resetting simulation...")
        self.env = Environment3D()
        for agent in self.agents:
            cmds.delete(agent.agent_name)
            agent.position = [GRID_SIZE // 2, 0, GRID_SIZE // 2]
            agent.create_agent()
            agent.q_table = agent.init_q_table()
            agent.energy = MAX_ENERGY
            agent.total_reward = 0

    def save_state(self):
        """Save the simulation state."""
        print("Saving simulation state...")
        state = {
            'environment': self.env.state,
            'agents': [{
                'position': agent.position,
                'q_table': agent.q_table,
                'total_reward': agent.total_reward,
                'energy': agent.energy,
            } for agent in self.agents]
        }
        with open('simulation_state.json', 'w') as f:
            json.dump(state, f)
        print("Simulation state saved.")

    def load_state(self):
        """Load the simulation state."""
        print("Loading simulation state...")
        try:
            with open('simulation_state.json', 'r') as f:
                state = json.load(f)
            self.env.state = state['environment']
            for agent_data, agent in zip(state['agents'], self.agents):
                agent.position = agent_data['position']
                agent.q_table = agent_data['q_table']
                agent.total_reward = agent_data['total_reward']
                agent.energy = agent_data['energy']
            print("Simulation state loaded.")
        except FileNotFoundError:
            print("Error: simulation_state.json not found.")

# Initialize and run the simulation
simulation = Simulation3D()
