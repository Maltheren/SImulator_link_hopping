import numpy as np
import matplotlib.pyplot as plt
import numpy.typing as npt




class SDA:
    def __init__(self, Granularity: int = 4, HPBW: float | None = None, Beta: float = 0):
        self.Granularity = Granularity
        self.Antenna_directions = np.linspace(-np.pi, np.pi, Granularity+1)[:Granularity]
        self.closest_theta = 0
        self.HPBW = (HPBW/2) / 180 * np.pi if HPBW is not None else np.pi / Granularity
        self.Beta = Beta



    def get_gain(self, theta: np.floating, phi: np.floating) -> np.floating:
        '''
        Docstring for get_gain
        
        :param self: Description
        :param theta: The theta angle in radians
        :param phi: The phi angle in radians
        '''
        if self.HPBW == np.pi:
            return 1
        n = np.log(0.5) / np.log(np.cos(self.HPBW/2)) # Calculate N based on the HPBW
        #Bliver nød til at lave den til en int, eller kan potensen ikke lide det
        n = int(np.ceil(n)) # Round up to the nearest integer
        

        return np.abs(np.cos((theta-self.closest_theta)/2))**n * np.abs(np.cos(phi/2))**n +self.Beta

    def set_dir(self, theta: np.floating):
        '''
        Docstring for set_dir
        
        :param self: Description
        :param theta: The theta angle in radians
        :returns: Closest theta index in the linspace grid
        '''
        closest_index = np.argmin(np.abs(self.Antenna_directions - theta))
        self.closest_theta = self.Antenna_directions[closest_index]
    
    




if __name__ == "__main__":
    Antenna = SDA(Granularity=1, HPBW=90, Beta=0.0)
    theta_test = np.pi /4  # Example theta
    phi_test = np.pi / 4    # Example phi
    print(Antenna.Antenna_directions)
    

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={'projection': 'polar'})
    test_sweep = np.linspace(0, 2*np.pi, Antenna.Granularity+1)
    for theta in test_sweep:
        Antenna.set_dir(theta)
        theta_sweep = np.linspace(0, 2*np.pi, 4000)
        gains = []
        
        # Calculate gain for each theta angle
        for theta in theta_sweep:
            gain = Antenna.get_gain(theta, 0)
            gains.append(gain)
        
        gains = np.array(gains)
        # Clip gains to a small positive value before converting to dB to avoid -inf/NaN
        gains_clipped = np.clip(gains, 1e-12, None)

        # Plot in polar coordinates
        
        ax.plot(theta_sweep, 10*np.log10(gains_clipped), color='b', linewidth=2)

    ax.grid(True)
    ax.set_ylim(-20, 5)

    plt.show()