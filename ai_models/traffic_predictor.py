"""
Traffic Predictor using LSTM Neural Network
Dự đoán traffic matrix và phát hiện xu hướng tắc nghẽn
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from collections import deque
import pickle
import os

import sys
sys.path.append('..')
from environment.config import AI_MODELS, PATHS


class LSTMPredictor(nn.Module):
    """LSTM Model for Traffic Prediction"""
    
    def __init__(self, input_size=1, hidden_size=64, num_layers=2, output_size=1, dropout=0.2):
        super(LSTMPredictor, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # LSTM layers
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout,
            batch_first=True
        )
        
        # Fully connected layer
        self.fc = nn.Linear(hidden_size, output_size)
        
    def forward(self, x):
        # Initialize hidden state and cell state
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        
        # Forward propagate LSTM
        out, _ = self.lstm(x, (h0, c0))
        
        # Decode the hidden state of the last time step
        out = self.fc(out[:, -1, :])
        return out


class TrafficPredictor:
    """Traffic Prediction System using LSTM"""
    
    def __init__(self, sequence_length=10, hidden_size=64, num_layers=2):
        self.sequence_length = sequence_length
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # Model configuration from config.py
        config = AI_MODELS['lstm']
        self.learning_rate = config['learning_rate']
        self.batch_size = config['batch_size']
        self.epochs = config['epochs']
        self.dropout = config['dropout']
        
        # Initialize model
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = LSTMPredictor(
            input_size=1,
            hidden_size=hidden_size,
            num_layers=num_layers,
            output_size=1,
            dropout=self.dropout
        ).to(self.device)
        
        self.criterion = nn.MSELoss()
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        
        # Data buffer for online prediction
        self.data_buffer = deque(maxlen=sequence_length)
        
        # Statistics
        self.train_losses = []
        self.val_losses = []
        
        print(f"Traffic Predictor initialized on {self.device}")
        print(f"Model parameters: {sum(p.numel() for p in self.model.parameters())} total")
    
    def prepare_sequences(self, data, sequence_length):
        """
        Prepare sequences for LSTM training
        Args:
            data: list or array of traffic values
            sequence_length: length of input sequence
        Returns:
            X: input sequences, y: target values
        """
        X, y = [], []
        
        for i in range(len(data) - sequence_length):
            X.append(data[i:i + sequence_length])
            y.append(data[i + sequence_length])
        
        return np.array(X), np.array(y)
    
    def normalize_data(self, data):
        """Normalize data to [0, 1] range"""
        data = np.array(data)
        self.data_min = np.min(data)
        self.data_max = np.max(data)
        
        if self.data_max - self.data_min == 0:
            return data
        
        normalized = (data - self.data_min) / (self.data_max - self.data_min)
        return normalized
    
    def denormalize_data(self, normalized_data):
        """Denormalize data back to original scale"""
        return normalized_data * (self.data_max - self.data_min) + self.data_min
    
    def train(self, train_data, val_data=None, epochs=None):
        """
        Train LSTM model
        Args:
            train_data: training data (list of traffic values)
            val_data: validation data (optional)
            epochs: number of training epochs
        """
        if epochs is None:
            epochs = self.epochs
        
        # Normalize data
        train_data_norm = self.normalize_data(train_data)
        
        # Prepare sequences
        X_train, y_train = self.prepare_sequences(train_data_norm, self.sequence_length)
        
        # Convert to tensors
        X_train = torch.FloatTensor(X_train).unsqueeze(-1).to(self.device)
        y_train = torch.FloatTensor(y_train).unsqueeze(-1).to(self.device)
        
        # Validation data
        if val_data is not None:
            val_data_norm = self.normalize_data(val_data)
            X_val, y_val = self.prepare_sequences(val_data_norm, self.sequence_length)
            X_val = torch.FloatTensor(X_val).unsqueeze(-1).to(self.device)
            y_val = torch.FloatTensor(y_val).unsqueeze(-1).to(self.device)
        
        # Training loop
        self.model.train()
        for epoch in range(epochs):
            # Forward pass
            outputs = self.model(X_train)
            loss = self.criterion(outputs, y_train)
            
            # Backward and optimize
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
            
            self.train_losses.append(loss.item())
            
            # Validation
            if val_data is not None:
                self.model.eval()
                with torch.no_grad():
                    val_outputs = self.model(X_val)
                    val_loss = self.criterion(val_outputs, y_val)
                    self.val_losses.append(val_loss.item())
                self.model.train()
            
            if (epoch + 1) % 10 == 0:
                if val_data is not None:
                    print(f'Epoch [{epoch+1}/{epochs}], Train Loss: {loss.item():.4f}, Val Loss: {val_loss.item():.4f}')
                else:
                    print(f'Epoch [{epoch+1}/{epochs}], Loss: {loss.item():.4f}')
        
        print("Training completed!")
    
    def predict(self, sequence):
        """
        Predict next traffic value given a sequence
        Args:
            sequence: list of recent traffic values (length = sequence_length)
        Returns:
            predicted value
        """
        self.model.eval()
        
        # Normalize input
        sequence_norm = (np.array(sequence) - self.data_min) / (self.data_max - self.data_min)
        
        # Convert to tensor
        x = torch.FloatTensor(sequence_norm).unsqueeze(0).unsqueeze(-1).to(self.device)
        
        with torch.no_grad():
            prediction_norm = self.model(x).cpu().numpy()[0, 0]
        
        # Denormalize prediction
        prediction = self.denormalize_data(prediction_norm)
        
        return prediction
    
    def predict_next_step(self, current_value):
        """
        Predict next step using buffer
        Args:
            current_value: current traffic value
        Returns:
            predicted next value
        """
        self.data_buffer.append(current_value)
        
        if len(self.data_buffer) < self.sequence_length:
            return current_value  # Not enough data yet
        
        sequence = list(self.data_buffer)
        return self.predict(sequence)
    
    def predict_future(self, sequence, steps=5):
        """
        Predict multiple future steps
        Args:
            sequence: initial sequence
            steps: number of future steps to predict
        Returns:
            list of predicted values
        """
        predictions = []
        current_sequence = list(sequence)
        
        for _ in range(steps):
            next_value = self.predict(current_sequence)
            predictions.append(next_value)
            current_sequence.pop(0)
            current_sequence.append(next_value)
        
        return predictions
    
    def detect_congestion(self, sequence, threshold=80.0):
        """
        Detect potential congestion based on prediction
        Args:
            sequence: recent traffic data
            threshold: congestion threshold (e.g., 80% utilization)
        Returns:
            dict with congestion info
        """
        future_predictions = self.predict_future(sequence, steps=5)
        
        congestion_detected = any(pred > threshold for pred in future_predictions)
        max_predicted = max(future_predictions)
        
        return {
            'congestion_detected': congestion_detected,
            'max_predicted_utilization': max_predicted,
            'predictions': future_predictions,
            'current_utilization': sequence[-1] if sequence else 0
        }
    
    def save_model(self, filepath):
        """Save model to file"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'data_min': self.data_min,
            'data_max': self.data_max,
            'train_losses': self.train_losses,
            'val_losses': self.val_losses,
        }, filepath)
        print(f"Model saved to {filepath}")
    
    def load_model(self, filepath):
        """Load model from file"""
        checkpoint = torch.load(filepath, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.data_min = checkpoint['data_min']
        self.data_max = checkpoint['data_max']
        self.train_losses = checkpoint['train_losses']
        self.val_losses = checkpoint['val_losses']
        print(f"Model loaded from {filepath}")


def generate_sample_traffic_data(num_samples=1000):
    """Generate synthetic traffic data for testing"""
    # Simulate traffic pattern: base load + periodic peaks + random noise
    t = np.linspace(0, 10, num_samples)
    base_load = 30
    periodic = 20 * np.sin(2 * np.pi * t)  # Daily pattern
    peaks = 15 * np.sin(10 * np.pi * t)  # Short-term variations
    noise = np.random.normal(0, 5, num_samples)
    
    traffic = base_load + periodic + peaks + noise
    traffic = np.clip(traffic, 0, 100)  # Clip to [0, 100] range
    
    return traffic


if __name__ == "__main__":
    # Example usage
    print("Testing Traffic Predictor...")
    
    # Generate sample data
    traffic_data = generate_sample_traffic_data(num_samples=1000)
    
    # Split data
    train_size = int(0.8 * len(traffic_data))
    train_data = traffic_data[:train_size]
    test_data = traffic_data[train_size:]
    
    # Initialize predictor
    predictor = TrafficPredictor(sequence_length=10, hidden_size=64, num_layers=2)
    
    # Train model
    print("\nTraining model...")
    predictor.train(train_data, epochs=50)
    
    # Test prediction
    print("\nTesting prediction...")
    test_sequence = test_data[:10].tolist()
    prediction = predictor.predict(test_sequence)
    actual = test_data[10]
    
    print(f"Input sequence: {[f'{x:.2f}' for x in test_sequence]}")
    print(f"Predicted: {prediction:.2f}, Actual: {actual:.2f}, Error: {abs(prediction - actual):.2f}")
    
    # Test congestion detection
    print("\nTesting congestion detection...")
    high_traffic_sequence = [70, 72, 75, 78, 80, 82, 84, 85, 87, 88]
    congestion_info = predictor.detect_congestion(high_traffic_sequence, threshold=80)
    print(f"Congestion detected: {congestion_info['congestion_detected']}")
    print(f"Max predicted utilization: {congestion_info['max_predicted_utilization']:.2f}%")
    print(f"Future predictions: {[f'{x:.2f}' for x in congestion_info['predictions']]}")
    
    # Save model
    model_path = os.path.join(PATHS['models'], 'lstm_traffic_predictor.pth')
    predictor.save_model(model_path)
