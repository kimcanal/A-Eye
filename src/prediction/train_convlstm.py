from __future__ import annotations

import json
from pathlib import Path
import math

import numpy as np
import pandas as pd

from src.common.config import load_config

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset


class ConvLSTMCell(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, kernel_size: int, bias: bool = True):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.kernel_size = kernel_size
        self.padding = kernel_size // 2
        self.bias = bias
        
        self.conv = nn.Conv2d(
            in_channels=self.input_dim + self.hidden_dim,
            out_channels=4 * self.hidden_dim,
            kernel_size=self.kernel_size,
            padding=self.padding,
            bias=self.bias
        )

    def forward(self, input_tensor, cur_state):
        h_cur, c_cur = cur_state
        
        # Concatenate along channel axis
        combined = torch.cat([input_tensor, h_cur], dim=1)
        combined_conv = self.conv(combined)
        
        cc_i, cc_f, cc_o, cc_g = torch.split(combined_conv, self.hidden_dim, dim=1)
        
        i = torch.sigmoid(cc_i)
        f = torch.sigmoid(cc_f)
        o = torch.sigmoid(cc_o)
        g = torch.tanh(cc_g)
        
        c_next = f * c_cur + i * g
        h_next = o * torch.tanh(c_next)
        
        return h_next, c_next

    def init_hidden(self, batch_size: int, image_size: tuple):
        height, width = image_size
        return (torch.zeros(batch_size, self.hidden_dim, height, width, device=self.conv.weight.device),
                torch.zeros(batch_size, self.hidden_dim, height, width, device=self.conv.weight.device))


class ConvLSTM(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, kernel_size: int):
        super().__init__()
        self.cell = ConvLSTMCell(input_dim=input_dim, hidden_dim=hidden_dim, kernel_size=kernel_size)
        self.conv_out = nn.Conv2d(in_channels=hidden_dim, out_channels=1, kernel_size=1)

    def forward(self, x):
        # x shape: (B, Seq_Len, C, H, W)
        b, seq_len, _, h, w = x.shape
        h_t, c_t = self.cell.init_hidden(batch_size=b, image_size=(h, w))
        
        for t in range(seq_len):
            h_t, c_t = self.cell(x[:, t, :, :, :], (h_t, c_t))
            
        # We only care about the last output to predict the next step
        output = self.conv_out(h_t) # Shape (B, 1, H, W)
        return output


def build_grid_sequences(
    df: pd.DataFrame,
    time_column: str,
    feature_columns: list[str],
    target_column: str,
    seq_len: int,
    grid_w: int,
    grid_h: int
) -> tuple[np.ndarray, np.ndarray]:
    """
    Reformats tabular grid data into (Time, Channel, H, W) and generates sequences.
    """
    times = sorted(df[time_column].unique())
    num_times = len(times)
    num_features = len(feature_columns)
    
    # Pre-allocate full spatial tensor
    spatial_data = np.zeros((num_times, num_features, grid_h, grid_w), dtype=np.float32)
    spatial_target = np.zeros((num_times, 1, grid_h, grid_w), dtype=np.float32)
    
    # We will build a mapping of time to index
    time_to_idx = {t: i for i, t in enumerate(times)}
    
    for _, row in df.iterrows():
        t_idx = time_to_idx[row[time_column]]
        x = int(row['grid_x'])
        y = int(row['grid_y'])
        
        for c_idx, col in enumerate(feature_columns):
            spatial_data[t_idx, c_idx, y, x] = row[col]
            
        spatial_target[t_idx, 0, y, x] = row[target_column]
        
    xs, ys = [], []
    for i in range(seq_len, num_times):
        xs.append(spatial_data[i - seq_len : i])
        ys.append(spatial_target[i])
        
    return np.array(xs, dtype=np.float32), np.array(ys, dtype=np.float32)


def standardize(
    x_train: np.ndarray, x_test: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    # Compute mean/std over exactly B, Seq, H, W to keep Channel isolated
    mean = x_train.mean(axis=(0, 1, 3, 4), keepdims=True)
    std = x_train.std(axis=(0, 1, 3, 4), keepdims=True)
    std = np.where(std == 0, 1.0, std)
    return (x_train - mean) / std, (x_test - mean) / std


def main() -> None:
    cfg = load_config()
    grid_csv = Path(cfg['grid']['output_csv'])
    time_column = cfg['data']['time_column']
    target_column = cfg['data']['demand_column']
    test_size = cfg['model']['test_size']
    
    cv_cfg = cfg['convlstm']
    
    print(f"Loading grid data from {grid_csv}...")
    df = pd.read_csv(grid_csv)
    
    feature_columns = [
        "call_count",
        "available_taxis",
        "is_holiday",
        "temperature",
        "precipitation"
    ]
    
    grid_w = cfg['grid']['width']
    grid_h = cfg['grid']['height']
    
    X, Y = build_grid_sequences(
        df=df,
        time_column=time_column,
        feature_columns=feature_columns,
        target_column=target_column,
        seq_len=cv_cfg["seq_len"],
        grid_w=grid_w,
        grid_h=grid_h
    )
    
    split_idx = int(len(X) * (1 - test_size))
    x_train, x_test = X[:split_idx], X[split_idx:]
    y_train, y_test = Y[:split_idx], Y[split_idx:]
    
    x_train, x_test = standardize(x_train, x_test)
    
    train_loader = DataLoader(
        TensorDataset(torch.tensor(x_train), torch.tensor(y_train)),
        batch_size=cv_cfg["batch_size"],
        shuffle=True,
    )
    
    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Training ConvLSTM on device: {device}")
    
    model = ConvLSTM(
        input_dim=len(feature_columns),
        hidden_dim=cv_cfg["hidden_dim"],
        kernel_size=cv_cfg["kernel_size"]
    ).to(device)
    
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=cv_cfg["learning_rate"])
    
    for epoch in range(cv_cfg["epochs"]):
        model.train()
        total_loss = 0
        for xb, yb in train_loader:
            xb = xb.to(device)
            yb = yb.to(device)
            
            optimizer.zero_grad()
            pred = model(xb)
            loss = criterion(pred, yb)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            
        if (epoch + 1) % 10 == 0 or epoch == 0:
            print(f"Epoch {epoch+1}/{cv_cfg['epochs']} | Loss: {total_loss/len(train_loader):.4f}")
            
    model.eval()
    with torch.no_grad():
        test_pred = model(torch.tensor(x_test).to(device)).cpu().numpy()
        
    rmse = float(np.sqrt(np.mean((test_pred - y_test) ** 2)))
    mae = float(np.mean(np.abs(test_pred - y_test)))
    
    # Safe MAPE avoiding division by zero
    y_test_safe = np.where(y_test == 0, 1e-6, y_test)
    mape = float(np.mean(np.abs((test_pred - y_test) / y_test_safe)) * 100)
    
    metrics_output = Path(cv_cfg["metrics_output"])
    predictions_output = Path(cv_cfg["predictions_output"])
    metrics_output.parent.mkdir(parents=True, exist_ok=True)
    
    metrics = {
        "model": "convlstm",
        "device": str(device),
        "train_sequences": int(len(x_train)),
        "test_sequences": int(len(x_test)),
        "seq_len": int(cv_cfg["seq_len"]),
        "features": feature_columns,
        "grid_size": f"{grid_w}x{grid_h}",
        "rmse": round(rmse, 4),
        "mae": round(mae, 4),
        "mape": round(mape, 4),
    }
    
    metrics_output.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    
    # Save flattened predictions
    flat_test = test_pred.flatten()
    flat_actual = y_test.flatten()
    pred_df = pd.DataFrame({
        "actual_call_count": flat_actual,
        "predicted_call_count": flat_test
    })
    pred_df.to_csv(predictions_output, index=False)
    
    print("\n--- ConvLSTM Evaluation ---")
    print("rmse:", round(rmse, 4))
    print("mae:", round(mae, 4))
    print("mape:", round(mape, 4), "%")
    print(f"saved: {metrics_output}")
    print(f"saved: {predictions_output}")


if __name__ == "__main__":
    main()
