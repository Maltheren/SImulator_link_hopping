
from __future__ import annotations
import numpy as np              ##Numpy OFC
import numpy.typing as npt      ##Numpy typing så vi får niice syntax highlighting
import pandas as pd             ##Pands for linkstates
from SDA import *               ##Mikkels antenner
from numba import njit          ##accelering
from Functions import FSPL      ##Freespace slaveberegning
from typing import Tuple        ##Bruger vi så vi kan få syntax highlighting


##Det hyppist brugte funktioner, 
@njit()
def getDist2Target_numba(pos, target):
    diff = target - pos
    return np.sqrt(np.sum(diff ** 2))

@njit()
def getDIR2Target_numba(pos, target):
    DIR = target - pos
    DIR = DIR / np.linalg.norm(DIR)
    return DIR

@njit()
def getPolarCoordinates_numba(vector: npt.NDArray[np.floating]) -> list[float, float]:
    """Forsøger at finde de vinkler der giver vektoren suppleret."""
    theta = np.arctan2(vector[1], vector[0])
    phi = np.arcsin( vector[2] /np.linalg.norm(vector))
    return theta, phi

@njit()
def transform2local_numba(dronepeg, vector):
    dronepeg[2] = 0.0
    up = np.array([0.0, 0.0, 1.0])

    # cross product
    y_loc = np.array([
        dronepeg[1]*up[2] - dronepeg[2]*up[1],
        dronepeg[2]*up[0] - dronepeg[0]*up[2],
        dronepeg[0]*up[1] - dronepeg[1]*up[0]
    ])

    # matrix construction
    Matrix = np.vstack((dronepeg, y_loc, up))

    # transform
    transformers = Matrix @ vector
    return transformers
#####################################################3



class Node:
    def __init__(self, name="NaN", path:str | npt.NDArray[np.floating] = np.array([0, 0, 0]), antenna = SDA(), tx_power: float =1):
        
        if type(path) == str:
            df = pd.read_csv(path)
            df.columns = df.columns.str.strip()
           
            self.time = df["time"]
           
            self.pos_lookup = np.transpose(np.array([
                df["x"],
                df["y"],
                df["z"]
            ]))
            self.pos = self.pos_lookup[0]
            self.lastpos = self.pos   
            self.maxtime = np.max(self.time) ##Optimering, bruger vi så vi ik skal køre numpy.max hver gang
        else:
            self.pos = path
            self.time = None
            self.pos_lookup = None
            self.lastpos = self.pos
       
        self.name = name
        self.antenna = antenna
        self.tx_power = 10**((tx_power-30)/10)
        
        self.hpbw = antenna.HPBW
        self.gran = antenna.Granularity
        self.dir = np.array([0,1,0])
        

    def update_pos(self, t: float):
        
        if self.time is None:
            return self.pos
        
        self.lastpos = self.pos
        ## Snak om at interpolere
        t = t % self.maxtime
        idx_1 = np.searchsorted(self.time, t, side='right') - 1
        idx_1 = max(idx_1, 0)
        idx_2 = (idx_1 + 1) % len(self.time) ## Next index 

        t_1 = self.time[idx_1]
        t_2 = self.time[idx_2]

        alpha = (t-t_1) / (t_2 -t_1) # AKA. Hvor mange "procent" af tidslinjen t er.

        self.pos = self.pos_lookup[idx_1] + alpha * (self.pos_lookup[idx_2] - self.pos_lookup[idx_1])

        self.dir = self.pos - self.lastpos
        length = np.linalg.norm(self.dir)
        if(length > 0.001):
            self.dir /= length
        else:
            self.dir = np.array([0,1,0])
        #Simpel matematik: Start ved P1 + alpha (procentdel) * linjen - Axel...   (du skal ha bøde axel) - Malthe



    def getPos (self) -> npt.NDArray[np.floating]:
        return self.pos


    def getDIR (self) -> npt.NDArray[np.floating]:
        DIR = self.pos - self.lastpos
        if np.linalg.norm(DIR) == 0:
            return np.array([1, 0, 0])
        DIR = DIR / np.linalg.norm(DIR)
        return DIR

    def getDIR2Target(self, target: npt.NDArray[np.floating] | Node) -> npt.NDArray[np.floating]:
        if type(target) is Node:
            return getDist2Target_numba(self.pos, target.getPos())
        else:
            return getDist2Target_numba(self.pos, target)
    

    def getDist2Target (self, target: npt.NDArray[np.floating] | Node) -> np.floating:
        if type(target) is Node:
            return getDist2Target_numba(self.pos, target.getPos())
        else:
            return getDist2Target_numba(self.pos, target)
  
    def transform2local(self, vector: npt.NDArray[np.floating]) -> npt.NDArray[np.floating]:
        '''
        Transformerer bassen MED HENSYN TIL Nodens egen retning!!
        
        :param self: Drone eller base
        :param vector: Hvilken vektor skal vi projektere op mod
        :return: (Theta, Phi) Vektoren i dronens koordinatsystem.
        '''
        ##Numba accerleret kode
        return transform2local_numba(self.dir, vector)

    def getPolarCoordinates(self, vector: npt.NDArray[np.floating]) -> list[float, float]:
        """Forsøger at finde de vinkler der giver vektoren suppleret."""
        return getPolarCoordinates_numba(vector)

    def getLinkstate(self, target: Node, Jammers: list[Node]) -> Tuple[float, float]:
        """
        Regner link fra et target (som tx) til os selv, som (rx)
        Returns, RSSI & SNR
        """
        
        polar_coords = self.getPolarCoordinates(self.transform2local(self.pos - target.getPos())) ##Finder den relative heading
        self.antenna.set_dir(polar_coords[0])
        p_s = self.antenna.get_gain(*polar_coords)* target.tx_power * FSPL(self.getDist2Target(target))
        p_n = 0
        for jammer in Jammers:
            heading = self.getPolarCoordinates(self.transform2local(self.pos - jammer.getPos()))
            p_n += self.antenna.get_gain(*heading) * FSPL(self.getDist2Target(jammer)) * jammer.tx_power
        
        return (p_s + p_n, p_s/p_n) ##rssi, SNR

        



if __name__ == "__main__":
    
    base1 = Node(path=[0,0,1], antenna_type='patch')
    drone = Node(path="BenchPath.csv", antenna_type='patch')
    t = 2


    drone.update_pos(t)

    #Retning fra drone til base
    DIR1 = drone.getDIR2Target(base1.getPos())
    #Retning fra base til drone
    DIR2 = base1.getDIR2Target(drone.getPos())
    
    print(f"drone pos {drone.getPos()}")




'''
    data = np.loadtxt("dronepath.txt", skiprows=1)
    time = data[:,0]
    pos = data[:,1:4]

    drone1 = drone(time, pos)
    base1 = base(np.array([3,3,3]))

    print(drone1.getPos(0))
    print(base1.pos)
    print(base1.getDist2Drone(drone1.getPos(0)))
'''

