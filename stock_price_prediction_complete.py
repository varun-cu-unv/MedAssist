#!/usr/bin/env python3
"""
Stock Price Prediction using CNN-based Sliding Window Model
==========================================================

This script implements a comprehensive stock price prediction system using 
CNN-based sliding window methodology based on Selvin et al. (2017).

Author: AI Assistant
Date: 2024
License: MIT

Usage:
    python stock_price_prediction_complete.py
"""

# Install required packages (uncomment for first run)
# !pip install yfinance pandas numpy matplotlib seaborn scikit-learn tensorflow plotly

# Import necessary libraries
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv1D, MaxPooling1D, Flatten, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.optimizers import Adam

print("✅ All packages imported successfully!")
print(f"TensorFlow version: {tf.__version__}")
print(f"GPU Available: {len(tf.config.experimental.list_physical_devices('GPU')) > 0}")


class StockDataFetcher:
    """
    Handles fetching and preprocessing stock data from Yahoo Finance
    """
    
    def __init__(self):
        self.symbols = {
            'INFY': 'INFY.NS',
            'TCS': 'TCS.NS', 
            'CIPLA': 'CIPLA.NS'
        }
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        
    def fetch_stock_data(self, symbol, start_date, end_date, interval='1d'):
        """
        Fetch stock data from Yahoo Finance
        """
        try:
            print(f"Fetching data for {symbol} from {start_date} to {end_date}...")
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date, interval=interval)
            
            if data.empty:
                print(f"❌ No data available for {symbol} in the specified period")
                return pd.DataFrame()
            
            # Clean and prepare data
            data = data.dropna()
            data['Symbol'] = symbol
            
            print(f"✅ Successfully fetched {len(data)} data points for {symbol}")
            return data
            
        except Exception as e:
            print(f"❌ Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_training_data(self):
        """Fetch training data: Infosys from July 1, 2014 to October 14, 2014"""
        print("\n📊 Fetching Training Data...")
        print("=" * 50)
        
        train_data = self.fetch_stock_data(
            symbol=self.symbols['INFY'],
            start_date='2014-07-01',
            end_date='2014-10-14',
            interval='1d'
        )
        
        if train_data.empty:
            print("⚠️ Training data not available, using simulated data for demonstration")
            train_data = self._generate_simulated_data('INFY.NS', '2014-07-01', '2014-10-14')
        
        return train_data
    
    def get_testing_data(self):
        """Fetch testing data for all three companies"""
        print("\n📊 Fetching Testing Data...")
        print("=" * 50)
        
        test_data = {}
        
        for company, symbol in self.symbols.items():
            data = self.fetch_stock_data(
                symbol=symbol,
                start_date='2014-10-16',
                end_date='2014-11-28',
                interval='1d'
            )
            
            if data.empty:
                print(f"⚠️ Testing data for {company} not available, using simulated data")
                data = self._generate_simulated_data(symbol, '2014-10-16', '2014-11-28')
            
            test_data[company] = data
        
        return test_data
    
    def _generate_simulated_data(self, symbol, start_date, end_date):
        """Generate simulated stock data for demonstration"""
        print(f"🔄 Generating simulated data for {symbol}...")
        
        # Create date range
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        # Generate business days only
        business_days = pd.bdate_range(start=start, end=end)
        
        # Create minute-wise data (9:15 AM to 3:30 PM IST trading hours)
        all_timestamps = []
        for day in business_days:
            day_start = day.replace(hour=9, minute=15)
            day_end = day.replace(hour=15, minute=30)
            minute_range = pd.date_range(start=day_start, end=day_end, freq='1min')
            all_timestamps.extend(minute_range)
        
        # Generate realistic stock price data
        np.random.seed(42)  # For reproducible results
        
        # Base prices for different companies
        base_prices = {'INFY.NS': 1200, 'TCS.NS': 2300, 'CIPLA.NS': 450}
        base_price = base_prices.get(symbol, 1000)
        
        n_points = len(all_timestamps)
        
        # Generate price series with realistic patterns
        price_changes = np.random.normal(0, 0.002, n_points)
        trend = np.linspace(-0.1, 0.1, n_points)
        noise = np.random.normal(0, 0.001, n_points)
        
        prices = [base_price]
        for i in range(1, n_points):
            change = price_changes[i] + trend[i] + noise[i]
            new_price = prices[-1] * (1 + change)
            prices.append(max(new_price, base_price * 0.8))
        
        # Create DataFrame
        data = pd.DataFrame({
            'Open': prices,
            'High': [p * (1 + abs(np.random.normal(0, 0.005))) for p in prices],
            'Low': [p * (1 - abs(np.random.normal(0, 0.005))) for p in prices],
            'Close': prices,
            'Volume': np.random.randint(1000, 50000, n_points)
        }, index=all_timestamps)
        
        data['Symbol'] = symbol
        
        print(f"✅ Generated {len(data)} simulated data points for {symbol}")
        return data
    
    def preprocess_data(self, data, feature_column='Close'):
        """Apply MinMax scaling to normalize values between 0 and 1"""
        if data.empty:
            return np.array([]), np.array([]), None
        
        # Extract the feature column
        prices = data[feature_column].values.reshape(-1, 1)
        
        # Apply MinMax scaling
        scaled_prices = self.scaler.fit_transform(prices)
        
        print(f"✅ Data preprocessed: {len(prices)} points scaled to [0, 1] range")
        print(f"   Original range: [{prices.min():.2f}, {prices.max():.2f}]")
        
        return scaled_prices.flatten(), prices.flatten(), self.scaler


class SlidingWindowGenerator:
    """
    Creates sliding windows for time series prediction
    """
    
    def __init__(self, window_size=100, overlap=90, prediction_steps=10):
        self.window_size = window_size
        self.overlap = overlap
        self.stride = window_size - overlap
        self.prediction_steps = prediction_steps
        
        print(f"SlidingWindowGenerator initialized:")
        print(f"  Window size: {self.window_size}")
        print(f"  Overlap: {self.overlap}")
        print(f"  Stride: {self.stride}")
        print(f"  Prediction steps: {self.prediction_steps}")
    
    def create_sliding_windows(self, data):
        """Create sliding windows from time series data"""
        if len(data) < self.window_size + self.prediction_steps:
            print(f"❌ Insufficient data: need at least {self.window_size + self.prediction_steps} points, got {len(data)}")
            return np.array([]), np.array([])
        
        X, y = [], []
        
        # Generate sliding windows
        for i in range(0, len(data) - self.window_size - self.prediction_steps + 1, self.stride):
            # Input window
            window = data[i:i + self.window_size]
            X.append(window)
            
            # Target sequence
            target = data[i + self.window_size:i + self.window_size + self.prediction_steps]
            y.append(target)
        
        X = np.array(X)
        y = np.array(y)
        
        # Reshape X for CNN input (samples, timesteps, features)
        X = X.reshape(X.shape[0], X.shape[1], 1)
        
        print(f"✅ Created {len(X)} sliding windows")
        print(f"   Input shape: {X.shape}")
        print(f"   Target shape: {y.shape}")
        
        return X, y


class CNNStockPredictor:
    """CNN-based sliding window model for stock price prediction"""
    
    def __init__(self, window_size=100, prediction_steps=10):
        self.window_size = window_size
        self.prediction_steps = prediction_steps
        self.model = None
        self.history = None
        
    def build_model(self, input_shape=(100, 1)):
        """Build CNN model with Conv1D layers"""
        print(f"\n🏗️ Building CNN model with input shape: {input_shape}")
        
        self.model = Sequential([
            # First Conv1D layer
            Conv1D(filters=64, kernel_size=3, activation='relu', 
                   input_shape=input_shape, name='conv1d_1'),
            MaxPooling1D(pool_size=2, name='maxpool_1'),
            
            # Second Conv1D layer
            Conv1D(filters=32, kernel_size=3, activation='relu', name='conv1d_2'),
            MaxPooling1D(pool_size=2, name='maxpool_2'),
            
            # Third Conv1D layer
            Conv1D(filters=16, kernel_size=3, activation='relu', name='conv1d_3'),
            
            # Flatten layer
            Flatten(name='flatten'),
            
            # Dense layers
            Dense(100, activation='relu', name='dense_1'),
            Dropout(0.2, name='dropout_1'),
            Dense(50, activation='relu', name='dense_2'),
            Dropout(0.2, name='dropout_2'),
            
            # Output layer
            Dense(self.prediction_steps, activation='linear', name='output')
        ])
        
        # Compile model
        self.model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        print("✅ Model built and compiled!")
        self.model.summary()
        
        return self.model
    
    def train_model(self, X_train, y_train, X_val=None, y_val=None, 
                   epochs=200, batch_size=32, early_stopping=True):
        """Train the CNN model with early stopping"""
        if self.model is None:
            print("❌ Model not built yet. Call build_model() first.")
            return None
        
        print(f"\n🚀 Training model...")
        print(f"  Training data shape: {X_train.shape} → {y_train.shape}")
        
        if X_val is not None:
            validation_data = (X_val, y_val)
        else:
            validation_data = None
        
        callbacks = []
        if early_stopping:
            early_stop = EarlyStopping(
                monitor='val_loss' if validation_data else 'loss',
                patience=50,
                restore_best_weights=True,
                verbose=1
            )
            callbacks.append(early_stop)
        
        # Train the model
        self.history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_data=validation_data,
            callbacks=callbacks,
            verbose=1
        )
        
        print("✅ Training completed!")
        return self.history
    
    def predict(self, X):
        """Make predictions using the trained model"""
        if self.model is None:
            print("❌ Model not built yet")
            return None
        
        predictions = self.model.predict(X, verbose=0)
        return predictions


class ModelEvaluator:
    """Comprehensive evaluation of stock prediction models"""
    
    def __init__(self):
        self.results = {}
        
    def calculate_metrics(self, y_true, y_pred, company_name="Unknown"):
        """Calculate comprehensive evaluation metrics"""
        # Ensure arrays are properly shaped
        if y_true.ndim > 1:
            y_true = y_true.flatten()
        if y_pred.ndim > 1:
            y_pred = y_pred.flatten()
        
        # Calculate metrics
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_true, y_pred)
        
        # Additional metrics
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        
        # R-squared
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        metrics = {
            'company': company_name,
            'mse': mse,
            'rmse': rmse,
            'mae': mae,
            'mape': mape,
            'r2_score': r2,
            'n_samples': len(y_true)
        }
        
        # Store results
        self.results[company_name] = metrics
        
        return metrics
    
    def print_metrics(self, metrics):
        """Print formatted metrics"""
        print(f"\n📊 Evaluation Results for {metrics['company']}")
        print("=" * 50)
        print(f"  Sample Size: {metrics['n_samples']}")
        print(f"  RMSE: {metrics['rmse']:.6f}")
        print(f"  MAE: {metrics['mae']:.6f}")
        print(f"  MSE: {metrics['mse']:.6f}")
        print(f"  MAPE: {metrics['mape']:.2f}%")
        print(f"  R² Score: {metrics['r2_score']:.4f}")


# Main execution pipeline
def main():
    """Main execution pipeline"""
    print("🚀 Starting Stock Price Prediction Pipeline")
    print("=" * 60)
    
    # Initialize components
    data_fetcher = StockDataFetcher()
    window_generator = SlidingWindowGenerator(window_size=100, overlap=90, prediction_steps=10)
    cnn_predictor = CNNStockPredictor(window_size=100, prediction_steps=10)
    evaluator = ModelEvaluator()
    
    # Step 1: Load and preprocess training data
    train_data_raw = data_fetcher.get_training_data()
    train_scaled, train_original, train_scaler = data_fetcher.preprocess_data(train_data_raw)
    
    print(f"\n📊 Training Data Summary:")
    print(f"  Raw data points: {len(train_data_raw)}")
    print(f"  Scaled data points: {len(train_scaled)}")
    
    # Step 2: Create sliding windows
    X_train, y_train = window_generator.create_sliding_windows(train_scaled)
    
    if len(X_train) == 0:
        print("❌ Failed to create windows. Insufficient training data.")
        return
    
    # Step 3: Build and train model
    model = cnn_predictor.build_model(input_shape=(X_train.shape[1], X_train.shape[2]))
    
    # Split for validation
    split_idx = int(0.8 * len(X_train))
    X_train_split = X_train[:split_idx]
    y_train_split = y_train[:split_idx]
    X_val_split = X_train[split_idx:]
    y_val_split = y_train[split_idx:]
    
    # Train model
    history = cnn_predictor.train_model(
        X_train_split, y_train_split,
        X_val_split, y_val_split,
        epochs=100,  # Reduced for faster execution
        batch_size=16,
        early_stopping=True
    )
    
    # Step 4: Evaluate on test data
    test_data_raw = data_fetcher.get_testing_data()
    
    for company_name, company_data in test_data_raw.items():
        print(f"\n📊 Evaluating {company_name}...")
        
        if company_data.empty:
            continue
        
        # Preprocess test data
        test_scaled, test_original, _ = data_fetcher.preprocess_data(company_data)
        
        # Create sliding windows
        X_test, y_test = window_generator.create_sliding_windows(test_scaled)
        
        if len(X_test) == 0:
            continue
        
        # Make predictions
        y_pred = cnn_predictor.predict(X_test)
        
        # Calculate and display metrics
        metrics = evaluator.calculate_metrics(y_test, y_pred, company_name)
        evaluator.print_metrics(metrics)
    
    # Final summary
    print(f"\n🎯 PIPELINE COMPLETED SUCCESSFULLY!")
    print(f"✅ Companies evaluated: {len(evaluator.results)}")
    
    if evaluator.results:
        best_company = min(evaluator.results.keys(), key=lambda x: evaluator.results[x]['rmse'])
        print(f"🏆 Best performance: {best_company} (RMSE: {evaluator.results[best_company]['rmse']:.6f})")


if __name__ == "__main__":
    main()