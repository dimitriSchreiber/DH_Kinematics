import os
import numpy as np
import sympy as sp

#based on https://github.com/studywolf/blog/blob/master/SymPy/ur5.py however for a different goal

class dh_robot_config:
    ''' provides a robot class for forward and inverse kinematics, jacobian calculation based on modified DH parameters as defined in Introduction to Robotics, Mechanics and Control'''
    
    def __init__(self, DH_parameters):
        
        self.DH_parameters = {}
        
        self._Tx = {}
        self._T_inv = {}
        self._J = {}
        
        self.q = [sp.Symbol('q%i' % ii) for ii in range(self.num_joints)]
        self.dq = [sp.Symbol('dq%i' % ii) for ii in range(self.num_joints)]
        
        self.x = [sp.Symbol('x'), sp.Symbol('y'), sp.Symbol('z')] #to be used later

        
        self.initKinematicTransforms()
        
    def initKinematicTransforms(self):
        #constructs transform matrices
        pass
    
    def _calc_T(self, name):
        pass
    
    
    def _calc_Tx(self, name, x, lambdify=True):
        pass
    
    def _calc_T_inv(self, name, x, lambdify=True):
        pass
    
    def visualizeKinematics