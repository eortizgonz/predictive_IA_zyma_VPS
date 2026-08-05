from services.simulator_service import SimulatorService


sim = SimulatorService()


for machine in sim.machines:

    print(
        machine.machine_id,
        "| Temp:",
        machine.temperature,
        "| Vib:",
        machine.vibration,
        "| Current:",
        machine.current,
        "| Load:",
        machine.load,
        "| Hours:",
        machine.operating_hours
    )