from Classes import Node
import numpy as np
import numpy.typing as npt
import pandas as pd
from Simulator import Simulator
from SDA import SDA
from typing import Tuple        ##Bruger vi så vi kan få syntax highlighting
import seaborn as sns
import matplotlib.pyplot as plt
import copy ##Bruger vi til at genbruge antenner
from mesh import construct_adjacencylist, all_paths, find_worst_link


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

def assign_random_drone_pos(rng: np.random.Generator) -> npt.NDArray[np.floating]:
    return np.array([
            rng.uniform(-3000, 200),
            rng.uniform(-2000, -300),
            rng.uniform(50, 150)
        ])






def run_simulation(args: Tuple[int, list[Node], npt.NDArray[np.floating], int]):
    seed, drones, time, N_helper_drones = args
    ##Sætter en random op efter vores seed.
    rng = np.random.default_rng(seed) ##Seed gør vi kan lave deterministiske resultater.

    ###Vores øvrgie simulationsobjekter
    ground_stations = [
        Node("B_0", np.array([0,0,2]), antenna=SDA(80, 20, Beta=0.05), tx_power=20)
    ]

    jammers = [
        Node("Jammer_0", assign_random_pos(-2000, rng), antenna=SDA(1), tx_power=27),
        Node("Jammer_1", assign_random_pos(-1800, rng), antenna=SDA(1), tx_power=20),
        Node("Jammer_2", assign_random_pos(-1800, rng), antenna=SDA(1), tx_power=20),
        Node("Jammer_3", assign_random_pos(-1800, rng), antenna=SDA(1), tx_power=20),
        Node("Jammer_4", assign_random_pos(-1800, rng), antenna=SDA(1), tx_power=20),
    ]


    for i in range(N_helper_drones):
        drones.append(
            Node(f"d{i}", assign_random_drone_pos(rng), copy.copy(drones[0].antenna), tx_power=20)
        )
    


    sim = Simulator(drones, ground_stations, jammers)

    timestamps, snrb2d, snrd2b = [], [], []

    d0 = drones[0].name

    for t in time:
        ##Starts by updating all drones
        sim.update_positions(t)

        ##Får vores forbindelser
        (name_rx, name_tx, snr, rssi) = sim.evaluate_links()
        

        ##Alle possible paths fra drone til base
        graph = construct_adjacencylist(name_rx, name_tx, snr)

        path_candidates = all_paths(graph, d0, "B_0")


        best_path_d2b = -np.inf
        for path in path_candidates:
            best_path_d2b = max(find_worst_link(path), best_path_d2b)

        ##den bedste path, er den path for den VÆRSTE SNR er højest
        snrd2b.append(10*np.log10(np.abs(best_path_d2b)))


        path_candidates = all_paths(graph, "B_0", d0)
        best_path_b2d = -np.inf
        for path in path_candidates:
            best_path_b2d = max(find_worst_link(path), best_path_b2d)

        ##Samme dans men den anden vej rundt

        snrb2d.append(10*np.log10(np.abs(best_path_b2d)))
        

        timestamps.append(t)

 


    drone_name = [d0] * len(timestamps)
    N_helper_drones = [N_helper_drones]* len(timestamps)
    Jammer_positions = [jammer.pos for jammer in jammers]
    Drone_positions = [drones[i].pos for i in range(1, len(drones))]

    return timestamps, snrd2b, snrb2d, drone_name, Jammer_positions, Drone_positions, N_helper_drones






if __name__ == "__main__":

    ##Vores time vector
    T_s = 0.5
    time = np.arange(120, 320, T_s)



    ##Parametre vi skal teste
    #num_helpers = range(6) ##Bruger vi ik
    Drones = [ Node("dir", "./path/Bench_path.csv", SDA(180, 40, 0.05), tx_power=20)] #Node("iso", "./path/Bench_path.csv", SDA(1), tx_power=20 ),
    seeds = np.arange(300)
    N_helper_drones = np.arange(20)

    inputs = []
    for seed, Drone, helpers in product(seeds, Drones, N_helper_drones):
        inputs.append(
            (seed, [Drone], time, helpers) ##TupleTupleTupleTupleTupleTupleTupleTupleTupleTuple
        )

    results = []
    ###Kun for at køre fejlfinding på 1 thread#######
    #for input in inputs:
    #    results.append(run_simulation(input))
    ###################################################

    with mp.Pool(processes=mp.cpu_count() - 1) as pool: ##Næsten det samme som før MEN!!! tqdm gør man kan få en lille nice process bar.
        
        for result in tqdm(
                pool.imap_unordered(run_simulation, inputs), ##Fortæller den skal køre i ligegyldig rækkefølge og bare få en input med
                total=len(inputs), ##Så mange inputs der er i alt
                smoothing=0): ##fortæller noget om hvor tit progressbaren skal opdateres
            results.append(result)

    ##Folder det hele ud igen.
    timestamps_all, snrd2b_all, snrb2d_all, drone_names_all, jammer_positions_all, drones_pos_all, N_helper_drones = zip(*results)
    timestamps_flat   = np.concatenate(timestamps_all)
    snrd2b_flat       = np.concatenate(snrd2b_all)
    snrb2d_flat       = np.concatenate(snrb2d_all)
    drone_names_flat  = np.concatenate(drone_names_all)
    N_helper_drones = np.concatenate(N_helper_drones)

    jammer_positions = [
    pos
    for sim in jammer_positions_all
    for pos in sim
    ]
    drones_pos = [
        pos 
        for sim in drones_pos_all
        for pos in sim
    ]
    jammer_positions = np.array(jammer_positions)
    drones_pos = np.array(drones_pos)
    # Save jammer positions
    np.savetxt("jammer_positions.csv", jammer_positions, delimiter=",", header="x,y,z", comments="", fmt="%.6f")

    # Save drone positions
    np.savetxt("drones_positions.csv", drones_pos, delimiter=",", header="x,y,z", comments="", fmt="%.6f")

    df = pd.DataFrame({
        "t"             : timestamps_flat,
        "snrd2b"        : snrd2b_flat,
        "snrb2d"        : snrb2d_flat,
        "drone_names"   : drone_names_flat,
        "n_helpers" : N_helper_drones,
    })

    print(df[df["drone_names"] == "iso"].head(20))
    print(df[df["drone_names"] == "dir"].head(20))

    df.to_csv("output_w_helpers_increased_spawn.csv")

    




#Performance profiler:
# python -m cProfile -o output.prof dit_script.py