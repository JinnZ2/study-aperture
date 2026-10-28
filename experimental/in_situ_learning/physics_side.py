"""Numbers on the physics side of THEORY.md T7. CC0, stdlib only.

Inputs: the proton Larmor frequency stated in Jensen et al. (arXiv:2603.19448,
Section 4.1: about 14.8 MHz, X-band, 80 K) and CODATA constants. Everything else is
computed. Thermal polarization of a spin-1/2 ensemble: P = tanh(h nu / (2 k T)).

    python3 physics_side.py            # print the numbers
    python3 physics_side.py selftest   # exit 1 if any pinned value changes
"""
import math
import sys

H = 6.62607015e-34        # J s (exact, SI 2019)
K = 1.380649e-23          # J/K (exact, SI 2019)
GAMMA_E = 28.02495e9      # Hz/T, free electron, |gamma_e| / 2pi (CODATA)
GAMMA_H = 42.577478e6     # Hz/T, proton, gamma_p / 2pi (CODATA)

NU_H = 14.8e6             # Hz, Jensen et al. Section 4.1 ("about 14.8 MHz")
T = 80.0                  # K, Jensen et al. Section 4.2


def polarization(nu, temp):
    return math.tanh(H * nu / (2 * K * temp))


def run():
    b = NU_H / GAMMA_H
    nu_e = GAMMA_E * b
    p_e, p_h = polarization(nu_e, T), polarization(NU_H, T)
    return {
        "field_T": round(b, 4),
        "electron_GHz": round(nu_e / 1e9, 3),
        "P_electron": float(f"{p_e:.3e}"),
        "P_proton": float(f"{p_h:.3e}"),
        "enhancement_ceiling": round(p_e / p_h, 1),   # ~ gamma_e / gamma_H at high T
        "gamma_ratio": round(GAMMA_E / GAMMA_H, 1),
        "paper_reported_max": 180,                    # Section 2.2, "approaching 180"
    }


PINNED = {"field_T": 0.3476, "electron_GHz": 9.742, "P_electron": 2.922e-03,
          "P_proton": 4.439e-06, "enhancement_ceiling": 658.2, "gamma_ratio": 658.2,
          "paper_reported_max": 180}


def main():
    r = run()
    print("Physics side of T7 (computed from Jensen et al. Section 4.1-4.2 + CODATA)")
    print(f"  field B0                        {r['field_T']} T")
    print(f"  electron Larmor frequency       {r['electron_GHz']} GHz")
    print(f"  thermal electron polarization   {r['P_electron']}  (at {T:.0f} K)")
    print(f"  thermal proton polarization     {r['P_proton']}")
    print(f"  ceiling on enhancement          {r['enhancement_ceiling']}  (= P_e / P_H; gamma ratio {r['gamma_ratio']})")
    print(f"  reported in the paper           'approaching {r['paper_reported_max']}'")
    print("  The order the microwaves move is the electron polarization the field created;")
    print("  the field and temperature set the ceiling, not the drive.")


if __name__ == "__main__":
    if sys.argv[1:] == ["selftest"]:
        got = run()
        bad = [k for k in PINNED if got[k] != PINNED[k]]
        for k in bad:
            print(f"CHANGED {k}: expected {PINNED[k]}, got {got[k]}")
        print(f"checks: {len(PINNED)}   failed: {len(bad)}")
        sys.exit(1 if bad else 0)
    main()
