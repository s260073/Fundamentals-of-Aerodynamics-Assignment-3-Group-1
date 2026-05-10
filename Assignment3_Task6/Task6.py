"""
Task 6 - Forward flight with optional wing (Mars drone).

Design from Tasks 2 & 5:
  Quadcopter: N_rotors=4, R=0.53 m, N_b=2, m_tot=4.6 kg, Omega=293.2 rad/s

Wing aerodynamics use Prandtl's Lifting Line Theory (LLT) to compute the
Oswald efficiency e from first principles for any (AR, taper ratio lam,
washout theta_tip).

Three deliverables:
  1. Wing shape optimisation: e vs lam/theta_tip, power vs wingspan, mass vs wingspan
  2. 10% power reduction feasibility at rho_wing=74 kg/m^3; required density if not
  3. Total power and rotor tilt angle vs flight speed (0-12 m/s) for final design
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize_scalar
from scipy.interpolate import interp1d

plt.rcParams.update({"font.size": 12, "axes.grid": True, "grid.alpha": 0.35,
                     "figure.dpi": 130})

# =============================================================================
# CONSTANTS
# =============================================================================

rho      = 0.020        # kg/m^3  Mars air density
g        = 3.73         # m/s^2   Mars gravity

N_rotors = 4
R        = 0.53         # m  rotor radius
N_b      = 2            # blades per rotor
Omega    = 293.2        # rad/s  (2800 rpm)
c_bar    = 0.14167 / N_b   # mean chord = 0.0708 m
kappa    = 1.15         # induced power correction
Cd0_rot  = 0.02         # blade profile drag coefficient

m_base   = 4.6          # kg  total mass incl. 2 kg payload
A_rot    = np.pi * R**2

V_design = 10.0         # m/s  forward speed

A_body   = 0.018        # m^2  fuselage frontal area
CD_body  = 0.4

rho_wing = 74.0         # kg/m^3  carbon fibre + foam (from assignment)
tau      = 0.05         # t/c for ROAMX-0201 (from Ingenuity geometry)
k_shape  = 0.55         # airfoil section area factor: A_sec = k_shape*tau*c^2

# =============================================================================
# ROAMX-0201 AIRFOIL POLAR  (from blade_data.csv, Task 5)
# =============================================================================

_alpha_data = np.array([-2.0,  0.0,  2.0,  2.5,  3.0,  3.5,
                          4.0,  4.5,  5.0,  5.5,  6.0])
_Cl_data    = np.array([-0.0081, 0.1725, 0.3869, 0.4299, 0.4781, 0.5229,
                          0.5679, 0.6376, 0.7337, 0.7999, 0.8606])
_Cd_data    = np.array([ 0.0565, 0.0464, 0.0439, 0.0456, 0.0475, 0.0499,
                          0.0525, 0.0544, 0.0602, 0.0667, 0.0744])

_Cd_of_Cl = interp1d(_Cl_data, _Cd_data,
                     bounds_error=False,
                     fill_value=(_Cd_data[0], _Cd_data[-1]))

CL_max = 0.86
CL_min = 0.0

# Linear fit over the attached (pre-stall) range for LLT
_lin_mask            = _alpha_data <= 4.0
_slope, _intercept   = np.polyfit(_alpha_data[_lin_mask], _Cl_data[_lin_mask], 1)
a0_per_rad           = _slope * (180.0 / np.pi)   # 2-D lift slope [1/rad]
alpha_L0_deg         = -_intercept / _slope        # zero-lift angle [deg]
print(f"ROAMX-0201 linear fit: a0 = {a0_per_rad:.3f} /rad,  "
      f"alpha_L0 = {alpha_L0_deg:.2f} deg")

# =============================================================================
# PRANDTL LIFTING LINE THEORY  (same matrix formulation as Assignment 2)
# =============================================================================

def solve_llt(AR, lam, theta_tip_deg, alpha_root_deg=4.0, N=50):
    """
    Solve Prandtl LLT for a linearly tapered, linearly twisted wing.

    Parameters
    ----------
    AR             : aspect ratio
    lam            : taper ratio  c_tip / c_root
    theta_tip_deg  : geometric washout at tip relative to root [deg]
                     (negative = washout, reduces tip angle of attack)
    alpha_root_deg : root geometric angle of attack [deg]  (sets CL level)
    N              : number of Fourier terms / collocation points

    Returns
    -------
    dict: e, CL, CDi, A (Fourier coefficients), y_norm (2y/b),
          cl_local, alpha_i_deg, c_norm
    """
    b     = 1.0                                   # normalised span
    S     = b**2 / AR
    c_r   = 2.0 * S / (b * (1.0 + lam))          # root chord

    # Collocation points in theta space  (theta=0: right tip, theta=pi: left tip)
    theta      = np.arange(1, N + 1) * np.pi / (N + 1)
    y_abs_norm = np.abs(np.cos(theta))            # |2y/b|, =1 at tips, =0 at root

    # Chord and geometric angle of attack at each collocation point
    c          = c_r * (1.0 - (1.0 - lam) * y_abs_norm)
    alpha_geom = alpha_root_deg + theta_tip_deg * y_abs_norm   # [deg]

    rhs = np.radians(alpha_geom - alpha_L0_deg)

    # Build LLT matrix  M * A = rhs
    n_arr = np.arange(1, N + 1)
    M     = np.zeros((N, N))
    for j, th in enumerate(theta):
        M[j, :] = ((4.0 * b / (a0_per_rad * c[j])) * np.sin(n_arr * th)
                   + n_arr * np.sin(n_arr * th) / np.sin(th))

    A = np.linalg.solve(M, rhs)

    # Global aerodynamic coefficients
    CL  = np.pi * AR * A[0]
    CDi = np.pi * AR * np.dot(n_arr, A**2)
    e   = A[0]**2 / np.dot(n_arr, A**2)

    # Spanwise distributions (for plotting)
    gamma_tilde = np.zeros(N)
    alpha_i_rad = np.zeros(N)
    for n in range(1, N + 1):
        gamma_tilde += A[n - 1] * np.sin(n * theta)
        alpha_i_rad += n * A[n - 1] * np.sin(n * theta) / np.sin(theta)

    alpha_eff_deg = alpha_geom - np.degrees(alpha_i_rad)
    cl_local = np.interp(alpha_eff_deg, _alpha_data, _Cl_data,
                         left=_Cl_data[0], right=_Cl_data[-1])

    return {
        'e':           e,
        'CL':          CL,
        'CDi':         CDi,
        'A':           A,
        'y_norm':      np.cos(theta),      # 2y/b: +1 = right tip, -1 = left tip
        'cl_local':    cl_local,
        'alpha_i_deg': np.degrees(alpha_i_rad),
        'c_norm':      c / c_r,            # c(y)/c_root
        'gamma_tilde': gamma_tilde,
    }

# =============================================================================
# WING SHAPE OPTIMISATION  -  sweep lam and theta_tip, find max e per AR
# =============================================================================

AR_arr        = [5, 7, 9]
lam_sweep     = np.array([0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1.0])
theta_tip_arr = [0.0, -1.0, -2.0, -3.0, -4.0]   # deg (washout)

print("\n--- LLT wing shape optimisation ---")

shape_e = {AR: np.full((len(lam_sweep), len(theta_tip_arr)), np.nan)
           for AR in AR_arr}

for AR in AR_arr:
    for i, lam in enumerate(lam_sweep):
        for j, th in enumerate(theta_tip_arr):
            try:
                shape_e[AR][i, j] = solve_llt(AR, lam, th)['e']
            except np.linalg.LinAlgError:
                pass

# Optimal (lam, theta_tip) per AR
shape_opt = {}
for AR in AR_arr:
    idx       = np.nanargmax(shape_e[AR])
    i_opt, j_opt = np.unravel_index(idx, shape_e[AR].shape)
    lam_opt   = lam_sweep[i_opt]
    tip_opt   = theta_tip_arr[j_opt]
    e_opt     = shape_e[AR][i_opt, j_opt]
    llt_opt   = solve_llt(AR, lam_opt, tip_opt)
    shape_opt[AR] = {'lam': lam_opt, 'theta_tip': tip_opt,
                     'e': e_opt, 'llt': llt_opt}
    print(f"  AR={AR}: lam*={lam_opt:.1f}  theta_tip*={tip_opt:.0f} deg  "
          f"e={e_opt:.4f}  CL={llt_opt['CL']:.3f}")

# --- Figure 1: Oswald efficiency vs taper ratio ---
colors_tip = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple']
fig1, axes1 = plt.subplots(1, 3, figsize=(13, 4), sharey=True)
for ax, AR in zip(axes1, AR_arr):
    for j, th in enumerate(theta_tip_arr):
        ax.plot(lam_sweep, shape_e[AR][:, j],
                color=colors_tip[j], lw=2,
                label=rf'$\theta_{{tip}}={th:.0f}^\circ$')
    opt = shape_opt[AR]
    ax.plot(opt['lam'], opt['e'], 'k*', ms=13, zorder=5,
            label=rf"Opt. $\lambda={opt['lam']:.1f}$, "
                  rf"$\theta_{{tip}}={opt['theta_tip']:.0f}^\circ$")
    ax.set_xlabel(r'Taper ratio $\lambda$')
    ax.set_title(f'AR = {AR}')
    ax.legend(fontsize=7.5)
axes1[0].set_ylabel('Oswald efficiency  $e$')
fig1.suptitle('LLT Oswald efficiency (ROAMX-0201, $\\alpha_r = 4^\\circ$)')
plt.tight_layout()
plt.savefig('task6_llt_oswald.png', dpi=150)
plt.show()
print("Saved: task6_llt_oswald.png")

# --- Figure 2: Spanwise CL distribution for optimal wing at each AR ---
colors_AR = ['tab:blue', 'tab:orange', 'tab:green']
fig2, ax2 = plt.subplots(figsize=(8, 5))
for AR, col in zip(AR_arr, colors_AR):
    llt = shape_opt[AR]['llt']
    y   = llt['y_norm']                  # 2y/b, right half (+1 tip, 0 root)
    cl  = llt['cl_local']
    # Mirror to full span (symmetric)
    y_full  = np.concatenate([-np.sort(-y), np.sort(y)])
    cl_full = np.concatenate([cl[np.argsort(-y)], cl[np.argsort(y)]])
    opt = shape_opt[AR]
    ax2.plot(y_full, cl_full, color=col, lw=2,
             label=(f"AR={AR}, $\\lambda={opt['lam']:.1f}$, "
                    f"$\\theta_{{tip}}={opt['theta_tip']:.0f}^\\circ$, "
                    f"$e={opt['e']:.3f}$"))

# Elliptic reference: cl_local = const (uniform)
ref_cl = shape_opt[AR_arr[1]]['llt']['CL']
ax2.axhline(ref_cl, color='k', ls='--', lw=1.2, label='Ideal elliptic (uniform $c_l$)')
ax2.set_xlabel(r'Normalised span  $2y/b$')
ax2.set_ylabel(r'Local lift coefficient  $c_l(y)$')
ax2.set_title('Spanwise lift distribution (optimal planform per AR)')
ax2.legend(fontsize=9)
plt.tight_layout()
plt.savefig('task6_llt_cl_dist.png', dpi=150)
plt.show()
print("Saved: task6_llt_cl_dist.png")

# =============================================================================
# AERODYNAMIC UTILITIES  (rotor + wing power model)
# =============================================================================

def wing_CD(CL, AR, e):
    """Finite-wing drag: profile (from ROAMX-0201 polar) + LLT induced drag."""
    Cd0_w = float(_Cd_of_Cl(CL))
    return Cd0_w + CL**2 / (np.pi * AR * e)


def wing_mass(b, AR, lam):
    """Wing structural mass via analytical volume integral (tapered planform)."""
    if b < 1e-6:
        return 0.0
    c_r      = 2.0 * b / (AR * (1.0 + lam))
    k_taper  = 2.0 * (1.0 - lam) / b
    half     = b / 2.0
    integ    = half - k_taper * half**2 + (k_taper**2 * half**3) / 3.0
    V_wing   = 2.0 * k_shape * tau * c_r**2 * integ
    return rho_wing * V_wing


def induced_velocity(T_per, V, beta, n_iter=300):
    """Glauert iterative induced velocity (Lecture 12)."""
    v_H = np.sqrt(max(T_per, 1e-9) / (2.0 * rho * A_rot))
    v_i = v_H
    Vx, Vz = V * np.cos(beta), V * np.sin(beta)
    for _ in range(n_iter):
        v_new  = v_H**2 / np.sqrt(Vx**2 + (Vz + v_i)**2 + 1e-30)
        v_next = 0.6 * v_i + 0.4 * v_new
        if abs(v_next - v_i) < 1e-10:
            break
        v_i = v_next
    return v_i


def profile_power_per_rotor(V, beta):
    """Profile drag power per rotor."""
    return (1.0/8.0) * rho * N_b * c_bar * Cd0_rot * Omega**3 * R**4


def rotor_power_total(V, beta, T_per):
    """Total power for all N_rotors rotors."""
    v_i = induced_velocity(T_per, V, beta)
    P_i = kappa * T_per * (V * np.sin(beta) + v_i)
    P_0 = profile_power_per_rotor(V, beta)
    return N_rotors * (P_i + P_0)


def force_balance(m_tot, V, CL, S, AR, e):
    """Force balance: tilted rotor + optional wing."""
    q      = 0.5 * rho * V**2
    W      = m_tot * g
    L_wing = q * S * CL        if S > 0 else 0.0
    D_wing = q * S * wing_CD(CL, AR, e) if S > 0 else 0.0
    D_body = q * A_body * CD_body
    D_tot  = D_wing + D_body
    W_eff  = max(W - L_wing, 0.01)
    beta   = np.arctan2(D_tot, W_eff)
    T_tot  = np.sqrt(W_eff**2 + D_tot**2)
    return T_tot / N_rotors, beta, L_wing, D_tot


def hover_power(m_tot):
    T_per = m_tot * g / N_rotors
    v_H   = np.sqrt(T_per / (2.0 * rho * A_rot))
    P_i   = kappa * T_per * v_H
    P_0   = (1.0/8.0) * rho * N_b * c_bar * Cd0_rot * Omega**3 * R**4
    return N_rotors * (P_i + P_0)


# =============================================================================
# BASELINE  (no wing, forward flight at V_design)
# =============================================================================

P_hover_base = hover_power(m_base)
print(f"\nHover power (no wing):                    {P_hover_base:.1f} W")

T_per0, beta0, _, _ = force_balance(m_base, V_design, 0.0, 0.0, AR_arr[0], 1.0)
P_no_wing = rotor_power_total(V_design, beta0, T_per0)
print(f"Forward flight power (no wing, V=10 m/s): {P_no_wing:.1f} W")
print(f"10% reduction target:                      {0.9*P_no_wing:.1f} W")

# =============================================================================
# WING SWEEP  -  power and mass vs wingspan  (using LLT e for each AR)
# =============================================================================

b_arr = np.linspace(0.0, 5.0, 150)


def power_for_config(V, m_t, S, AR, CL, e):
    """Total rotor power for a given flight condition and wing config."""
    T_per, beta, _, _ = force_balance(m_t, V, CL, S, AR, e)
    return rotor_power_total(V, beta, T_per)


def best_power_at(b, AR, V=V_design):
    """Minimum rotor power over CL for given wingspan and AR (LLT e and lam)."""
    lam = shape_opt[AR]['lam']
    e   = shape_opt[AR]['e']
    S   = b**2 / AR if b > 0 else 0.0
    m_w = wing_mass(b, AR, lam)
    m_t = m_base + m_w

    if S < 1e-6:
        T_per, beta, _, _ = force_balance(m_t, V, 0.0, 0.0, AR, e)
        return rotor_power_total(V, beta, T_per), m_t, 0.0, np.degrees(beta)

    res = minimize_scalar(
        lambda cl: power_for_config(V, m_t, S, AR, cl, e),
        bounds=(CL_min, CL_max), method='bounded', options={'xatol': 1e-5}
    )
    CL_opt = res.x
    P_opt  = res.fun
    _, beta, _, _ = force_balance(m_t, V, CL_opt, S, AR, e)
    return P_opt, m_t, CL_opt, np.degrees(beta)


sweep = {}
for AR in AR_arr:
    P_list, m_list, CL_list, beta_list = [], [], [], []
    for b in b_arr:
        P, m, cl, bd = best_power_at(b, AR)
        P_list.append(P); m_list.append(m)
        CL_list.append(cl); beta_list.append(bd)
    sweep[AR] = dict(P=np.array(P_list), m=np.array(m_list),
                     CL=np.array(CL_list), beta=np.array(beta_list))

print("\n--- Optimum wingspan per AR ---")
opt = {}
for AR in AR_arr:
    idx   = np.argmin(sweep[AR]['P'])
    b_opt = b_arr[idx]
    P_opt = sweep[AR]['P'][idx]
    m_opt = sweep[AR]['m'][idx]
    opt[AR] = dict(b=b_opt, P=P_opt, m=m_opt)
    print(f"  AR={AR} (lam={shape_opt[AR]['lam']:.1f}, e={shape_opt[AR]['e']:.4f}): "
          f"b={b_opt:.2f}m  P={P_opt:.1f}W  m={m_opt:.3f}kg  "
          f"dP={100*(P_opt-P_no_wing)/P_no_wing:+.2f}%")

# --- Figure 3: Power and mass vs wingspan ---
colors = ['tab:blue', 'tab:orange', 'tab:green']
fig3, axes3 = plt.subplots(1, 2, figsize=(13, 5))
for AR, col in zip(AR_arr, colors):
    lam = shape_opt[AR]['lam']
    e   = shape_opt[AR]['e']
    axes3[0].plot(b_arr, sweep[AR]['P'], color=col, lw=2,
                  label=f'AR={AR}, $\\lambda={lam:.1f}$, $e={e:.3f}$')
    axes3[1].plot(b_arr, sweep[AR]['m'], color=col, lw=2,
                  label=f'AR={AR}, $\\lambda={lam:.1f}$')
    axes3[0].plot(opt[AR]['b'], opt[AR]['P'], 'o', color=col, ms=7)

axes3[0].axhline(P_no_wing,     color='k',   ls='--', lw=1.3, label='No-wing baseline')
axes3[0].axhline(0.9*P_no_wing, color='red', ls=':',  lw=1.3, label='-10% target')
axes3[0].set_xlabel('Wingspan  $b$  [m]')
axes3[0].set_ylabel('Total rotor power  [W]')
axes3[0].set_title('Power vs wingspan  ($V = 10$ m/s)')
axes3[0].legend(fontsize=9)

axes3[1].axhline(m_base, color='k', ls='--', lw=1.3, label='No-wing mass')
axes3[1].set_xlabel('Wingspan  $b$  [m]')
axes3[1].set_ylabel('Total aircraft mass  [kg]')
axes3[1].set_title('Aircraft mass vs wingspan')
axes3[1].legend(fontsize=9)
plt.tight_layout()
plt.savefig('task6_wing_sweep.png', dpi=150)
plt.show()
print("Saved: task6_wing_sweep.png")

# --- Figure 3b: zoomed view b = 0 to 1 m ---
fig3b, ax3b = plt.subplots(figsize=(7, 5))
for AR, col in zip(AR_arr, colors):
    mask = b_arr <= 1.0
    ax3b.plot(b_arr[mask], sweep[AR]['P'][mask], color=col, lw=2,
              label=f'AR={AR}')
    idx_z = np.argmin(sweep[AR]['P'][mask])
    ax3b.plot(b_arr[mask][idx_z], sweep[AR]['P'][mask][idx_z],
              'o', color=col, ms=7)

ax3b.axhline(P_no_wing, color='k', ls='--', lw=1.3, label='No-wing baseline')
ax3b.set_xlabel('Wingspan  $b$  [m]')
ax3b.set_ylabel('Total rotor power  [W]')
ax3b.set_title(r'Power vs wingspan -- zoomed view  ($V = 10$ m/s,  $b \leq 1$ m)')
ax3b.legend(fontsize=10)
plt.tight_layout()
plt.savefig('task6_wing_sweep_zoom.png', dpi=150)
plt.show()
print("Saved: task6_wing_sweep_zoom.png")

# =============================================================================
# 10% REDUCTION ANALYSIS
# =============================================================================

best_AR = min(AR_arr, key=lambda ar: opt[ar]['P'])
best_P  = opt[best_AR]['P']
target  = 0.9 * P_no_wing

print(f"\n--- 10% reduction analysis (best AR={best_AR}) ---")
print(f"  Best power (rho_wing=74): {best_P:.1f} W  (target {target:.1f} W)")

if best_P <= target:
    print("  10% reduction achieved with rho_wing = 74 kg/m^3.")
    rho_req, b_req = rho_wing, opt[best_AR]['b']
else:
    print("  10% reduction NOT achievable at 74 kg/m^3. Searching required density...")
    AR_fix   = best_AR
    lam_fix  = shape_opt[AR_fix]['lam']
    e_fix    = shape_opt[AR_fix]['e']
    b_search = np.linspace(0.1, 8.0, 200)
    rho_req  = None

    for rho_w in np.linspace(74.0, 0.5, 500):
        P_scan = []
        for b in b_search:
            S   = b**2 / AR_fix
            m_w = (rho_w / rho_wing) * wing_mass(b, AR_fix, lam_fix)
            m_t = m_base + m_w
            res = minimize_scalar(
                lambda cl: power_for_config(V_design, m_t, S, AR_fix, cl, e_fix),
                bounds=(CL_min, CL_max), method='bounded')
            P_scan.append(res.fun)
        P_scan = np.array(P_scan)
        if P_scan.min() <= target:
            rho_req = rho_w
            b_req   = b_search[P_scan.argmin()]
            print(f"  Max allowable density: rho_wing <= {rho_req:.1f} kg/m^3 "
                  f"at b ~ {b_req:.2f} m  (P = {P_scan.min():.1f} W)")
            break

    if rho_req is None:
        print("  10% reduction not achievable even at very low density.")
        rho_req, b_req = 0.5, b_search[-1]

# =============================================================================
# FINAL DESIGN DECISION
# =============================================================================

best_P_all = min(opt[AR]['P'] for AR in AR_arr)
dP_best    = 100.0 * (P_no_wing - best_P_all) / P_no_wing

if dP_best >= 1.0:
    best_AR_f = min(AR_arr, key=lambda ar: opt[ar]['P'])
    b_final   = opt[best_AR_f]['b']
    m_final   = opt[best_AR_f]['m']
    lam_f     = shape_opt[best_AR_f]['lam']
    e_f       = shape_opt[best_AR_f]['e']
    AR_final  = best_AR_f
    S_final   = b_final**2 / AR_final
    print(f"\nFinal design: WITH wing  AR={AR_final}, lam={lam_f:.1f}, "
          f"b={b_final:.2f} m, S={S_final:.3f} m^2, e={e_f:.4f}")
else:
    b_final, m_final = 0.0, m_base
    AR_final, lam_f, e_f, S_final = AR_arr[1], shape_opt[AR_arr[1]]['lam'], \
                                     shape_opt[AR_arr[1]]['e'], 0.0
    print(f"\nFinal design: NO wing  "
          f"(best wing gives only {dP_best:.2f}% reduction - "
          f"wing mass outweighs lift on Mars where q = {0.5*rho*V_design**2:.1f} Pa)")

# =============================================================================
# SPEED SWEEP  0 - 12 m/s
# =============================================================================

V_arr      = np.linspace(0.0, 12.0, 120)
P_speed    = []
beta_speed = []

for V in V_arr:
    if V < 0.3:
        P_speed.append(hover_power(m_final))
        beta_speed.append(0.0)
        continue
    if S_final > 1e-6:
        res  = minimize_scalar(
            lambda cl: power_for_config(V, m_final, S_final, AR_final, cl, e_f),
            bounds=(CL_min, CL_max), method='bounded')
        CL_v = res.x
    else:
        CL_v = 0.0
    T_per, beta, _, _ = force_balance(m_final, V, CL_v, S_final, AR_final, e_f)
    P_speed.append(rotor_power_total(V, beta, T_per))
    beta_speed.append(np.degrees(beta))

P_speed    = np.array(P_speed)
beta_speed = np.array(beta_speed)

fig4, ax1 = plt.subplots(figsize=(9, 5))
ax2 = ax1.twinx()
l1, = ax1.plot(V_arr, P_speed,    'b-',  lw=2, label='Total rotor power [W]')
l2, = ax2.plot(V_arr, beta_speed, 'r--', lw=2, label=r'Rotor tilt $\beta$ [deg]')
ax1.set_xlabel('Flight speed  [m/s]')
ax1.set_ylabel('Total rotor power  [W]',       color='b')
ax2.set_ylabel(r'Rotor tilt angle $\beta$ [deg]', color='r')
ax1.tick_params(axis='y', labelcolor='b')
ax2.tick_params(axis='y', labelcolor='r')
ax1.set_title('Power and rotor tilt vs flight speed (final design)')
ax1.set_xlim(0, 12)
design_label = (f"Wing: AR={AR_final}, $b={b_final:.2f}$ m"
                if b_final > 0 else "No wing")
ax1.text(0.98, 0.97, design_label, transform=ax1.transAxes,
         ha='right', va='top', fontsize=10,
         bbox=dict(boxstyle='round', fc='w', alpha=0.8))
ax1.legend(handles=[l1, l2], loc='upper left', fontsize=10)
plt.tight_layout()
plt.savefig('task6_speed_sweep.png', dpi=150)
plt.show()
print("Saved: task6_speed_sweep.png")

# =============================================================================
# SUMMARY
# =============================================================================
print("\n" + "=" * 60)
print("TASK 6 SUMMARY")
print("=" * 60)
print(f"Mars: rho={rho} kg/m^3  g={g} m/s^2  "
      f"q={0.5*rho*V_design**2:.1f} Pa at V={V_design} m/s")
print(f"Aircraft: m={m_base} kg, {N_rotors} rotors, R={R} m")
print(f"Hover power:            {P_hover_base:.1f} W")
print(f"Forward power (no wing): {P_no_wing:.1f} W")
print()
print("LLT optimal wing shapes:")
for AR in AR_arr:
    o = shape_opt[AR]
    print(f"  AR={AR}: lam*={o['lam']:.1f}  theta_tip*={o['theta_tip']:.0f} deg  "
          f"e={o['e']:.4f}")
print()
print("Power sweep results:")
for AR in AR_arr:
    o = opt[AR]
    print(f"  AR={AR}: b_opt={o['b']:.2f}m  P={o['P']:.1f}W  "
          f"dP={100*(o['P']-P_no_wing)/P_no_wing:+.2f}%")
print()
print(f"10% reduction: requires rho_wing <= {rho_req:.1f} kg/m^3 at b~{b_req:.2f} m")
print(f"Final design: {'wing b='+str(round(b_final,2))+'m AR='+str(AR_final) if b_final>0 else 'no wing'}")
print("=" * 60)
