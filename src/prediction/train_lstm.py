from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.common.config import load_config

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "PyTorch is not installed. Install it first, then rerun: pip install torch"
    ) from exc


class DemandLSTM(nn.Module):
    def __init__(self, input_size: int, hidden_size: int, num_layers: int) -> None:
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
        )
        self.head = nn.Linear(hidden_size, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.lstm(x)
        out = out[:, -1, :]
        return self.head(out)


def build_sequences(
    df: pd.DataFrame,
    time_column: str,
    zone_column: str,
    feature_columns: list[str],
    target_column: str,
    seq_len: int,
) -> tuple[np.ndarray, np.ndarray, list[dict[str, str]]]:
    xs: list[np.ndarray] = []
    ys: list[float] = []
    meta: list[dict[str, str]] = []

    for _, zone_df in df.groupby(zone_column):
        zone_df = zone_df.sort_values(time_column).reset_index(drop=True)
        if len(zone_df) <= seq_len:
            continue

        values = zone_df[feature_columns].to_numpy(dtype=np.float32)
        targets = zone_df[target_column].to_numpy(dtype=np.float32)

        for idx in range(seq_len, len(zone_df)):
            xs.append(values[idx - seq_len : idx])
            ys.append(targets[idx])
            meta.append(
                {
                    time_column: str(zone_df.loc[idx, time_column]),
                    zone_column: str(zone_df.loc[idx, zone_column]),
                }
            )

    return np.array(xs, dtype=np.float32), np.array(ys, dtype=np.float32), meta


def standardize(
    x_train: np.ndarray, x_test: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    mean = x_train.mean(axis=(0, 1), keepdims=True)
    std = x_train.std(axis=(0, 1), keepdims=True)
    std = np.where(std == 0, 1.0, std)
    return (x_train - mean) / std, (x_test - mean) / std, mean, std


def main() -> None:
    cfg = load_config()
    processed_csv = Path(cfg["data"]["processed_csv"])
    time_column = cfg["data"]["time_column"]
    zone_column = cfg["data"]["zone_column"]
    target_column = cfg["data"]["demand_column"]
    test_size = cfg["model"]["test_size"]
    lstm_cfg = cfg["lstm"]

    df = pd.read_csv(processed_csv).dropna().copy().sort_values(time_column).reset_index(drop=True)
    feature_columns = [
        "available_taxis",
        "hour",
        "day_of_week",
        "lag_1",
        "rolling_mean_3",
    ]

    x, y, meta = build_sequences(
        df=df,
        time_column=time_column,
        zone_column=zone_column,
        feature_columns=feature_columns,
        target_column=target_column,
        seq_len=lstm_cfg["seq_len"],
    )

    split_idx = int(len(x) * (1 - test_size))
    x_train, x_test = x[:split_idx], x[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    meta_test = meta[split_idx:]

    x_train, x_test, _, _ = standardize(x_train, x_test)

    train_loader = DataLoader(
        TensorDataset(torch.tensor(x_train), torch.tensor(y_train).unsqueeze(-1)),
        batch_size=lstm_cfg["batch_size"],
        shuffle=True,
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = DemandLSTM(
        input_size=len(feature_columns),
        hidden_size=lstm_cfg["hidden_size"],
        num_layers=lstm_cfg["num_layers"],
    ).to(device)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lstm_cfg["learning_rate"])

    for _ in range(lstm_cfg["epochs"]):
        model.train()
        for xb, yb in train_loader:
            xb = xb.to(device)
            yb = yb.to(device)
            optimizer.zero_grad()
            pred = model(xb)
            loss = criterion(pred, yb)
            loss.backward()
            optimizer.step()

    model.eval()
    with torch.no_grad():
        test_pred = model(torch.tensor(x_test).to(device)).cpu().numpy().reshape(-1)

    rmse = float(np.sqrt(np.mean((test_pred - y_test) ** 2)))
    mae = float(np.mean(np.abs(test_pred - y_test)))

    metrics_output = Path(lstm_cfg["metrics_output"])
    predictions_output = Path(lstm_cfg["predictions_output"])
    metrics_output.parent.mkdir(parents=True, exist_ok=True)

    metrics_output.write_text(
        json.dumps(
            {
                "model": "lstm",
                "device": str(device),
                "train_sequences": int(len(x_train)),
                "test_sequences": int(len(x_test)),
                "seq_len": int(lstm_cfg["seq_len"]),
                "features": feature_columns,
                "rmse": round(rmse, 4),
                "mae": round(mae, 4),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    pred_df = pd.DataFrame(meta_test)
    pred_df["actual_call_count"] = y_test
    pred_df["predicted_call_count"] = test_pred
    pred_df.to_csv(predictions_output, index=False)

    print("lstm rmse:", round(rmse, 4))
    print("lstm mae:", round(mae, 4))
    print(f"saved: {metrics_output}")
    print(f"saved: {predictions_output}")


if __name__ == "__main__":
    main()
