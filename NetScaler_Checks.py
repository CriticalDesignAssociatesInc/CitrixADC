import json
import requests, sys, base64, collections
import urllib3
import csv
import getpass

#Get a list of LB vServers, Service Group Bindings, Server Group members, 
#Service Group Member Ports, Service Group Monitors, Service Group Monitor HTTP Requests, LB vServer Status, Backend Server Status
#Get list of LB vServers
#Loop through each LB vServer to get Service Group Binding
#Loop though each Service Group to get Service Group Members and monitors
#Loop though each monitor to get HTTP Request parameter
#Write output to .csv

#Disable SSL Warnings if cert is untrusted
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#User input server IP Address
NITRO_SERVER=input("Server IP: ")

#User input username
NITRO_USER=input("Username: ")

#User input password
try:
    NITRO_PWD=getpass.getpass()
except Exception as error:
    print ('ERROR',error)


#Open a .csv file and create a new line 
with open('monitor_status.csv','w', newline='') as f:
    writer = csv.writer(f)

    #write headings for each column
    writer.writerow(['vServer Name','ServiceGroup Name', 'Server Name', 'Port', 'Monitor Name', 'HTTP Request', 'LB VIP Status', 'Server Status', 'Backend Server State'])

    #send first request to NITRO API to get list of Load Balancing vServser
    lbvs_response=requests.get("https://%s/nitro/v1/config/lbvserver"%(NITRO_SERVER),auth=(NITRO_USER, NITRO_PWD),verify=False)
    
    lbvs_data=json.loads(lbvs_response.text)
    
    #for each lbvserver in lbvs_data get the name and current state
    for j in lbvs_data['lbvserver']:
        lbvs_name=j['name']
        lbvs_stat=j['curstate']

        #send request to get Service Group bindings for each Load Balancing vServer
        svg_response=requests.get("https://%s/nitro/v1/config/lbvserver_servicegroup_binding/%s"%(NITRO_SERVER,lbvs_name),auth=(NITRO_USER, NITRO_PWD),verify=False)

        svg_data = json.loads(svg_response.text)

        #if there is a Service Group binding, get the monitor name and Service Group members
        if 'lbvserver_servicegroup_binding' in svg_data:
            for k in svg_data['lbvserver_servicegroup_binding']:

                svg_grpname=k["servicegroupname"]
                svgmon_response=requests.get("https://%s/nitro/v1/config/servicegroup_lbmonitor_binding/%s"%(NITRO_SERVER,svg_grpname),auth=(NITRO_USER, NITRO_PWD),verify=False)
                svgmon_data=json.loads(svgmon_response.text)

                member_response=requests.get("https://%s/nitro/v1/config/servicegroup_servicegroupmember_binding/%s"%(NITRO_SERVER,svg_grpname),auth=(NITRO_USER, NITRO_PWD),verify=False)
                mr_data=json.loads(member_response.text)

            #if there is a monitor bound, get the port, backend server name, and backend server state
            if 'servicegroup_lbmonitor_binding' in svgmon_data:

                for l in mr_data['servicegroup_servicegroupmember_binding']:

                    port=str(l["port"])
                    svrname=l["servername"]
                    svrip=l["ip"]
                    svrstate=l["svrstate"]
                    svrport=":"+port

                    #for each monitor, get the monitor name 
                    for m in svgmon_data['servicegroup_lbmonitor_binding']:

                        monname=m["monitor_name"]
                        mon_response=requests.get("https://%s/nitro/v1/config/lbmonitor/%s"%(NITRO_SERVER,monname),auth=(NITRO_USER, NITRO_PWD),verify=False)
                        mon_data=json.loads(mon_response.text)

                        for n in mon_data["lbmonitor"]:

                            #if there is a http request field
                            if 'httprequest' in mon_data["lbmonitor"][0]:
                                
                                httpreq=n['httprequest']
                                mon_sec=n['secure']
                                httpreq=str.replace(httpreq,'GET ','')
                                   
                                if( mon_sec == 'NO'):
                                    #create test uri 
                                    test_uri='http://'+svrip+svrport+httpreq
                                    response = requests.get(test_uri)
                                    
                                    if(response == '<Response [200]>'):
                                        backend = 'UP'
                                        writer.writerow([lbvs_name,svg_grpname,svrname,port,monname,httpreq,lbvs_stat,svrstate,backend])
                                    else:
                                        backend = 'DOWN'
                                        writer.writerow([lbvs_name,svg_grpname,svrname,port,monname,httpreq,lbvs_stat,svrstate,backend])
                                else:
                                    test_uri='https://'+svrip+svrport+httpreq
                                    response = requests.get(test_uri)
                                    
                                    if(response == '<Response [200]>'):
                                        backend = 'UP'
                                        writer.writerow([lbvs_name,svg_grpname,svrname,port,monname,httpreq,lbvs_stat,svrstate,backend])
                                    else:
                                        backend = 'DOWN'
                                        writer.writerow([lbvs_name,svg_grpname,svrname,port,monname,httpreq,lbvs_stat,svrstate,backend])
                                    
 
                            #else assign httpreq to none
                            else:

                                httpreq='N/A'
                                backend='N/A'
                                #write to .csv file 
                                writer.writerow([lbvs_name,svg_grpname,svrname,port,monname,httpreq,lbvs_stat,svrstate,backend])

            else:

                monname='tcp'
                httpreq='N/A'
                backend='N/A'

                for l in mr_data['servicegroup_servicegroupmember_binding']:

                    port=str(l["port"])
                    svrname=l["servername"]
                    svrstate=l["svrstate"]

                    writer.writerow([lbvs_name,svg_grpname,svrname,port,monname,httpreq,lbvs_stat,svrstate,backend])

        else:
            port ='N/A'
            svrname='N/A'
            httpreq='N/A'
            svg_grpname='N/A'
            monname='N/A'
            svrstate='N/A'
            backend='N/A'
            writer.writerow([lbvs_name,svg_grpname,svrname,port,monname,httpreq,lbvs_stat,svrstate,backend])
            
            
            
            
            
