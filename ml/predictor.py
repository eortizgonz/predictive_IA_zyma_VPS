import os
import joblib
import pandas as pd


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "ml",
    "model.pkl"
)


model = joblib.load(MODEL_PATH)



class Predictor:


    def predict(self, machine):


        data = pd.DataFrame([{

            "temperature": machine.temperature,

            "vibration": machine.vibration,

            "current": machine.current,

            "pressure": machine.pressure,

            "rpm": machine.rpm,

            "load": machine.load,

            "operating_hours": machine.operating_hours

        }])


        print("\n----------------------")
        print(machine.machine_id)
        print(data)


        probability = model.predict_proba(data)[0][1]


        print(
            "RIESGO MODELO:",
            probability
        )


        machine.failure_probability = probability * 100


        if probability < 0.30:

            machine.status = "Healthy"

            machine.prediction = "Machine operating normally."


        elif probability < 0.70:

            machine.status = "Warning"

            machine.prediction = "Maintenance recommended."


        else:

            machine.status = "Critical"

            machine.prediction = "High probability of failure."


        return machine