import random
from ml.predictor import Predictor
from models.machine import Machine


class SimulatorService:

    def __init__(self):

        self.machines = []

        self.predictor = Predictor()

        self.create_machines()

    # -------------------------------------------------------------
    def create_machines(self):

        self.machines = []


        for i in range(1,21):


            operating_hours = random.randint(
                500,
                9000
            )


            # desgaste inicial según edad

            wear_level = operating_hours / 10000



            machine = Machine(

               machine_id=f"Machine-{i:03}",


               temperature=random.uniform(35,60)
               +
               (wear_level * 20),


               vibration=random.uniform(0.2,0.5)
               +
               (wear_level * 1.5),


               current=random.uniform(10,18)
               +
               (wear_level * 10),


               pressure=random.uniform(5,8),

               rpm=random.randint(1450,1800),


               load=random.uniform(40,70)
               +
               (wear_level * 25),


               operating_hours=operating_hours,


               wear_level=wear_level

             )


            self.machines.append(machine)

    # -------------------------------------------------------------

    def update(self):

        for machine in self.machines:

            # =====================================
            # 1. Envejecimiento de la máquina
            # =====================================

            machine.operating_hours += 1

            # Incremento pequeño de desgaste
            machine.wear_level += 0.00005


            # No permitir desgaste mayor a 100%
            machine.wear_level = min(
                machine.wear_level,
                1.0
            )


            # =====================================
            # 2. Evolución de sensores según desgaste
            # =====================================

            # Vibración aumenta con desgaste
            machine.vibration += (
                machine.wear_level * 0.015
                +
                random.uniform(-0.01, 0.01)
            )


            # Temperatura aumenta con desgaste
            machine.temperature += (
                machine.wear_level * 0.05
                +
                random.uniform(-0.3, 0.3)
            )


            # Corriente del motor aumenta con esfuerzo
            machine.current += (
                machine.wear_level * 0.02
                +
                random.uniform(-0.1, 0.1)
            )


            # Presión con pequeñas variaciones
            machine.pressure += random.uniform(
                -0.1,
                0.1
            )


            # RPM con pequeñas variaciones
            machine.rpm += random.randint(
                -10,
                10
            )


            # Carga variable
            machine.load += random.uniform(
                -1,
                1
            )


            # =====================================
            # 3. Límites físicos
            # =====================================

            machine.temperature = max(
                20,
                min(90, machine.temperature)
            )


            machine.vibration = max(
                0.05,
                min(3, machine.vibration)
            )


            machine.current = max(
                5,
                min(40, machine.current)
            )


            machine.pressure = max(
                2,
                min(12, machine.pressure)
            )


            machine.load = max(
                10,
                min(100, machine.load)
            )


            machine.rpm = max(
                500,
                min(2500, machine.rpm)
            )


            # =====================================
            # 4. Machine Learning Prediction
            # =====================================

            self.predictor.predict(machine)
    # -------------------------------------------------------------

    def get_all(self):

        return [m.to_dict() for m in self.machines]

    #--------------------------------------------------------------
    def get_by_id(self, machine_id: str):
        for machine in self.machines:
            if machine.machine_id == machine_id:
                return machine
        return None