# Evaluation query reference

The evaluation contains 18 answerable queries and 6 no-answer traps. Exact labeled
spans and rejected distractors remain in [`eval/queries.yaml`](../eval/queries.yaml).

## Answerable: direct

1. `officer orders the driver to step out of the vehicle`
2. `officer threatens to take someone to jail`
3. `officer explains the bail amount and court date`
4. `officers discuss finding a driver asleep at a traffic light`
5. `an officer reads someone their Miranda rights`
6. `an officer asks about drugs or alcohol`
7. `a breathalyzer test is discussed or given`
8. `an ambulance or medics are called to the scene`
9. `a vehicle is towed or impounded`

## Answerable: cross-modal

1. `a field sobriety test is conducted`
2. `a person is being handcuffed`
3. `a vehicle stopped by police at night`
4. `firefighters respond to a vehicle fire at night`
5. `an officer conducts a traffic stop in daylight`
6. `officers pursue someone on foot`
7. `someone is placed in the back of a patrol car`
8. `a weapon is found or discussed`
9. `a car crash or collision scene`

## No-answer traps

The correct result for each query is no confident match.

1. `a gunshot is fired`
2. `a police K-9 searches a vehicle`
3. `an officer deploys a taser`
4. `a house is on fire`
5. `an officer performs CPR`
6. `a school bus is visible`
