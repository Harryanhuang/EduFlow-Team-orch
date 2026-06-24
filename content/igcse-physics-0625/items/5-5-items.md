# Items: 5.5 — Potential divider, thermistor, LDR

### Question Q-5.5-01
**Difficulty**: Foundation
**Question**: How does the resistance of an LDR change as light intensity increases?
**Answer**: The resistance of an LDR decreases as light intensity increases.
**Explanation**: More light gives lower resistance.
**Tags**: LDR, resistance, light-intensity

### Question Q-5.5-02
**Difficulty**: Foundation
**Question**: Give one practical application each for an LDR and a thermistor.
**Answer**: LDR: automatic street lights or camera light meters. Thermistor: digital thermometers, engine temperature sensors, or fire alarms.
**Explanation**: Applications must match the sensor type.
**Tags**: LDR, thermistor, applications

### Question Q-5.5-03
**Difficulty**: Standard
**Question**: A potential divider consists of a 4 kohm resistor and a 6 kohm resistor in series connected to a 10 V supply. Calculate the output voltage across the 6 kohm resistor.
**Answer**: 6 V
**Explanation**: V_out = 10 × 6/(4 + 6) = 6 V. Use the resistor across which the output is taken.
**Tags**: potential-divider, voltage, calculation

### Question Q-5.5-04
**Difficulty**: Standard
**Question**: In a temperature sensor circuit, an NTC thermistor and a fixed resistor are in series. As temperature increases, what happens to the voltage across the fixed resistor? Explain.
**Answer**: The voltage across the fixed resistor increases. The thermistor resistance decreases, so it takes a smaller share of the supply voltage.
**Explanation**: In a series divider, larger resistance gets larger p.d.
**Tags**: thermistor, temperature-sensor, voltage

### Question Q-5.5-05
**Difficulty**: Standard
**Question**: Design a potential divider that outputs 3 V from a 9 V supply using two resistors. Give suitable resistor values.
**Answer**: Use R1 = 2 kohm and R2 = 1 kohm, taking V_out across R2. Then V_out = 9 × 1/(2 + 1) = 3 V.
**Explanation**: The ratio matters more than absolute values.
**Tags**: potential-divider, design, resistor-values

### Question Q-5.5-06
**Difficulty**: Standard
**Question**: An LDR is in series with a fixed resistor. The output is taken across the LDR. What happens to V_out when light intensity increases?
**Answer**: V_out decreases because the LDR resistance decreases and it takes a smaller share of the supply voltage.
**Explanation**: Apply voltage division after remembering the LDR trend.
**Tags**: LDR, potential-divider, output-voltage

### Question Q-5.5-07
**Difficulty**: Challenge
**Question**: A 12 V supply is connected to a 2 kohm resistor in series with an unknown resistor. The output across the unknown resistor is 8 V. Calculate the unknown resistance.
**Answer**: The 2 kohm resistor has 4 V across it. Resistance ratio equals voltage ratio, so R_unknown / 2 kohm = 8/4 = 2. R_unknown = 4 kohm.
**Explanation**: In series, p.d. is proportional to resistance.
**Tags**: potential-divider, unknown-resistance, calculation

### Question Q-5.5-08
**Difficulty**: Challenge
**Question**: A dark-activated lamp needs a higher control voltage in the dark. Explain where the output should be taken in an LDR potential divider.
**Answer**: Take the output across the LDR. In the dark, LDR resistance is high, so it takes a larger share of the supply voltage and V_out is high.
**Explanation**: Sensor placement controls whether output rises or falls.
**Tags**: LDR, dark-activated-switch, circuit-design

### Question Q-5.5-09
**Difficulty**: Challenge
**Question**: Compare an LDR and an NTC thermistor in terms of what they sense and how resistance changes.
**Answer**: An LDR senses light; resistance decreases as light increases. An NTC thermistor senses temperature; resistance decreases as temperature increases. Both can be used in potential divider sensors.
**Explanation**: They sense different quantities but both commonly decrease resistance as the stimulus increases.
**Tags**: LDR, thermistor, comparison, sensors
