import numpy as np
import scipy as scp
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from scipy.optimize import fsolve

r_tested = np.linspace(0.2,1,50)
m_comp = 1
m_batt = .5
m_payload = 2
m_const = m_comp + m_batt + m_payload
N_b = 2
rho = 0.020
N_rotors_tested = [2,4,]
N_b_tested = [2]



j = 0
for N_rotors in N_rotors_tested:
    output = np.zeros((len(r_tested),2))
    i = 0
    guess = (1,100)
    for N_b in N_b_tested:
        i = 0
        for r in r_tested:
            def equations(vars):
                m_tot, P_tot = vars
                eq1 = 1.2 * (m_const + 29.* 0.001 * r * N_b*N_rotors + 2.5 * 0.001 * P_tot) - m_tot
                
                inner = (51.895 * m_tot**3) / (2 * N_rotors **3* rho * np.pi * r**2)
                eq2 = (np.sqrt(np.abs(inner)) + 178.72 * r**4)*N_rotors - P_tot  # abs prevents invalid sqrt
                
                return [eq1, eq2]
            
            sol = fsolve(equations,guess, full_output=True)
            x, info, ier, msg = sol
            output[i] = x
            guess = x
            i+=1
        

        mindex = np.argmin(output[:,1])
        plt.plot(r_tested,output[:,1], 
                color = list(mcolors.TABLEAU_COLORS)[j],
                alpha = 2/N_b)
        plt.plot(r_tested[mindex],
                output[mindex,1], 
                marker = 'o', 
                alpha = 2/N_b,
                color = list(mcolors.TABLEAU_COLORS)[j],
                #label = str(N_rotors) + " Rotors, ")
                label = str(N_rotors) + " Rotors, "+ str(N_b) +"Blades, Minimum at P = " + str(round(output[mindex,1],1)) + "W, r = "+str(round(r_tested[mindex],2)) + "m, m_tot = " + str(round(output[mindex,0],1)) + "kg")
        j +=1

plt.xlabel("Blade Radius (m)")
plt.ylabel("Power (Watts)")
plt.legend()
plt.grid()
plt.show()
