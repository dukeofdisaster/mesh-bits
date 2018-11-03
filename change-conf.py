import subprocess
import os
import sys
import fileinput
import json

# much of this initial functionality taken from:
# 	-https://github.com/cjdelisle/cjdns/blob/master/contrib/python/cjdnsadminmaker.py
# Needed to adopt it to add the ability to dynamically add entries to the config
# as part of some ansible automation I was tinkering with.
cjdroutelocations = ["/opt/cjdns",
    "~/cjdns",
    "~/cjdns-git",
		"/usr/local/opt/cjdns"]

cjdroutelocations = ["/opt/cjdns",
    "~/cjdns",
    "~/cjdns-git",
		"/usr/local/opt/cjdns"]

cjdroutelocations += os.getenv("PATH").split(":")


def find_cjdroute_bin():
    for path in cjdroutelocations:
        path = os.path.expanduser(path) + "/cjdroute"
        if os.path.isfile(path):
            return path

    print "Failed to find cjdroute"
    print "Please tell me where it is"
    return raw_input("ie. <cjdns git>/cjdroute: ")


# for consistency we should assume that this key will always
# get written into /tmp by the ansible script and probably deleted  after it has
# been written into the conf since we assume the field name 'publicKey' will 
# stay the same we just need to extract the key value, so we can save it to 
# a variable
key = ''
with open("/tmp/key.txt", "r") as key_: 
	content= key_.readlines()
	stripped = content[0].strip()
	key = stripped[18:72]
	print(stripped[18:72])

def load_clean_conf(conf):
	print "Loading as valid json with --cleanconf: " + conf
	cjdroute = find_cjdroute_bin()
	print "Using: " + cjdroute
	process = subprocess.Popen([cjdroute, "--cleanconf"], stdin=open(conf), stdout=subprocess.PIPE)
	try:
		return json.load(process.stdout)
	except ValueError:
		print "Failed to parse, check: "
		print "-" * 8
		print "{} --cleanconf < {}".format(cjdroute, conf)
		print "-" * 8
		sys.exit(1)

# Assumes standardized location of cjdroute.conf; not true on all platforms
conf_json = load_clean_conf("/etc/cjdroute.conf")

# Below we manipulate the last added ip address  in allowedConnections which is 1/3 of the 
# data we need to create a new entry.	
lastip = conf_json['router']['ipTunnel']['allowedConnections'][-1]['ip4Address']
lastoctet = lastip.split('.')[-1]
lastiparray = lastip.split('.')

# Noww that we have the last octet and the values split, we can increment
# the last octet and then join the values back together in a string
newoctet = str(int(lastoctet)+1)
lastiparray[-1] = newoctet
newipstring = '.'.join(lastiparray)

# Now that we have the relevant pieces of data we can append conf_json 
# then write it to file and reload ( which will take place in the ansible script.
# Note this assumes we'll alwas want the new addition to be /24, but whatev.
conf_json['router']['ipTunnel']['allowedConnections'].append({'publicKey': key, 'ip4Address': newipstring, 'ip4Prefix': 24})
#print json.dumps(conf_json, indent=2)
with open('testdump.json', 'w') as outfile:
	outfile.write(json.dumps(conf_json, indent=2))
	outfile.close()
