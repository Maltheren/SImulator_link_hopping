from Classes import Node
import numpy as np
import numpy.typing as npt
import pandas as pd
from typing import Tuple        ##Bruger vi så vi kan få syntax highlighting


class Simulator:
    def __init__(self, drones: list[Node], ground_stations: list[Node], jammers: list[Node]):
        
        self.drones = drones
        self.ground_stations = ground_stations
        self.jammers = jammers
        pass


    def update_positions(self, t: float):
        for drone in self.drones:
            drone.update_pos(t)
    

    def evaluate_links(self) -> Tuple[list[str], list[str], list[float], list[float]]:
        allies = (self.drones+ self.ground_stations)
        name_rx, name_tx, snr, rssi = ([],[],[],[]) #Ik så meget andet end en skør måde at lave 4 arrays

        for node_rx in allies:
            for node_tx in allies:
                if (node_rx == node_tx):
                    continue
                if (node_rx.getDist2Target(node_tx) < 0.1):
                    continue

                channel_rssi, channel_snr = node_rx.getLinkstate(node_tx, self.jammers)
                name_rx.append(node_rx.name)
                name_tx.append(node_tx.name)
                snr.append(channel_snr)
                rssi.append(channel_rssi)
        
        return (np.array(name_rx), np.array(name_tx), np.array(snr), np.array(rssi))







