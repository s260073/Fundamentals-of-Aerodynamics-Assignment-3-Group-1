import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve

# -----------------------------
# Fixed design from corrected Task 2
# -----------------------------
N_rotors = 4
N_b = 2
R = 0.53          # updated blade radius [m]

# -----------------------------
# Constants
# -----------------------------
rho = 0.020       # Mars density [kg/m^3]

m_comp = 2.77      # computer/components [kg]
m_batt = 0.5      # original battery pack [kg]

m_cell = 0.047    # extra battery mass [kg]
E_base = 20       # original battery energy [Wh]
E_cell = 10 / 6   # extra battery energy [Wh]

payload_limit = 2  # kg available for extra batteries

# Maximum number of extra batteries
N_extra_max = int(np.floor(payload_limit / m_cell))
N_extra_array = np.arange(0, N_extra_max + 1)

flight_time_min = []
total_mass_list = []
total_power_list = []

guess = (2.0, 100.0)

for N_extra in N_extra_array:

    def equations(vars):
        m_tot, P_tot = vars

        # Payload removed, replaced by extra batteries
        m_no_struct = (
            m_comp
            + N_extra * m_cell
        )

        # Structure = 20% of non-structural mass
        eq1 = 1.2 * m_no_struct - m_tot

        # Hover power model from Task 2
        induced_power = np.sqrt(
            (51.895 * m_tot**3)
            / (2 * N_rotors**2 * rho * np.pi * R**2)
        )
        inner = (51.895 * m_tot**3) / (2 * N_rotors **3* rho * np.pi * R**2)
        induced_power = (np.sqrt(np.abs(inner)) + 178.72 * R**4)*N_rotors # abs prevents invalid sqrt

        profile_power = 178.72 * R**4

        eq2 = induced_power + profile_power - P_tot

        return [eq1, eq2]

    sol = fsolve(equations, guess)
    m_tot, P_tot = sol
    guess = sol

    E_tot = E_base + N_extra * E_cell
    t_flight = 60 * E_tot / P_tot

    total_mass_list.append(m_tot)
    total_power_list.append(P_tot)
    flight_time_min.append(t_flight)

flight_time_min = np.array(flight_time_min)
total_mass_list = np.array(total_mass_list)
total_power_list = np.array(total_power_list)

# Find optimum
idx_best = np.argmax(flight_time_min)

best_N_extra = N_extra_array[idx_best]
best_time = flight_time_min[idx_best]
best_mass = total_mass_list[idx_best]
best_power = total_power_list[idx_best]

print("Maximum allowed batteries:", N_extra_max)
print("Best number of extra batteries:", best_N_extra)
print("Best flight time [min]:", round(best_time, 2))
print("Total mass [kg]:", round(best_mass, 2))
print("Total power [W]:", round(best_power, 2))

# Plot
plt.figure()
plt.plot(N_extra_array, flight_time_min, linewidth=2)
plt.plot(best_N_extra, best_time, "o",
         label=f"Optimum: {best_N_extra} batteries, {best_time:.1f} min")

plt.xlabel("Number of extra batteries")
plt.ylabel("Flight time [min]")
plt.title("Flight time vs number of additional batteries")
plt.grid(True)
plt.legend()
plt.savefig("Assignment3_Task3_updated_flight_time_vs_batteries.png", dpi=300)
plt.show()