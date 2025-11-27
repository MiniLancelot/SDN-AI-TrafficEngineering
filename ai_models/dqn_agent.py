"""
Deep Q-Network (DQN) Agent for Intelligent Load Balancing
Sử dụng Reinforcement Learning để tối ưu hóa định tuyến động
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
from collections import deque, namedtuple
import pickle

import sys
sys.path.append('..')
from environment.config import AI_MODELS, RL_ENVIRONMENT, PATHS

# Experience tuple
Experience = namedtuple('Experience', ['state', 'action', 'reward', 'next_state', 'done'])


class DQNetwork(nn.Module):
    """Deep Q-Network"""
    
    def __init__(self, state_size, action_size, hidden_layers=[128, 64]):
        super(DQNetwork, self).__init__()
        
        layers = []
        input_size = state_size
        
        # Build hidden layers
        for hidden_size in hidden_layers:
            layers.append(nn.Linear(input_size, hidden_size))
            layers.append(nn.ReLU())
            input_size = hidden_size
        
        # Output layer
        layers.append(nn.Linear(input_size, action_size))
        
        self.network = nn.Sequential(*layers)
    
    def forward(self, x):
        return self.network(x)


class ReplayBuffer:
    """Experience Replay Buffer"""
    
    def __init__(self, capacity):
        self.buffer = deque(maxlen=capacity)
    
    def push(self, state, action, reward, next_state, done):
        """Add experience to buffer"""
        experience = Experience(state, action, reward, next_state, done)
        self.buffer.append(experience)
    
    def sample(self, batch_size):
        """Sample a batch of experiences"""
        experiences = random.sample(self.buffer, batch_size)
        
        states = torch.FloatTensor([e.state for e in experiences])
        actions = torch.LongTensor([e.action for e in experiences])
        rewards = torch.FloatTensor([e.reward for e in experiences])
        next_states = torch.FloatTensor([e.next_state for e in experiences])
        dones = torch.FloatTensor([e.done for e in experiences])
        
        return states, actions, rewards, next_states, dones
    
    def __len__(self):
        return len(self.buffer)


class DQNAgent:
    """DQN Agent for Load Balancing"""
    
    def __init__(self, state_size, action_size, hidden_layers=[128, 64]):
        """
        Initialize DQN Agent
        Args:
            state_size: dimension of network state (e.g., number of links)
            action_size: number of possible routing paths
            hidden_layers: hidden layer sizes
        """
        self.state_size = state_size
        self.action_size = action_size
        
        # Get configuration
        config = AI_MODELS['dqn']
        self.learning_rate = config['learning_rate']
        self.gamma = config['gamma']  # discount factor
        self.epsilon = config['epsilon_start']
        self.epsilon_min = config['epsilon_end']
        self.epsilon_decay = config['epsilon_decay']
        self.batch_size = config['batch_size']
        self.target_update_freq = config['target_update_frequency']
        
        # Device
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Q-Networks
        self.policy_net = DQNetwork(state_size, action_size, hidden_layers).to(self.device)
        self.target_net = DQNetwork(state_size, action_size, hidden_layers).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()
        
        # Optimizer
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=self.learning_rate)
        self.criterion = nn.MSELoss()
        
        # Replay buffer
        self.memory = ReplayBuffer(config['memory_size'])
        
        # Training statistics
        self.episode_rewards = []
        self.losses = []
        self.update_count = 0
        
        print(f"DQN Agent initialized on {self.device}")
        print(f"State size: {state_size}, Action size: {action_size}")
        print(f"Policy network parameters: {sum(p.numel() for p in self.policy_net.parameters())}")
    
    def select_action(self, state, training=True):
        """
        Select action using epsilon-greedy policy
        Args:
            state: current network state
            training: if True, use epsilon-greedy; if False, use greedy
        Returns:
            action index
        """
        if training and random.random() < self.epsilon:
            # Explore: random action
            return random.randrange(self.action_size)
        else:
            # Exploit: best action according to Q-network
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
                q_values = self.policy_net(state_tensor)
                return q_values.argmax().item()
    
    def store_experience(self, state, action, reward, next_state, done):
        """Store experience in replay buffer"""
        self.memory.push(state, action, reward, next_state, done)
    
    def train_step(self):
        """Perform one training step"""
        if len(self.memory) < self.batch_size:
            return None
        
        # Sample batch from replay buffer
        states, actions, rewards, next_states, dones = self.memory.sample(self.batch_size)
        
        states = states.to(self.device)
        actions = actions.to(self.device)
        rewards = rewards.to(self.device)
        next_states = next_states.to(self.device)
        dones = dones.to(self.device)
        
        # Compute current Q values
        current_q_values = self.policy_net(states).gather(1, actions.unsqueeze(1)).squeeze(1)
        
        # Compute target Q values
        with torch.no_grad():
            next_q_values = self.target_net(next_states).max(1)[0]
            target_q_values = rewards + (1 - dones) * self.gamma * next_q_values
        
        # Compute loss
        loss = self.criterion(current_q_values, target_q_values)
        
        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        # Gradient clipping to prevent exploding gradients
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), 1.0)
        self.optimizer.step()
        
        self.losses.append(loss.item())
        self.update_count += 1
        
        # Update target network
        if self.update_count % self.target_update_freq == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())
        
        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
        
        return loss.item()
    
    def compute_reward(self, network_state, action):
        """
        Compute reward based on network state after taking action
        Args:
            network_state: dict containing network metrics
            action: selected path/action
        Returns:
            reward value
        """
        # Get reward weights from config
        weights = RL_ENVIRONMENT['reward_weights']
        
        # Extract metrics from network state
        max_utilization = network_state.get('max_link_utilization', 0)
        avg_delay = network_state.get('avg_delay', 0)
        packet_loss = network_state.get('packet_loss_rate', 0)
        
        # Compute reward (negative penalties)
        reward = (
            weights['max_utilization'] * max_utilization +
            weights['avg_delay'] * avg_delay +
            weights['packet_loss'] * packet_loss
        )
        
        # Bonus for balanced load (low max utilization)
        if max_utilization < 50:
            reward += 1.0
        
        return reward
    
    def get_network_state_vector(self, network_state):
        """
        Convert network state dict to state vector for neural network
        Args:
            network_state: dict with network metrics
        Returns:
            numpy array representing state
        """
        # Example state representation:
        # - Link utilizations for all links
        # - Current flow distribution
        # - Queue depths
        
        link_utils = network_state.get('link_utilizations', [])
        flow_counts = network_state.get('flow_counts', [])
        queue_depths = network_state.get('queue_depths', [])
        
        # Pad or truncate to state_size
        state_vector = []
        state_vector.extend(link_utils[:self.state_size // 3])
        state_vector.extend(flow_counts[:self.state_size // 3])
        state_vector.extend(queue_depths[:self.state_size // 3])
        
        # Pad with zeros if needed
        while len(state_vector) < self.state_size:
            state_vector.append(0.0)
        
        return np.array(state_vector[:self.state_size], dtype=np.float32)
    
    def train_episode(self, env, max_steps=1000):
        """
        Train for one episode
        Args:
            env: network environment
            max_steps: maximum steps per episode
        Returns:
            total reward
        """
        state = env.reset()
        state_vector = self.get_network_state_vector(state)
        
        total_reward = 0
        
        for step in range(max_steps):
            # Select action
            action = self.select_action(state_vector, training=True)
            
            # Take action in environment
            next_state, reward, done = env.step(action)
            next_state_vector = self.get_network_state_vector(next_state)
            
            # Store experience
            self.store_experience(state_vector, action, reward, next_state_vector, done)
            
            # Train
            loss = self.train_step()
            
            total_reward += reward
            state_vector = next_state_vector
            
            if done:
                break
        
        self.episode_rewards.append(total_reward)
        return total_reward
    
    def evaluate(self, env, num_episodes=10):
        """
        Evaluate agent performance
        Args:
            env: network environment
            num_episodes: number of episodes to evaluate
        Returns:
            average reward
        """
        total_rewards = []
        
        for episode in range(num_episodes):
            state = env.reset()
            state_vector = self.get_network_state_vector(state)
            episode_reward = 0
            
            done = False
            while not done:
                action = self.select_action(state_vector, training=False)
                next_state, reward, done = env.step(action)
                state_vector = self.get_network_state_vector(next_state)
                episode_reward += reward
            
            total_rewards.append(episode_reward)
        
        return np.mean(total_rewards)
    
    def save(self, filepath):
        """Save agent to file"""
        torch.save({
            'policy_net_state_dict': self.policy_net.state_dict(),
            'target_net_state_dict': self.target_net.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'episode_rewards': self.episode_rewards,
            'losses': self.losses,
        }, filepath)
        print(f"Agent saved to {filepath}")
    
    def load(self, filepath):
        """Load agent from file"""
        checkpoint = torch.load(filepath, map_location=self.device)
        self.policy_net.load_state_dict(checkpoint['policy_net_state_dict'])
        self.target_net.load_state_dict(checkpoint['target_net_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.epsilon = checkpoint['epsilon']
        self.episode_rewards = checkpoint['episode_rewards']
        self.losses = checkpoint['losses']
        print(f"Agent loaded from {filepath}")


class NetworkEnvironment:
    """
    Simulated Network Environment for DQN Training
    This is a simplified environment - replace with actual network simulation
    """
    
    def __init__(self, num_links=10, num_paths=4):
        self.num_links = num_links
        self.num_paths = num_paths
        self.reset()
    
    def reset(self):
        """Reset environment to initial state"""
        self.link_utilizations = np.random.uniform(20, 40, self.num_links)
        self.flow_counts = np.zeros(self.num_paths)
        self.queue_depths = np.zeros(self.num_links)
        self.step_count = 0
        
        return self._get_state()
    
    def step(self, action):
        """
        Take action (select path) and return next state, reward, done
        Args:
            action: selected path index
        Returns:
            next_state, reward, done
        """
        self.step_count += 1
        
        # Simulate routing flow on selected path
        # This affects link utilizations on that path
        path_links = self._get_path_links(action)
        
        # Add load to links on selected path
        flow_size = np.random.uniform(1, 5)
        for link in path_links:
            self.link_utilizations[link] += flow_size
        
        self.flow_counts[action] += 1
        
        # Natural decay of utilization (flows finish)
        self.link_utilizations *= 0.95
        self.link_utilizations = np.clip(self.link_utilizations, 0, 100)
        
        # Compute reward
        max_util = np.max(self.link_utilizations)
        avg_util = np.mean(self.link_utilizations)
        std_util = np.std(self.link_utilizations)
        
        # Reward: minimize max utilization and variance (balanced load)
        reward = -max_util / 100.0 - std_util / 50.0
        
        # Bonus for balanced utilization
        if max_util < 50:
            reward += 0.5
        
        # Penalty for over-utilization
        if max_util > 80:
            reward -= 1.0
        
        # Episode terminates after certain steps or if congestion occurs
        done = self.step_count >= 100 or max_util > 95
        
        next_state = self._get_state()
        
        return next_state, reward, done
    
    def _get_state(self):
        """Get current state as dict"""
        return {
            'link_utilizations': self.link_utilizations.tolist(),
            'flow_counts': self.flow_counts.tolist(),
            'queue_depths': self.queue_depths.tolist(),
            'max_link_utilization': np.max(self.link_utilizations),
            'avg_delay': np.mean(self.link_utilizations) * 0.1,  # simplified
            'packet_loss_rate': max(0, (np.max(self.link_utilizations) - 80) / 20)
        }
    
    def _get_path_links(self, path_id):
        """Get links belonging to a path (simplified)"""
        # This is a simplified mapping - in real scenario, 
        # use actual topology to determine which links are on each path
        links_per_path = self.num_links // self.num_paths
        start = path_id * links_per_path
        end = start + links_per_path
        return list(range(start, min(end, self.num_links)))


if __name__ == "__main__":
    # Example usage
    print("Testing DQN Agent for Load Balancing...")
    
    # Create environment
    env = NetworkEnvironment(num_links=12, num_paths=4)
    
    # Create agent
    state_size = 20  # Size of state vector
    action_size = 4  # Number of routing paths
    agent = DQNAgent(state_size, action_size, hidden_layers=[128, 64])
    
    # Training
    print("\nTraining agent...")
    num_episodes = 100
    
    for episode in range(num_episodes):
        total_reward = agent.train_episode(env, max_steps=100)
        
        if (episode + 1) % 10 == 0:
            avg_reward = np.mean(agent.episode_rewards[-10:])
            print(f"Episode {episode + 1}/{num_episodes}, "
                  f"Avg Reward: {avg_reward:.2f}, "
                  f"Epsilon: {agent.epsilon:.3f}")
    
    # Evaluation
    print("\nEvaluating agent...")
    avg_reward = agent.evaluate(env, num_episodes=10)
    print(f"Average evaluation reward: {avg_reward:.2f}")
    
    # Save agent
    import os
    model_path = os.path.join(PATHS['models'], 'dqn_load_balancer.pth')
    agent.save(model_path)
    
    print("\nTraining completed!")
