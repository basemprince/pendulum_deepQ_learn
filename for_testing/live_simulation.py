#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb  5 22:35:39 2022

@author: parallels
"""
import sys
import os
import glob
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
import tensorflow as tf
from tensorflow.keras import layers
import numpy as np
from deep_q_network.enviroment.hybrid_pendulum import Hybrid_Pendulum
import time
import matplotlib.pyplot as plt

prev_dir= os.path.normpath(os.getcwd() + os.sep + os.pardir) 
#FOLDER = 'Q_weights_backup/'
#FOLDER = 'model_backup/'
FOLDER = prev_dir  + '/Q_weights_backup/model_51552/'
#FOLDER = prev_dir  + '/best_models/'
FILE_ACR = 'MODEL_51552_' 
#FILE_ACR = 'Q_weights_' 

from tensorflow.python.ops.numpy_ops import np_config
np_config.enable_numpy_behavior()
np.set_printoptions(threshold=sys.maxsize)
### --- Hyper paramaters

GAMMA                  = 0.9           # Discount factor 
PLOT                   = True          # plot results 
JOINT_COUNT            = 3             # number of joints in model
NU                     = 11            # discretized control count
INNER_ITR              = 300           # number of iterations for each seperate simulation
THRESHOLD_C            = 9e-1          # threshold for cost
THRESHOLD_V            = 9e-1          # threshold for velocity
STAY_UP                = 50            # how many iterations doing hand stand to account as target achieved
RENDER                 = True         # simulate the movements
SLOW_DOWN              = False          # to slow down render of simulation
def get_critic(nx,name):
    ''' Create the neural network to represent the Q function '''
    inputs = layers.Input(shape=(nx+JOINT_COUNT))
    state_out1 = layers.Dense(16, activation="relu")(inputs) 
    state_out2 = layers.Dense(32, activation="relu")(state_out1) 
    state_out3 = layers.Dense(64, activation="relu")(state_out2) 
    state_out4 = layers.Dense(64, activation="relu")(state_out3)
    outputs = layers.Dense(JOINT_COUNT)(state_out4)

    model = tf.keras.Model(inputs, outputs,name = name)

    return model
def reset_env():
    if JOINT_COUNT == 1:
        x0  = np.array([[np.pi], [0.]])
    elif JOINT_COUNT == 2:
        x0  = np.array([[np.pi, 0.], [0., 0.]])
    else:
        x0 = None
    return env.reset(x0) , 0.0 , 1, False

def reset_env_rand():
    return env.reset() , 0.0 , 1, False
    
def simulate_folder(itr=INNER_ITR):
    h_ctg = []
    model_sucess = []
    best_model = ''
    best_ctg = np.inf
    directory = glob.glob(FOLDER+'*')
    for file in sorted(directory):
        if file.endswith(".h5"):
            print('loading Model' , file,end='. ')
            Q.load_weights(file)
            x , ctg , gamma_i , reached = reset_env()
            at_target = 0
            for i in range(itr):      
                x_rep = np.repeat(x.reshape(1,-1),NU**(JOINT_COUNT),axis=0)
                xu_check = np.c_[x_rep,u_list]
                pred = Q.__call__(xu_check)
                u_ind = np.argmin(tf.math.reduce_sum(pred,axis=1), axis=0)
                u = u_list[u_ind]
                x, cost = env.step(u)
        #        print(cost , x[nv:])
                if cost <= THRESHOLD_C and (abs(x[nv:])<= THRESHOLD_V).all():
                    at_target+=1
#                    print(at_target)
        #            print("sucessfully reached")
                else:
                    at_target = 0
                
                if(at_target >= STAY_UP):
                    reached = True
                else:
                    reached = False
                if(at_target > 100):
                    print('passed')
                    break
                ctg += gamma_i*cost
                gamma_i *= GAMMA
                if(RENDER): env.render(SLOW_DOWN)   
            h_ctg.append(ctg)
            model_sucess.append(reached)
            if ctg < best_ctg and reached:
                best_ctg = ctg
                best_model = file
            print("Model was sucessful:" if reached else "Model failed", "with a cost to go of:",round(ctg,3))
    print("the best model performance is:", best_model, "with a cost to go of:",round(best_ctg,3)) if any(model_sucess) else print("None of the models reached target")
    if(PLOT):
        plt.plot( np.cumsum(h_ctg)/range(1,len(h_ctg)+1)  )
        plt.xlabel("Episode Number")
        plt.title ("Average Cost to Go")
        plt.show()                 


def simulate_sp(file_num,itr=INNER_ITR,rand=False,rend=True):
    directory = FOLDER + FILE_ACR
    file_name = directory + str(file_num) + '.h5'
    print('loading file' , file_name)
    Q.load_weights(file_name)
    x , ctg , gamma_i, reached  = reset_env() if not rand else reset_env_rand()
    at_target = 0
    for i in range(itr):      
        x_rep = np.repeat(x.reshape(1,-1),NU**(JOINT_COUNT),axis=0)
        xu_check = np.c_[x_rep,u_list]
        pred = Q.__call__(xu_check)
        u_ind = np.argmin(tf.math.reduce_sum(pred,axis=1), axis=0)
        u = u_list[u_ind]
        x, cost = env.step(u)
#        print(cost , x[nv:])
        if cost <= THRESHOLD_C and (abs(x[nv:])<= THRESHOLD_V).all():
            at_target+=1
#            print(at_target)
#            print("sucessfully reached")
        else:
            at_target = 0
        
        if(at_target >= STAY_UP):
            reached = True  
        else:
            reached = False
        if(at_target > 100):
            break
        ctg += gamma_i*cost
        gamma_i *= GAMMA
        if (rend):
            env.render(SLOW_DOWN)
    print("Model was sucessful:" if reached else "Model failed", "with a cost to go of:",ctg)
    return reached

def simulate_till(file_num,rand=True,rend=True,cut_of=False,itr=2000):
    directory = FOLDER + FILE_ACR
    file_name = directory + str(file_num) + '.h5'
    print('loading file' , file_name)
    Q.load_weights(file_name)
    x , ctg , gamma_i, reached  = reset_env() if not rand else reset_env_rand()
    at_target = 0
    t = time.time()
    reached = False
    iterations = 0
    while not reached or (cut_of and itr == iterations):  
        iterations+=1
        x_rep = np.repeat(x.reshape(1,-1),NU**(JOINT_COUNT),axis=0)
        xu_check = np.c_[x_rep,u_list]
        pred = Q.__call__(xu_check)
        u_ind = np.argmin(tf.math.reduce_sum(pred,axis=1), axis=0)
        u = u_list[u_ind]
        x, cost = env.step(u)
#        print(cost , x[nv:])
        if cost <= THRESHOLD_C and (abs(x[nv:])<= THRESHOLD_V).all():
            at_target+=1
#            print(at_target)
#            print("sucessfully reached")
        else:
            at_target = 0
        
        if(at_target >= STAY_UP):
            reached = True  
        else:
            reached = False
        if(at_target > 200):
            break
        ctg += gamma_i*cost
        gamma_i *= GAMMA
        if (rend):
            env.render(SLOW_DOWN)
    time_taken=time.time()-t
    print('Time:', round(time_taken,2), 'iterations:', iterations)
#    print("Model was sucessful:" if reached else "Model failed", "with a cost to go of:",ctg)
    return time_taken , iterations

def simulate_to_death_till(file_num,itr=20,rend=False,inner_iter=INNER_ITR,cut_off=False):
    time_total = 0
    total_iters = 0
    for i in range(itr):
        time_taken,iters = simulate_till(file_num,True,rend,cut_off)
        time_total+=time_taken
        total_iters+=iters
    average_time = round(time_total / itr,1)
    average_iters = round(total_iters/itr,1)
    print("total time for", itr ,"iterations:", round(time_total/60.0,1), "minutes. average:",average_time )
    print("total steps for", itr ,"iterations:", total_iters, ". average:",average_iters )

def simulate_to_death(file_num,itr=20,rend=False,inner_iter=INNER_ITR):
    sucess = 0
    for i in range(itr):
        reached = simulate_sp(file_num,inner_iter,True,rend)
        if reached: sucess+=1
    print("percent sucess:" ,round(sucess/itr *100.0,2), "%" )

def play_final(itr=300):
    simulate_sp('final',itr)


if __name__=='__main__':
    ### --- Random seed
    RANDOM_SEED = int((time.time()%10)*1000)
    print("Seed = %d" % RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    
  
    env = Hybrid_Pendulum(JOINT_COUNT, NU, dt=0.1)
    nx = env.nx
    nv = env.nv
    Q = get_critic(nx,'Q')
    Q.summary()
    Q_target = get_critic(nx,'Q_target')
    Q_target.set_weights(Q.get_weights())
    
    directory = glob.glob(FOLDER+'*')
    check = 0
    print('Loading dircetory:', FOLDER)
    print('found',len(directory), 'files in directroy')     
    # creating a matrix for controls based on JOINT_COUNT
    u_list1 = np.array(range(0, NU))
    u_list2 = np.repeat(u_list1,NU**(JOINT_COUNT-1))
    u_list = u_list2
    for i in range(JOINT_COUNT-1):
        if(i==JOINT_COUNT-2):
            u_list3 = np.tile(u_list1,NU**(JOINT_COUNT-1))            
        else:
            u_list3 = np.repeat(u_list1,NU**(JOINT_COUNT-2-i))
            u_list3 = np.tile(u_list3,NU**(i+1))        
        u_list = np.c_[u_list,u_list3]
    print('ready...')
#    simulate_folder(ITR)
        

    