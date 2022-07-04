import json
import csv

# Import the vpn status data from 1.json file 
# Make sure to use utf-8 to read json file including Chinese characters
api_json_file = open("1.json", encoding='utf-8')
vpn_status_data = json.load(api_json_file)

# Open the STBX_result CSV file as output and write the 1st line
rs = open('STBX_result.csv', 'w', encoding='utf-8')
rs.write("Network 1,Network 2,Status\n")

try:
    # If there is spoke.csv file existing, read the network names from it. And
    # only search for unreachable peers within this range.
    rows = []
    with open('spoke.csv', newline='') as f:
        reader = csv.reader(f) 
        for row in reader:
            rows.append(row)

    for x in vpn_status_data:
        if ("IDC_MX" in x["networkName"]):
            m_vpn_peers = x["merakiVpnPeers"]
            for z in rows:
                for y in m_vpn_peers:
                    if (z[0] == y["networkName"]):
                        if(y["reachability"]) != 'reachable': 
                            line = x["networkName"] + "," + y["networkName"] + "," + y["reachability"] + "\n"
                            rs.write(line)
                            print(line)   

except IOError as ioe:
    # If there is no spoke.csv file, search for all networks uneachable from networks have name as IDC_MX   
    for x in vpn_status_data:
        if ("IDC_MX" in x["networkName"]):
            m_vpn_peers = x["merakiVpnPeers"]
            for y in m_vpn_peers:
                if(y["reachability"]) != 'reachable':  
                    line = x["networkName"] + "," + y["networkName"] + "," + y["reachability"] + "\n"
                    rs.write(line)
                    print(line)   

#Close the output file
rs.close()
       

