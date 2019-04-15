import vrep_interface_library.VREP_Python.vrep as vrep
import numpy as np
import time

''' 
Discussion on various communication types over remote API:
http://www.coppeliarobotics.com/helpFiles/en/remoteApiModusOperandi.htm#serverSideCommandHandling
http://www.coppeliarobotics.com/helpFiles/en/remoteApiConstants.htm#operationModes
http://www.coppeliarobotics.com/helpFiles/en/simulation.htm

The safest procedure is sychronous mode with streaming mode:
1) simxSynchronousTrigger
2) simxGetPingTime
3) read values using streaming mode
4) write values using non-blocking
5) restart at 1

This may be slow, depending on if the performance is acceptable I should instead use sychronous mode with streaming and disable/renable the server side (simxPauseCommunication) to make all commands be executed at the same time. This should be OK for my use since I am not performing dynamic simulations.

For synchronous mode: 

simx_opmode_buffer should be used exclusively on remote API commands that are streaming data to the client (i.e. started initially with simx_opmode_streaming), and that retrieve data from V-REP (i.e. receive if available, non blocking).

simx_opmode_oneshot should be used exclusively on remote API commands that are sending data to V-REP, and that do not expect any response from V-REP (i.e. send and forget, non blocking)

Note, there is a new B0 remote API: http://www.forum.coppeliarobotics.com/viewtopic.php?t=7795

simxCheckDistance (http://www.coppeliarobotics.com/helpFiles/en/b0RemoteApi-cpp.htm#simxCheckDistance) gives the information I want.

By breaking up the arm into seperate clusters I should be able to get the distances for each joint.

Path planning:
https://www.youtube.com/watch?v=JAs2yciPjvM
http://www.coppeliarobotics.com/helpFiles/en/pathAndMotionPlanningModules.htm
http://ompl.kavrakilab.org/blog.html
'''

class VREP_Environement():
    ''' This object defines a VREP environment '''
    def __init__(self, synchronous = False, dt = 0.05):
        self.dt = dt
        self.synchronous = synchronous
        self.robots_connected = 0
        self.robot_names = []
        self.handles_init = None
        self.clientID = None

        #Close any open connections
        vrep.simxFinish(-1)
        
        #Initiate connection to server
        self.connectToServer()


    def connectToServer(self):
        self.clientID = vrep.simxStart('127.0.0.1', 19997, True, True, 500, 5)
        
        if self.clientID != -1: # if we connected successfully
            print ('Connected to remote API server')
            time.sleep(1)
        #Setup synchronous mode or not
        if self.synchronous == True:
            print("In synchronous mode")
            vrep.simxSynchronous(self.clientID, True)
            dt = 0.001
            time.sleep(1)
            #vrep.simxSetFloatParameter(self.clientId,sim_floatparam_simulation_time_step,dt,opMode)


    def add_robot(self, robot_class):
        self.robots_connected = self.robots_connected + 1
        
        #Vrep env class stuff
        self.robot_names.append(robot_class.robot_name)
        
        #robot_class stuff
        robot_class.clientID = self.clientID
        robot_class.get_handles()
        
        #Add robot to class attributes
        setattr(self, robot_class.robot_name, robot_class)
        
    def start_simulation(self):
        if self.robots_connected == 0:
            print("no robots connected, simulation not started")
        else:
            # Set up streaming
            print("{} robot(s) connected: {}".format(self.robots_connected, self.robot_names))
            vrep.simxSetFloatingParameter(
                self.clientID,
                vrep.sim_floatparam_simulation_time_step,
                self.dt, # specify a simulation time stept
                vrep.simx_opmode_oneshot)
        
            # Start the simulation
            #vrep.simxStartSimulation(self.clientID,vrep.simx_opmode_blocking) #to increase loop speed mode is changed.
            vrep.simxStartSimulation(self.clientID,vrep.simx_opmode_oneshot_wait)


    def shutdown(self):
        vrep.simxStopSimulation(self.clientID, vrep.simx_opmode_oneshot)
        time.sleep(1)
        vrep.simxFinish(self.clientID)

class VREP_Robot():
    '''This object defines the robots in the environment'''
    def __init__(self, robot_name, handle_names, connection_type = 'nonblocking'):
        self.robot_name = robot_name
        self.handle_names = handle_names
        self.handles = None
        self.num_poses = len(handle_names) 
        self.positions = np.ones([self.num_poses,3]) #xyz
        self.orientations = np.ones([self.num_poses,4]) #xyzw
        self.connection_type = connection_type
        self.clientID = None
        self.collisionHandle = None

        #Connection type for object grabbing/setting
        if self.connection_type == 'blocking':
            self.opmode = vrep.simx_opmode_blocking
        elif self.connection_type == 'nonblocking':
            self.opmode = vrep.simx_opmode_oneshot
    def getCollisionHandle(self, name):
        returnCode, self.collision_handle = vrep.simxGetCollisionHandle(
            self.clientID, name, vrep.simx_opmode_blocking)
    def getCollisionState(self, initialize = False):
        if initialize:
            returnCode, state = vrep.simxReadCollision(self.clientID, self.collision_handle, vrep.simx_opmode_streaming)
            
        returnCode, state = vrep.simxReadCollision(
            self.clientID, self.collision_handle, vrep.simx_opmode_buffer)
        return state
    
    def get_handles(self):
        self.handles = [vrep.simxGetObjectHandle(self.clientID,
            name, vrep.simx_opmode_blocking)[1] for name in self.handle_names]
        
    def setJointPosition(self, object_name, joint_position):
        #object name is the handle for the joint
        
        if self.clientID == None:
            print("Robot not attached to VREP environment")
        else:
            vrep.simxSetJointPosition(
                self.clientID,
                object_name,
                joint_position,
                operationMode=self.opmode
                )
    
    def getJointPosition(self, object_name, initialize = False):
        #object name is the handle for the joint
        
        if self.clientID == None:
            print("Robot not attached to VREP environment")
        elif initialize:
            joint_position = vrep.simxGetJointPosition(
                self.clientID,
                object_name,
                operationMode=vrep.simx_opmode_streaming
                )    
        else:
            joint_position = vrep.simxGetJointPosition(
                self.clientID,
                object_name,
                operationMode=vrep.simx_opmode_buffer
                )  
      
            
        return joint_position
            
    def getJointMatrix(self, object_name):
        #object name is the handle for the joint
    
        if self.clientID == None:
            print("Robot not attached to VREP environment")
        else:
            joint_matrix = vrep.simxGetJointMatrix(
                self.clientID,
                object_name,
                operationMode=self.opmode
                )
        return joint_matrix
        
    def setObjectPosition(self, object_name, cartesian_position, relative2='parent'):
        #Changes what it is relative to
        if relative2 == 'parent':
            relative_handle = vrep.sim_handle_parent
        else:
            relative_handle = self.handles[self.handle_names.index(relative2)]
        
        if self.clientID == None:
            print("Robot not attached to VREP environment")
        else:
            vrep.simxSetObjectPosition(
                self.clientID,
                object_name,
                relative_handle,
                position=cartesian_position,
                operationMode=self.opmode
                )
            
    def setObjectOrientation(self, object_name, orientation, relative2='parent'):
        #Changes what it is relative to
        if relative2 == 'parent':
            relative_handle = vrep.sim_handle_parent
        else:
            relative_handle = self.handles[self.handle_names.index(relative2)]
        
        if self.clientID == None:
            print("Robot not attached to VREP environment")
        else:
            vrep.simxSetObjectOrientation(
                self.clientID,
                object_name,
                relative_handle,
                orientation,
                operationMode = self.opmode
                )
            
    def setObjectQuaternion(self, object_name, quaternion, relative2='parent'):
        #Changes what it is relative to
        if relative2 == 'parent':
            relative_handle = vrep.sim_handle_parent
        else:
            relative_handle = self.handles[self.handle_names.index(relative2)]
        
        if self.clientID == None:
            print("Robot not attached to VREP environment")
        else:
            vrep.simxSetObjectQuaternion(
                self.clientID,
                object_name,
                relative_handle,
                quaternion, #(x, y, z, w)
                operationMode = self.opmode
                )
            
    def getObjectPosition(self, object_name, relative2='parent',initialize=False):
        #Changes what it is relative to
        if relative2 == 'parent':
            relative_handle = vrep.sim_handle_parent
        else:
            relative_handle = self.handles[self.handle_names.index(relative2)]
        
        if self.clientID == None:
            print("Robot not attached to VREP environment")
        elif initialize:
            cartesian_position = vrep.simxGetObjectPosition(
                self.clientID,
                object_name,
                relative_handle,
                vrep.simx_opmode_streaming
                )
        else:
            cartesian_position = vrep.simxGetObjectPosition(
                self.clientID,
                object_name,
                relative_handle,
                vrep.simx_opmode_buffer
                )# !CHANGE OPMODE from operationMode=self.opmode
        return cartesian_position
    
    
    def getObjectOrientation(self, object_name, relative2='parent',initialize=False):
        #Changes what it is relative to
        if relative2 == 'parent':
            relative_handle = vrep.sim_handle_parent
        else:
            relative_handle = self.handles[self.handle_names.index(relative2)]
            
        if self.clientID == None:
            print("Robot not attached to VREP environment")
        elif initialize:
            orientation = vrep.simxGetObjectOrientation(
                self.clientID,
                object_name,
                relative_handle,
                vrep.simx_opmode_streaming
                )# !CHANGE OPMODE
        else:
            orientation = vrep.simxGetObjectOrientation(
                self.clientID,
                object_name,
                relative_handle,
                vrep.simx_opmode_buffer
                )# !CHANGE OPMODE from operationMode=self.opmode
        return orientation
    
    
    def getObjectQuaternion(self, object_name, relative2='parent',initialize=False):
        #Changes what it is relative to
        if relative2 == 'parent':
            relative_handle = vrep.sim_handle_parent
        else:
            relative_handle = self.handles[self.handle_names.index(relative2)]
            
        if self.clientID == None:
            print("Robot not attached to VREP environment")
        elif initialize:
            quaternion = vrep.simxGetObjectQuaternion(
                self.clientID,
                object_name,
                relative_handle,
                vrep.simx_opmode_streaming
                )# !CHANGE OPMODE
        else:
            quaternion = vrep.simxGetObjectQuaternion(
                self.clientID,
                object_name,
                relative_handle,
                vrep.simx_opmode_buffer
                )# !CHANGE OPMODE from operationMode=self.opmode
        return quaternion #(x, y, z, w)?

    def GetObjectGroupData(self, object_name, parameter): #does not work
        if self.clientID == None:
            print("Robot not attached to VREP environment")
            return -1
        else:
            return vrep.simxGetObjectGroupData(
                self.clientID,
                object_name,
                parameter,
                operationMode = self.opmode
                )