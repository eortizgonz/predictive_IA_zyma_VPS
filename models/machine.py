from dataclasses import dataclass, asdict


@dataclass

class Machine:


    def __init__(
        self,
        machine_id,
        temperature,
        vibration,
        current,
        pressure,
        rpm,
        load,
        operating_hours,
        wear_level=0.0
    ):


        self.machine_id = machine_id

        self.temperature = temperature

        self.vibration = vibration

        self.current = current

        self.pressure = pressure

        self.rpm = rpm

        self.load = load

        self.operating_hours = operating_hours

        self.wear_level = wear_level


        # Datos ML

        self.failure_probability = 0

        self.status = "Unknown"

        self.prediction = ""



    def to_dict(self):

        return {

            "machine_id": self.machine_id,

            "temperature": round(self.temperature,2),

            "vibration": round(self.vibration,2),

            "current": round(self.current,2),

            "pressure": round(self.pressure,2),

            "rpm": self.rpm,

            "load": round(self.load,2),

            "operating_hours": self.operating_hours,

            "wear_level": round(self.wear_level * 100,2),

            "failure_probability": round(
                self.failure_probability,
                2
            ),

            "status": self.status,

            "prediction": self.prediction
        }