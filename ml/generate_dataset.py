import random
import csv

OUTPUT = "../data/historical_data.csv"

TOTAL = 5000

with open(OUTPUT, "w", newline="") as file:

    writer = csv.writer(file)

    writer.writerow([
        "temperature",
        "vibration",
        "current",
        "pressure",
        "rpm",
        "load",
        "operating_hours",
        "failure"
    ])

    for _ in range(TOTAL):

        temperature = random.uniform(30, 75)

        vibration = random.uniform(0.1, 2.5)

        current = random.uniform(8, 35)

        pressure = random.uniform(5, 10)

        rpm = random.randint(1450, 1800)

        load = random.uniform(35, 100)

        hours = random.randint(100, 9000)

        score = 0

        if temperature > 58:
            score += 1

        if vibration > 1.3:
            score += 1

        if current > 24:
            score += 1

        if load > 82:
            score += 1

        if hours > 6500:
            score += 1

        failure = 1 if score >= 3 else 0

        writer.writerow([
            round(temperature,2),
            round(vibration,2),
            round(current,2),
            round(pressure,2),
            rpm,
            round(load,2),
            hours,
            failure
        ])

print("Dataset generado correctamente.")