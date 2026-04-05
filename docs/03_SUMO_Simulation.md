# SUMO Traffic Simulation Guide: A-Eye

This project uses **SUMO (Simulation of Urban MObility)** as the industrial-standard traffic simulator to validate taxi demand and dispatch predictions.

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
- `demand.rou.xml`: **(Generated)** The route file containing vehicles spawned based on ConvLSTM predictions.

---

## 🔄 Dynamic Export from Pipeline

The prediction pipeline automatically generates the `demand.rou.xml` file.

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
3.  Observe the yellow taxis spawning according to the predicted demand levels.

---

## 🔬 How it Works

The `src.dispatch.export_to_sumo` script:
1. Calculates the total predicted demand across the 3x3 grid.
2. Generates a list of vehicle departures (`<vehicle>`) in the route file.
3. Maps predicted volumes to traffic density in the 3x3 road network.
