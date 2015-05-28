#locust

##Overview
Locust is a agent + driver(s) that can be used for verification of robustness, fault-tolerance and high-availability of your system.
Locust Agent (locust) is a cross platform service running on a server(s) that hosts your system. Locust executes commands received by REST and provides a response with the results of the commands execution.
Locust Driver (driver) is a singleton for communication with Locust remotely to execute commands.

##Locust Agent
Locust Agent is a cross platform python service installed on each server where you want your system to be affected by disasters.
Locust Agent has RESTful service for interaction with Locust Driver, and Locust Agent Remote CLI.
Each Agent should have an unique secret key during installation. Each request to an Agent must contain this key.
Locust Agent is managed by a Supervisor. It restarts the Agent automatically if the Agent fails or the server reboots.



