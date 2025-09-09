# Stock Price Prediction using CNN-based Sliding Window Model

This project implements a comprehensive stock price prediction system using CNN-based sliding window methodology, based on the approach described in Selvin et al. (2017). The system is designed to predict stock prices for NSE-listed companies with high accuracy using deep learning techniques.

## 🎯 Project Overview

### Objective
Develop a CNN-based sliding window model to predict stock prices for three NSE-listed companies:
- **Infosys (INFY.NS)**
- **TCS (TCS.NS)** 
- **Cipla (CIPLA.NS)**

### Key Features
- ✅ **Multi-step ahead prediction**: Predicts next 10 time steps
- ✅ **CNN-based architecture**: Uses Conv1D layers for temporal feature extraction
- ✅ **Sliding window approach**: 100-minute windows with 90-minute overlap
- ✅ **Comprehensive evaluation**: RMSE, MAE, R², and directional accuracy metrics
- ✅ **Interactive visualizations**: Both static and interactive plots
- ✅ **Google Colab optimized**: Ready for cloud execution
- ✅ **Error handling**: Robust data validation and fallback mechanisms

## 📊 Data Configuration

### Training Data
- **Company**: Infosys (INFY.NS)
- **Period**: July 01, 2014 to October 14, 2014
- **Interval**: Minute-wise (simulated due to historical data limitations)

### Testing Data
- **Companies**: Infosys, TCS, Cipla
- **Period**: October 16, 2014 to November 28, 2014
- **Interval**: Minute-wise (simulated due to historical data limitations)

### Data Preprocessing
- **Feature**: Closing stock price only
- **Normalization**: MinMax scaling (0 to 1 range)
- **Window Configuration**: 
  - Window size: 100 minutes
  - Overlap: 90 minutes
  - Stride: 10 minutes
  - Prediction horizon: 10 minutes

## 🏗️ Model Architecture

### CNN Architecture
```
Input Layer: (100, 1)
├── Conv1D(64, kernel_size=3, activation='relu')
├── MaxPooling1D(pool_size=2)
├── Conv1D(32, kernel_size=3, activation='relu')
├── MaxPooling1D(pool_size=2)
├── Conv1D(16, kernel_size=3, activation='relu')
├── Flatten()
├── Dense(100, activation='relu')
├── Dropout(0.2)
├── Dense(50, activation='relu')
├── Dropout(0.2)
└── Dense(10, activation='linear')  # Output: 10 predictions
```

### Training Configuration
- **Optimizer**: Adam (learning_rate=0.001)
- **Loss Function**: Mean Squared Error (MSE)
- **Metrics**: Mean Absolute Error (MAE)
- **Early Stopping**: Patience=50 epochs
- **Max Epochs**: 1000 (with early stopping)
- **Batch Size**: 32

## 🚀 Getting Started

### Prerequisites
```bash
# Required packages
pip install yfinance pandas numpy matplotlib seaborn scikit-learn tensorflow plotly
```

### Running in Google Colab
1. **Upload the notebook**: `stock_price_prediction_cnn.ipynb`
2. **Run installation cell**: Installs all required packages
3. **Execute cells sequentially**: The notebook is designed for step-by-step execution
4. **View results**: Interactive plots and comprehensive analysis

### Local Execution
1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd MedAssist
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Open Jupyter notebook**:
   ```bash
   jupyter notebook stock_price_prediction_cnn.ipynb
   ```

## 📋 Implementation Modules

### 1. Data Fetching and Preprocessing (`StockDataFetcher`)
- Fetches minute-wise stock data from Yahoo Finance
- Handles API limitations with chunked requests
- Generates realistic simulated data as fallback
- Applies MinMax scaling for normalization

### 2. Sliding Window Creation (`SlidingWindowGenerator`)
- Creates overlapping windows from time series data
- Configurable window size and overlap parameters
- Supports testing different window configurations
- Provides visualization of window structure

### 3. CNN Model Definition (`CNNStockPredictor`)
- Implements CNN architecture with Conv1D layers
- Configurable model parameters
- Early stopping for optimal training
- Comprehensive model summary and statistics

### 4. Evaluation and Metrics (`ModelEvaluator`)
- Calculates multiple evaluation metrics:
  - Root Mean Square Error (RMSE)
  - Mean Absolute Error (MAE)
  - Mean Absolute Percentage Error (MAPE)
  - R-squared (R²) score
  - Directional accuracy
- Compares performance across companies
- Statistical analysis and ranking

### 5. Visualization (`StockPredictionVisualizer`)
- **Static plots**: Comprehensive matplotlib visualizations
- **Interactive plots**: Plotly-based interactive charts
- **Multi-step prediction analysis**: Step-by-step prediction visualization
- **Residual analysis**: Error distribution and patterns
- **Performance comparison**: Cross-company metrics comparison

### 6. Main Execution Pipeline
- **Step 1**: Data loading and preprocessing
- **Step 2**: Sliding window creation
- **Step 3**: Model building and training
- **Step 4**: Testing and evaluation
- **Step 5**: Comprehensive visualization
- **Step 6**: Window size optimization (optional)

## 📈 Expected Results

### Performance Metrics
The model provides detailed evaluation for each company:
- **RMSE**: Root Mean Square Error (lower is better)
- **MAE**: Mean Absolute Error (lower is better)
- **MAPE**: Mean Absolute Percentage Error (lower is better)
- **R² Score**: Coefficient of determination (higher is better)
- **Directional Accuracy**: Trend prediction accuracy (higher is better)

### Visualizations
1. **Time Series Plot**: Actual vs predicted prices
2. **Scatter Plot**: Predicted vs actual correlation
3. **Residual Analysis**: Error patterns and distribution
4. **Multi-step Predictions**: Individual prediction sequences
5. **Interactive Charts**: Zoomable, interactive time series
6. **Performance Comparison**: Cross-company metrics

## 🛠️ Customization Options

### Adjustable Parameters
```python
# Window configuration
window_size = 100          # Input sequence length
overlap = 90              # Overlap between windows
prediction_steps = 10     # Number of future steps to predict

# Model architecture
filters = [64, 32, 16]    # Conv1D filter sizes
dense_units = [100, 50]   # Dense layer sizes
dropout_rate = 0.2        # Dropout rate

# Training parameters
epochs = 1000             # Maximum training epochs
batch_size = 32          # Training batch size
learning_rate = 0.001    # Adam optimizer learning rate
```

### Window Size Optimization
The notebook includes functionality to test different window sizes:
```python
window_sizes = [50, 75, 100, 125, 150]
results = window_generator.test_different_window_sizes(data, window_sizes)
```

## ⚠️ Important Notes

### Data Limitations
- **Historical minute data**: Yahoo Finance has limited historical minute-level data
- **Simulated data**: The notebook uses realistic simulated data for demonstration
- **Real implementation**: For production use, integrate with real-time data sources

### Google Colab Optimization
- **Reduced epochs**: Training limited to 200 epochs for faster execution
- **GPU support**: Automatically detects and uses GPU if available
- **Memory management**: Optimized for Colab's resource limitations

### Error Handling
- **Data validation**: Checks for sufficient data before processing
- **Graceful fallbacks**: Uses simulated data when real data unavailable
- **Progress indicators**: Clear feedback during long-running operations

## 📚 References

1. **Selvin, S., Vinayakumar, R., Gopalakrishnan, E. A., Menon, V. K., & Soman, K. P. (2017)**. Stock price prediction using LSTM, RNN and CNN-sliding window model. *2017 international conference on advances in computing, communications and informatics (icacci)* (pp. 1643-1647). IEEE.

2. **Yahoo Finance API**: Used for stock data retrieval
3. **TensorFlow/Keras**: Deep learning framework
4. **Plotly**: Interactive visualization library

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature-name`
3. **Commit changes**: `git commit -am 'Add feature'`
4. **Push to branch**: `git push origin feature-name`
5. **Submit pull request**

## 📄 License

This project is part of the MedAssist repository. Please refer to the main repository license.

## 🆘 Support

For issues and questions:
1. **Check the documentation** in the notebook cells
2. **Review error messages** - most include helpful suggestions
3. **Open an issue** in the repository for bugs or enhancements

---

**Note**: This implementation is designed for educational and research purposes. For production trading systems, additional considerations for risk management, real-time data integration, and regulatory compliance are necessary.