"""
Utilities for data preprocessing and handling
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, StandardScaler
import pickle
import os


class DataProcessor:
    """Data preprocessing utilities for AI models"""
    
    def __init__(self):
        self.scaler = None
        self.feature_names = []
    
    def normalize(self, data, method='minmax'):
        """
        Normalize data
        Args:
            data: numpy array or pandas DataFrame
            method: 'minmax' or 'standard'
        Returns:
            normalized data
        """
        if method == 'minmax':
            self.scaler = MinMaxScaler()
        elif method == 'standard':
            self.scaler = StandardScaler()
        else:
            raise ValueError(f"Unknown normalization method: {method}")
        
        if isinstance(data, pd.DataFrame):
            self.feature_names = data.columns.tolist()
            normalized = self.scaler.fit_transform(data.values)
            return pd.DataFrame(normalized, columns=data.columns, index=data.index)
        else:
            return self.scaler.fit_transform(data)
    
    def denormalize(self, normalized_data):
        """Denormalize data back to original scale"""
        if self.scaler is None:
            raise ValueError("Scaler not fitted yet")
        
        return self.scaler.inverse_transform(normalized_data)
    
    def create_sequences(self, data, sequence_length, target_col=None):
        """
        Create sequences for time series prediction
        Args:
            data: input data (DataFrame or array)
            sequence_length: length of input sequence
            target_col: column name for target (if DataFrame)
        Returns:
            X (sequences), y (targets)
        """
        X, y = [], []
        
        if isinstance(data, pd.DataFrame):
            if target_col:
                values = data[target_col].values
            else:
                values = data.values
        else:
            values = data
        
        for i in range(len(values) - sequence_length):
            X.append(values[i:i + sequence_length])
            y.append(values[i + sequence_length])
        
        return np.array(X), np.array(y)
    
    def load_csv_data(self, filepath, parse_dates=True):
        """Load data from CSV file"""
        df = pd.read_csv(filepath)
        
        if parse_dates and 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
        
        return df
    
    def extract_traffic_features(self, df):
        """
        Extract features from traffic data
        Args:
            df: DataFrame with traffic statistics
        Returns:
            DataFrame with engineered features
        """
        features = pd.DataFrame()
        
        # Basic features
        if 'tx_bytes' in df.columns and 'rx_bytes' in df.columns:
            features['total_bytes'] = df['tx_bytes'] + df['rx_bytes']
            features['byte_ratio'] = df['tx_bytes'] / (df['rx_bytes'] + 1)
        
        if 'tx_packets' in df.columns and 'rx_packets' in df.columns:
            features['total_packets'] = df['tx_packets'] + df['rx_packets']
            features['packet_ratio'] = df['tx_packets'] / (df['rx_packets'] + 1)
        
        # Speed features
        if 'tx_speed_mbps' in df.columns and 'rx_speed_mbps' in df.columns:
            features['total_speed_mbps'] = df['tx_speed_mbps'] + df['rx_speed_mbps']
            features['speed_variance'] = np.abs(df['tx_speed_mbps'] - df['rx_speed_mbps'])
        
        # Statistical features (rolling window)
        window = 5
        for col in df.select_dtypes(include=[np.number]).columns:
            features[f'{col}_mean_{window}'] = df[col].rolling(window=window).mean()
            features[f'{col}_std_{window}'] = df[col].rolling(window=window).std()
        
        features.fillna(0, inplace=True)
        
        return features
    
    def split_train_test(self, data, train_ratio=0.8):
        """Split data into training and testing sets"""
        split_idx = int(len(data) * train_ratio)
        
        if isinstance(data, pd.DataFrame):
            train = data.iloc[:split_idx]
            test = data.iloc[split_idx:]
        else:
            train = data[:split_idx]
            test = data[split_idx:]
        
        return train, test
    
    def save_scaler(self, filepath):
        """Save scaler to file"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(self.scaler, f)
        print(f"Scaler saved to {filepath}")
    
    def load_scaler(self, filepath):
        """Load scaler from file"""
        with open(filepath, 'rb') as f:
            self.scaler = pickle.load(f)
        print(f"Scaler loaded from {filepath}")


class FlowAnalyzer:
    """Analyze network flows"""
    
    @staticmethod
    def identify_elephant_flows(flow_stats, threshold_bytes=1000000):
        """
        Identify elephant flows
        Args:
            flow_stats: list of flow statistics
            threshold_bytes: minimum bytes for elephant flow
        Returns:
            list of elephant flows
        """
        elephant_flows = []
        
        for flow in flow_stats:
            if flow.get('byte_count', 0) >= threshold_bytes:
                elephant_flows.append(flow)
        
        # Sort by byte count
        elephant_flows.sort(key=lambda x: x.get('byte_count', 0), reverse=True)
        
        return elephant_flows
    
    @staticmethod
    def compute_flow_metrics(flow_stats):
        """
        Compute metrics for flow statistics
        Args:
            flow_stats: list of flow statistics
        Returns:
            dict with metrics
        """
        if not flow_stats:
            return {
                'total_flows': 0,
                'total_bytes': 0,
                'total_packets': 0,
                'avg_flow_size': 0,
                'avg_flow_duration': 0
            }
        
        total_bytes = sum(f.get('byte_count', 0) for f in flow_stats)
        total_packets = sum(f.get('packet_count', 0) for f in flow_stats)
        total_duration = sum(f.get('duration_sec', 0) for f in flow_stats)
        
        return {
            'total_flows': len(flow_stats),
            'total_bytes': total_bytes,
            'total_packets': total_packets,
            'avg_flow_size': total_bytes / len(flow_stats),
            'avg_flow_duration': total_duration / len(flow_stats),
            'avg_packet_size': total_bytes / total_packets if total_packets > 0 else 0
        }
    
    @staticmethod
    def detect_anomalies(flow_stats, std_multiplier=3):
        """
        Detect anomalous flows using statistical method
        Args:
            flow_stats: list of flow statistics
            std_multiplier: number of standard deviations for threshold
        Returns:
            list of anomalous flows
        """
        if not flow_stats:
            return []
        
        byte_counts = [f.get('byte_count', 0) for f in flow_stats]
        mean = np.mean(byte_counts)
        std = np.std(byte_counts)
        
        threshold = mean + std_multiplier * std
        
        anomalies = [f for f in flow_stats if f.get('byte_count', 0) > threshold]
        
        return anomalies


if __name__ == "__main__":
    # Test data processor
    print("Testing Data Processor...")
    
    processor = DataProcessor()
    
    # Generate sample data
    data = np.random.rand(100, 5) * 100
    
    # Normalize
    normalized = processor.normalize(data, method='minmax')
    print(f"Original shape: {data.shape}")
    print(f"Normalized shape: {normalized.shape}")
    print(f"Normalized range: [{normalized.min():.2f}, {normalized.max():.2f}]")
    
    # Create sequences
    X, y = processor.create_sequences(data[:, 0], sequence_length=10)
    print(f"\nSequences created:")
    print(f"  X shape: {X.shape}")
    print(f"  y shape: {y.shape}")
    
    print("\n✓ Data processor test completed!")
