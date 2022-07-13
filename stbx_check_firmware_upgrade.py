import meraki
import csv
from datetime import datetime

# Defining your API key as a variable in source code is not recommended
#API_KEY = MERAKI_DASHBOARD_API_KEY
# Instead, use an environment variable as shown under the Usage section
# @ https://github.com/meraki/dashboard-api-python/

dashboard = meraki.DashboardAPI()

orgs = dashboard.organizations.getOrganizations()

for x in orgs:
    if x['name'] == 'Starbucks China':
        org_id = x['id']
        print(org_id)

template_list = dashboard.organizations.getOrganizationConfigTemplates(
    org_id
)
#print(template_list)

try:
    rows = []
    with open('template.csv', newline='', encoding = 'utf-8-sig') as f:
        reader = csv.reader(f) 
        for row in reader:
            rows.append(row)

    # Open the STBX_result CSV file as output and write the 1st line
    rs = open('STBX_result.csv', 'w', encoding='utf-8')
    date = datetime.now().strftime("%Y_%m_%d-%I:%M:%S_%p")    
    print(date)
    rs.write('The scripts are run at ' + date + '\n')

    upgrade_template = []
    for i in rows:
        for j in template_list:
            if (i[0] == j['name']):
                upgrade_template.append(j['id'])
                print('Template name is ' + j['name'] + '. Template id is ' + j['id'] + '.\n')
                rs.write('Template name is ' + j['name'] + '. Template id is ' + j['id'] + '.\n')

    txt = "Matched {} templates for firmware upgrade this time.\n\n"
    print(txt.format(len(upgrade_template)))
    rs.write(txt.format(len(upgrade_template)))

    # Find the network ID list for upgrade under the specified templates
    network_list = dashboard.organizations.getOrganizationNetworks(
    org_id, total_pages='all'
    )
    
    # Get network list for upgrade 
    upgrade_nlist = []    
    for i in upgrade_template:
        for j in network_list:
            if (j['isBoundToConfigTemplate']):
                if(i == j['configTemplateId']):
                    upgrade_nlist.append(j['id'])            

    # Get the possible hub id list based on the DC name convention
    po_hub_id_list = []
    for j in network_list:
        if ("IDC_MX" in j['name']):
            po_hub_id_list.append(j['id'])

    # Validate if it's hub or not
    hub_id_list = []
    for h in po_hub_id_list:
        response = dashboard.appliance.getNetworkApplianceVpnSiteToSiteVpn(
        h
        )
        if (response['mode'] == 'hub'):
            hub_id_list.append(h)



    # Get the device statuses of those network ID list need to be upgraded. Applicance only. 
    # From my testing result, the networkIds array cannot be too big, otherwise it will return error.
    # device_status = dashboard.organizations.getOrganizationDevicesStatuses(
    # org_id, total_pages = 'all', networkIds = upgrade_nlist, productTypes = ['appliance']
    # )

    # In this way, there is no error but very slow :-(
    # device_status = dashboard.organizations.getOrganizationDevicesStatuses(
    # org_id, total_pages = 'all', productTypes = ['appliance']
    # )
    
    online = 0
    offline = 0
    alerting = 0
    dormant = 0

    ulist_len = len(upgrade_nlist)
    ulist_rem = ulist_len % 150
    ds = 0
    while (ds <= ulist_len//150):
        if (ds == ulist_len//150 and ulist_rem != 0):
            device_status = dashboard.organizations.getOrganizationDevicesStatuses(
            org_id, total_pages = 'all', networkIds = upgrade_nlist[ds*150:], productTypes = ['appliance']
            )
            for i in device_status:
                # print(type(i), i)
                if(i['status']) == 'online':
                    online += 1
                elif(i['status']) == 'offline':
                    offline += 1
                    print('Device with name as '+ i['name']+' and serial as '+i['serial']+' is offline')
                    rs.write('Device with name as '+ i['name']+' and serial as '+i['serial']+' is offline\n')
                elif(i['status'] == 'alerting'):
                    alerting += 1
                    print('Device with name as '+ i['name']+' and serial as '+i['serial']+' is alerting')
                    rs.write('Device with name as '+ i['name']+' and serial as '+i['serial']+' is alerting\n')
                else:
                    dormant += 1
                    print('Device with name as '+ i['name']+' and serial as '+i['serial']+' is dormant')
                    rs.write('Device with name as '+ i['name']+' and serial as '+i['serial']+' is dormant\n')

        elif (ds == ulist_len//150 and ulist_rem == 0):
            break

        else:
            device_status = dashboard.organizations.getOrganizationDevicesStatuses(
            org_id, total_pages = 'all', networkIds = upgrade_nlist[ds*150:(ds+1)*150], productTypes = ['appliance']
            )
            for i in device_status:
                # print(type(i), i)
                if(i['status']) == 'online':
                    online += 1
                elif(i['status']) == 'offline':
                    offline += 1
                    print('Device with name as '+ i['name']+' and serial as '+i['serial']+' is offline')
                    rs.write('Device with name as '+ i['name']+' and serial as '+i['serial']+' is offline\n')
                elif(i['status'] == 'alerting'):
                    alerting += 1
                    print('Device with name as '+ i['name']+' and serial as '+i['serial']+' is alerting')
                    rs.write('Device with name as '+ i['name']+' and serial as '+i['serial']+' is alerting\n')
                else:
                    dormant += 1
                    print('Device with name as '+ i['name']+' and serial as '+i['serial']+' is dormant')
                    rs.write('Device with name as '+ i['name']+' and serial as '+i['serial']+' is dormant\n')
        ds += 1

    print('Online devices count is ' + str(online) + '\n')
    rs.write('Online devices count is ' + str(online)+'\n')
    print('offline devices count is ' + str(offline) + '\n')
    rs.write('offline devices count is ' + str(offline) + '\n')
    print('alerting devices count is ' + str(alerting) + '\n')
    rs.write('alerting devices count is ' + str(alerting) + '\n')
    print('dormant count is ' + str(dormant) + '\n')
    rs.write('dormant count is ' + str(dormant) + '\n\n')

    #print('end')

    # Check VPN status from hub side only, otherwise it takes long time
    vpn_status_data = dashboard.appliance.getOrganizationApplianceVpnStatuses(
    org_id, networkIds = hub_id_list
    )

    rs.write("Check VPN status:\n")
    rs.write("Hub,Spoke,Status\n")

    unreachable = 0
    for x in vpn_status_data:
        if (x['vpnMode'] == 'hub'): # Only check those hubs
            m_vpn_peers = x["merakiVpnPeers"]
            for z in upgrade_nlist:
                for y in m_vpn_peers:
                    if (z == y["networkId"]):
                        if(y["reachability"]) != 'reachable': 
                            line = x["networkName"] + "," + y["networkName"] + "," + y["reachability"] + "\n"
                            rs.write(line)
                            print(line)
                            unreachable += 1  

    if(unreachable == 0):
        print('No unreachable spoke sites :-)')
        rs.write("No unreachable spoke sites.")

    #Close the output file
    rs.close()

except IOError as ioe:
    print('Cannot find template.csv file as input or open STBX_result.csv file as output! Please check both.')