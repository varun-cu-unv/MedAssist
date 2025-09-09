#!/usr/bin/env python3
"""
Stock Price Prediction Demo
===========================

A simplified demo of the CNN-based stock prediction system.
This script demonstrates the core functionality with minimal dependencies.

Usage:
    python stock_prediction_demo.py
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def generate_demo_stock_data(symbol, n_days=100, base_price=1000):
    """Generate realistic demo stock data"""
    np.random.seed(42)
    
    # Create timestamps
    start_date = datetime.now() - timedelta(days=n_days)
    timestamps = pd.date_range(start=start_date, periods=n_days, freq='D')
    
    # Generate price series
    price_changes = np.random.normal(0, 0.02, n_days)
    trend = np.linspace(-0.05, 0.05, n_days)
    
    prices = [base_price]
    for i in range(1, n_days):
        change = price_changes[i] + trend[i]
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, base_price * 0.8))
    
    return pd.DataFrame({
        'Close': prices,
        'Volume': np.random.randint(1000, 10000, n_days)
    }, index=timestamps)

def create_simple_windows(data, window_size=10, prediction_steps=3):
    """Create simple sliding windows"""
    X, y = [], []
    
    for i in range(len(data) - window_size - prediction_steps + 1):
        X.append(data[i:i + window_size])
        y.append(data[i + window_size:i + window_size + prediction_steps])
    
    return np.array(X), np.array(y)

def simple_prediction_model(X_train, y_train, X_test):
    """Simple linear prediction model for demo"""
    # Calculate simple trend from training data
    trends = []
    for x, y in zip(X_train, y_train):
        if len(x) > 1 and len(y) > 0:
            trend = (y[0] - x[-1]) / max(x[-1], 0.001)  # Avoid division by zero
            if np.isfinite(trend):  # Only add valid trends
                trends.append(trend)
    
    avg_trend = np.mean(trends) if trends else 0.01
    
    # Predict using average trend
    predictions = []
    for x in X_test:
        pred = []
        last_price = x[-1]
        for step in range(3):  # 3 prediction steps
            next_price = last_price * (1 + avg_trend)
            pred.append(next_price)
            last_price = next_price
        predictions.append(pred)
    
    return np.array(predictions)

def calculate_simple_metrics(y_true, y_pred):
    """Calculate basic evaluation metrics"""
    y_true_flat = y_true.flatten()
    y_pred_flat = y_pred.flatten()
    
    # Remove any NaN or infinite values
    mask = np.isfinite(y_true_flat) & np.isfinite(y_pred_flat)
    y_true_clean = y_true_flat[mask]
    y_pred_clean = y_pred_flat[mask]
    
    if len(y_true_clean) == 0:
        return {'MSE': 0.0, 'MAE': 0.0, 'RMSE': 0.0}
    
    mse = np.mean((y_true_clean - y_pred_clean) ** 2)
    mae = np.mean(np.abs(y_true_clean - y_pred_clean))
    rmse = np.sqrt(mse)
    
    return {'MSE': mse, 'MAE': mae, 'RMSE': rmse}

def main():
    """Run the demo"""
    print("🎯 Stock Price Prediction Demo")
    print("=" * 50)
    
    # Companies to analyze
    companies = {
        'INFY': {'base_price': 1200, 'name': 'Infosys'},
        'TCS': {'base_price': 2300, 'name': 'TCS'},
        'CIPLA': {'base_price': 450, 'name': 'Cipla'}
    }
    
    results = {}
    
    for symbol, info in companies.items():
        print(f"\n📊 Analyzing {info['name']} ({symbol})...")
        
        # Generate demo data
        stock_data = generate_demo_stock_data(
            symbol, 
            n_days=100, 
            base_price=info['base_price']
        )
        
        # Normalize data (simple min-max scaling)
        prices = stock_data['Close'].values
        min_price, max_price = prices.min(), prices.max()
        normalized_prices = (prices - min_price) / (max_price - min_price)
        
        # Create windows
        X, y = create_simple_windows(normalized_prices, window_size=10, prediction_steps=3)
        
        if len(X) < 10:
            print(f"  ❌ Insufficient data for {symbol}")
            continue
        
        # Split data
        split_idx = int(0.7 * len(X))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Train simple model and predict
        predictions = simple_prediction_model(X_train, y_train, X_test)
        
        # Calculate metrics
        metrics = calculate_simple_metrics(y_test, predictions)
        
        # Store results
        results[symbol] = {
            'company': info['name'],
            'metrics': metrics,
            'data_points': len(X),
            'test_samples': len(X_test)
        }
        
        # Print results
        print(f"  ✅ Training completed")
        print(f"     Data points: {len(X)}")
        print(f"     Test samples: {len(X_test)}")
        print(f"     RMSE: {metrics['RMSE']:.6f}")
        print(f"     MAE: {metrics['MAE']:.6f}")
    
    # Summary
    print(f"\n🏆 DEMO RESULTS SUMMARY")
    print("=" * 50)
    
    if results:
        print(f"Companies analyzed: {len(results)}")
        
        # Find best performer
        best_company = min(results.keys(), key=lambda x: results[x]['metrics']['RMSE'])
        best_rmse = results[best_company]['metrics']['RMSE']
        
        print(f"\nPerformance Ranking (by RMSE):")
        sorted_companies = sorted(results.items(), key=lambda x: x[1]['metrics']['RMSE'])
        
        for i, (symbol, data) in enumerate(sorted_companies, 1):
            rmse = data['metrics']['RMSE']
            mae = data['metrics']['MAE']
            print(f"  {i}. {data['company']}: RMSE={rmse:.6f}, MAE={mae:.6f}")
        
        print(f"\n🎯 Best Performance: {results[best_company]['company']} (RMSE: {best_rmse:.6f})")
        
        print(f"\n💡 Demo Features Demonstrated:")
        print(f"  ✅ Multi-company analysis")
        print(f"  ✅ Sliding window approach") 
        print(f"  ✅ Multi-step prediction")
        print(f"  ✅ Performance evaluation")
        print(f"  ✅ Comparative analysis")
        
    print(f"\n🚀 For full CNN implementation, run: stock_price_prediction_complete.py")
    print(f"📓 For Google Colab, use: stock_price_prediction_cnn.ipynb")

if __name__ == "__main__":
    main()