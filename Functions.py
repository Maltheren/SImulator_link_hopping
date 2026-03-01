import numpy as np
from Classes import *

Frekvens = 2.4e9 # 2.4 GHz




"SINR = P_sig * G_rx * G_tx * L_pathsig / P_jammer * G_jammer * G_rx * L_path_jammer + N"




            



def FSPL(distance:float , frequency: float = 2.4e9) -> float:
    """Free Space Path Loss - lineær værdi"""
    c = 3e8  # Speed of light in m/s
    wavelength = c / frequency
    dist = abs(distance)
    return (wavelength/(4 * np.pi * dist)) ** 2




def to_dB(value):
    return 10 * np.log10(value)

def radiation_pattern(theta, phi):
    return np.cos(theta/2)**2 * np.cos(phi/2)**2


def assign_random_pos(max_y, rng: np.random.Generator):
    return np.array([
        rng.uniform(-3000, 200),
        rng.uniform(-2300, max_y),
        2
    ])


#Til data og plotter:

def hent_plot_data(df, rx_navn, tx_navn):
    """Filtrerer dataframe baseret på RX og TX navne."""
    return df[(df['RX'] == rx_navn) & (df['TX'] == tx_navn)]

def plot_forbindelse(df, rx_navn, tx_navn, kolonne='SINR'):
    subset = hent_plot_data(df, rx_navn, tx_navn)
    
    if subset.empty:
        print(f"Ingen data fundet for RX: {rx_navn} og TX: {tx_navn}")
        return
    
    plt.plot(subset['tid'], subset[kolonne] )
    #label=f'{tx_navn} to {rx_navn}'