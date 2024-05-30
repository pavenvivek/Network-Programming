#!/bin/bash

# add -f to run ssh in background, parallellize
SSH="ssh -o StrictHostKeyChecking=no"

# update these entries to match your username and allocated resources!
RTR1="ezkissel@pc2.instageni.illinois.edu -p 29404"
NODE11="ezkissel@pc2.instageni.illinois.edu -p 29402"
NODE12="ezkissel@pc2.instageni.illinois.edu -p 29403"

RTR2="ezkissel@pc1.geni.it.cornell.edu -p 29692"
NODE21="ezkissel@pc1.geni.it.cornell.edu -p 29690"
NODE22="ezkissel@pc1.geni.it.cornell.edu -p 29691"

RTR3="ezkissel@pc2.instageni.idre.ucla.edu -p 26044"
NODE31="ezkissel@pc2.instageni.idre.ucla.edu -p 26042"
NODE32="ezkissel@pc2.instageni.idre.ucla.edu -p 26043"

ALL_NODES=("$RTR1" "$RTR2" "$RTR3"
	   "$NODE11" "$NODE12"
	   "$NODE21" "$NODE22"
	   "$NODE31" "$NODE32")

RTRS=("$RTR1" "$RTR2" "$RTR3")

HOSTS=("$NODE11" "$NODE12"
       "$NODE21" "$NODE22"
       "$NODE31" "$NODE32")

# Run commands below
# For example, this clears all IPs from dataplane interfaces
# and resets /etc/hosts

# NOTE: build a map of which ethX interfaces connect to each other
# before flushing!

# e.g.
# rtr1:eth3 < 10.10.100.1 - 10.10.100.3 > rtr3:eth4
# rtr1:eth4 < 10.10.101.1 - 10.10.101.2 > rtr2:eth3
# rtr2:eth4 < 10.10.102.2 - 10.10.102.3 > rtr3:eth3
for h in "${RTRS[@]}"; do
    $SSH $h "hostname; sudo ip addr flush dev eth1; \
    	    	       sudo ip addr flush dev eth2; \
		       sudo ip addr flush dev eth3; \
		       sudo ip addr flush dev eth4; \
		       head -n 1 /etc/hosts | sudo tee /etc/hosts"
done

for h in "${HOSTS[@]}"; do
    $SSH $h "hostname; sudo ip addr flush dev eth1; \
    	     head -n 1 /etc/hosts | sudo tee /etc/hosts"
done

# Next step: assign desired IPs to each site hosts and routers
# Update /etc/hosts if desired

$SSH $NODE11 "hostname; sudo ip addr add 10.10.0.11/24 dev eth1"
$SSH $NODE12 "hostname; sudo ip addr add 10.10.0.12/24 dev eth1"

$SSH $NODE21 "hostname; sudo ip addr add 10.10.1.21/24 dev eth1"
$SSH $NODE22 "hostname; sudo ip addr add 10.10.1.22/24 dev eth1"

$SSH $NODE31 "hostname; sudo ip addr add 192.168.0.31/24 dev eth1"
$SSH $NODE32 "hostname; sudo ip addr add 192.168.0.32/24 dev eth1"

$SSH $RTR1 "hostname; sudo ip addr add 10.10.0.1/24 dev eth1; \
		      sudo ip addr add 10.10.100.1/24 dev eth3; \
		      sudo ip addr add 10.10.101.1/24 dev eth4;"

$SSH $RTR2 "hostname; sudo ip addr add 10.10.1.1/24 dev eth1; \
		      sudo ip addr add 10.10.101.2/24 dev eth3; \
		      sudo ip addr add 10.10.102.2/24 dev eth4;"

$SSH $RTR3 "hostname; sudo ip addr add 192.168.0.1/24 dev eth1; \
		      sudo ip addr add 10.10.102.3/24 dev eth3; \
		      sudo ip addr add 10.10.100.3/24 dev eth4;"

# Then: add static routes on the routers and hosts to enable
# connectivity

# ...
