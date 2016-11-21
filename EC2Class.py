#Author:    Scott Pavlow
#Date:      Nov 14, 2016

from __future__ import print_function
import boto3
import math
ec2 = boto3.resource('ec2')

print('Loading function')


class EC2Driver(object):

        """ This class is designed to determine if new AWS instances need to be
            created or terminated based on the number of users passed into it.
            Use the SubmitNoUsers method and provide the number of users, and the
            machine type.  Keep in mind so far only Virtualization type that will work
            is paravirtual.  If it is not, you will receive an error.
            Example use:  SubmitNoUsers(500, 'ami-baab0fda')"""

        def start_EC2(self, Instance, MaxCount):
            """Start new instances"""
            ec2.create_instances(ImageId=Instance, MinCount=1, MaxCount=MaxCount,
                                 InstanceType='t1.micro')

        def get_current_instances(self, instance_type='t1.micro'):
            """Return a list of machines from oldest to newest."""
            ReturnValue = {}
            instance_filters = [{'Name': 'instance-state-name', 'Values': ['running']}]
            instances = ec2.instances.filter(Filters=instance_filters)
            for instance in instances:
                #Were checking for a type of t1.micro here for testing purposes.
                if instance.instance_type == instance_type:
                    ReturnValue[instance.id] = instance.launch_time
            #Returns a list if keys sorted by oldest first.
            return sorted(ReturnValue.keys(), key=lambda p: ReturnValue[p], reverse=False)


        def kill_EC2(self, InstanceIds):
            """Kill EC2 instances by there instanceID"""
            ec2.instances.filter(InstanceIds=InstanceIds).stop()
            ec2.instances.filter(InstanceIds=InstanceIds).terminate()


        def round_to_nearest_100(self, Number):
            """Round a given number to the nearest 100"""
            return int(math.ceil(Number / 100.0)) * 100


        def submit_no_users(self, NumUsers, InstanceType):
            """Determine if instances need to be added or removed."""
            #Percentage buffer we decide on to insulate against spikes.
            Buffer = .1
            #Calculate the Number of users with buffer added.
            TargetNumber = NumUsers + (NumUsers * Buffer)

            #Round to nearest 100 users.
            RoundedToNearest100 = self.round_to_nearest_100(TargetNumber)
            #Get the current instances info
            Instances = self.get_current_instances()
            #Get current number of servers running.
            CurrentNoOfServers = len(Instances)
            #Each server is capable of serving 100 users.
            CurrentCapacity = CurrentNoOfServers * 100
            #Output Status Data.
            print ('CurrentNoOfServers: ' + str(CurrentNoOfServers))
            print ('CurrentCapacity: ' + str(CurrentCapacity))
            print ('TargetNumber: ' + str(TargetNumber))
            print ('RoundedToNearest100: ' + str(RoundedToNearest100))
            #Eval current capacity to determine if more resources are needed,
            #or if some resources need to be terminated.
            if CurrentCapacity < RoundedToNearest100:
                #Calculate number of additional resources.
                AdditionalResourcesNeeded = (RoundedToNearest100 - CurrentCapacity) / 100
                print ('AdditionalResourcesNeeded: ' + str(AdditionalResourcesNeeded))
                self.start_EC2(InstanceType, AdditionalResourcesNeeded)
                return 'Instances add are: ' + str(AdditionalResourcesNeeded)

            #Calculate any resource that need to be removed.
            if CurrentCapacity > RoundedToNearest100:
                ResourcesThatNeedToBeRemoved = (CurrentCapacity - RoundedToNearest100) / 100
                print ('ResourcesThatNeedToBeRemoved: ' + str(ResourcesThatNeedToBeRemoved))
                InstancesToRemove = Instances[0:ResourcesThatNeedToBeRemoved]
                print (InstancesToRemove)
                self.kill_EC2(InstancesToRemove)
                return 'Instances removed are: ' + str(InstancesToRemove)

def SubmitNoUsers(dictarg, context):
    EC2 = EC2Driver()
    EC2.submit_no_users(dictarg['users'], dictarg['image'])


SubmitNoUsers({'users':300, 'image':'ami-baab0fda'}, None)
