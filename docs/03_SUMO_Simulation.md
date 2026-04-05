# SUMO Traffic Simulation Guide: A-Eye

This project uses **SUMO (Simulation of Urban MObility)** as a simulation bridge for the grid-based prediction experiment.
At the current stage, SUMO export is connected, but the route mapping is still a coarse demo rather than a fully realistic traffic model.

## 🛠️ Prerequisites

1.  **Install SUMO**:
    ```bash
    brew install sumo
    ```
2.  **Verify installation**:
    ```bash
    sumo --version
    ```

---

## 🚦 Grid 3x3 Simulation Environment

The simulation environment is located in `module1_sumo/`. It consists of:

- `grid3x3.net.xml`: A 3x3 grid road network with 9 junctions.
- `sumo_config.sumocfg`: The master configuration file.
- `demand.rou.xml`: **(Generated)** The route file containing vehicles spawned from ConvLSTM prediction volume.

---

## 🔄 Dynamic Export from Pipeline

The public pipeline automatically generates the `demand.rou.xml` file.

```bash
# Run the pipeline to regenerate SUMO demand
bash scripts/run_public_pipeline.sh
```

- Input: `outputs/seoul_public/convlstm_predictions.csv`
- Output: `module1_sumo/demand.rou.xml`

---

## ▶️ Running the Simulation

To launch the simulation with the GUI:

```bash
cd module1_sumo
sumo-gui -c sumo_config.sumocfg
```

1.  Open the GUI.
2.  Press **Play** (or select "Start" in the menu).
3.  Observe the yellow taxis spawning according to the predicted demand volume.

---

## 🔬 How it Works

The `src.dispatch.export_to_sumo` script currently:
1. Reads the ConvLSTM prediction output.
2. Converts the summed predicted demand into a set of vehicle departures.
3. Writes a valid SUMO route file for the 3x3 network.

## Current Limitation

- The export is not yet doing realistic cell-by-cell routing.
- Most vehicles are still assigned to a small static route set.
- This should be treated as a simulation connectivity check, not a final traffic validation layer.
