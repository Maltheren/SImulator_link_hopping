from Classes import Node
import numpy as np
import numpy.typing as npt
import pandas as pd
from Simulator import Simulator
from SDA import SDA
from typing import Tuple        ##Bruger vi så vi kan få syntax highlighting
import seaborn as sns
import matplotlib.pyplot as plt



##Gør multiprocessing nemmere
import multiprocessing as mp
from tqdm.auto import tqdm
from itertools import product ##GØr det nemmere for os at lave kombinationer af instillinger

##For at få performance metrics
from time import perf_counter


def assign_random_pos(max_y, rng: np.random.Generator):
    return np.array([
        rng.uniform(-3000, 200),
        rng.uniform(-2300, max_y),
        2
    ])



def run_simulation(args: Tuple[int, list[Node], npt.NDArray[np.floating]]):
    seed, drones, time = args
    ##Sætter en random op efter vores seed.
    rng_jammers = np.random.default_rng(seed) ##Seed gør vi kan lave deterministiske resultater.

    ###Vores øvrgie simulationsobjekter
    ground_stations = [
        Node("B_0", np.array([0,0,2]), antenna=SDA(80, 20, Beta=0.05), tx_power=20)
    ]

    jammers = [
        Node("Jammer_0", assign_random_pos(-2000, rng_jammers), antenna=SDA(1), tx_power=27),
        Node("Jammer_1", assign_random_pos(-1800, rng_jammers), antenna=SDA(1), tx_power=20),
        Node("Jammer_2", assign_random_pos(-1800, rng_jammers), antenna=SDA(1), tx_power=20),
        Node("Jammer_3", assign_random_pos(-1800, rng_jammers), antenna=SDA(1), tx_power=20),
        Node("Jammer_4", assign_random_pos(-1800, rng_jammers), antenna=SDA(1), tx_power=20),
    ]
    sim = Simulator(drones, ground_stations, jammers)

    timestamps, snrb2d, snrd2b = [], [], []

    d0 = drones[0].name

    for t in time:
        ##Starts by updating all drones
        sim.update_positions(t)

        ##Får vores forbindelser
        (name_rx, name_tx, snr, rssi) = sim.evaluate_links()
        
        ##Finder de 2 forbindelser vi vil logge
        drone2base = snr[(name_tx == d0) & (name_rx == "B_0")]
        base2drone = snr[(name_rx == d0) & (name_tx == "B_0")]

        timestamps.append(t)
        snrd2b.append(10*np.log10(np.abs(drone2base)))
        snrb2d.append(10*np.log10(np.abs(base2drone)))


    drone_name = [d0] * len(timestamps)
    Jammer_positions = [jammer.pos for jammer in jammers]

    return timestamps, snrd2b, snrb2d, drone_name, Jammer_positions






if __name__ == "__main__":

    ##Vores time vector
    T_s = 0.5
    time = np.arange(0, 320, T_s)



    ##Parametre vi skal teste
    #num_helpers = range(6) ##Bruger vi ik
    Drones = [Node("iso", "./path/Bench_path.csv", SDA(1), tx_power=20 ), Node("dir", "./path/Bench_path.csv", SDA(180, 40, 0.05), tx_power=20)]
    seeds = np.arange(300)

    inputs = []
    for seed, Drone in product(seeds, Drones):
        inputs.append(
            (seed, [Drone], time) ##TupleTupleTupleTupleTupleTupleTupleTupleTupleTuple
        )

    #results = []
    #for input in inputs:
    #    results.append(run_simulation(input))
    


    results = []

    with mp.Pool(processes=mp.cpu_count() - 1) as pool: ##Næsten det samme som før MEN!!! tqdm gør man kan få en lille nice process bar.
        
        for result in tqdm(
                pool.imap_unordered(run_simulation, inputs), ##Fortæller den skal køre i ligegyldig rækkefølge og bare få en input med
                total=len(inputs), ##Så mange inputs der er i alt
                smoothing=0): ##fortæller noget om hvor tit progressbaren skal opdateres
            results.append(result)

    ##Folder det hele ud igen.
    timestamps_all, snrd2b_all, snrb2d_all, drone_names_all, jammer_positions_all = zip(*results)
    timestamps_flat   = np.concatenate(timestamps_all)
    snrd2b_flat       = np.concatenate(snrd2b_all)
    snrb2d_flat       = np.concatenate(snrb2d_all)
    drone_names_flat  = np.concatenate(drone_names_all)


    jammer_positions = [
    pos
    for sim in jammer_positions_all
    for pos in sim
    ]
    jammer_positions = np.array(jammer_positions)

    

    df = pd.DataFrame({
        "t"             : timestamps_flat,
        "snrd2b"        : snrd2b_flat,
        "snrb2d"        : snrb2d_flat,
        "drone_names"   : drone_names_flat,
    })
    df.to_csv("output.csv")

    




#Performance profiler:
# python -m cProfile -o output.prof dit_script.py