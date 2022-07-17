from tabnanny import check
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
    with open('template.csv', newline='', encoding = 'utf-8') as f:
    #with open('template.csv', newline='', encoding = 'utf-8-sig') as f:
    #with open('template.csv', newline='') as f:
    # I've met the issue that the template name copied from somewhere has the mixed en-coding issue
    # and the scipts wil crash here. Make sure the encoding of the template network name is correct. 
        reader = csv.reader(f)
        for row in reader:
            rows.append(row)

    # Open the STBX_result CSV file as output and record the time for tracking purpose. 
    rs = open('STBX_result.csv', 'w', encoding='utf-8')
    date = datetime.now().strftime("%Y_%m_%d-%I:%M:%S_%p")    
    print(date)
    rs.write(date + '\n')

    upgrade_template = []
    for i in rows:
        for j in template_list:
            if (i[0] == j['name']):
                upgrade_template.append(j['id'])
                #print('Template name is ' + j['name'] + '. Template id is ' + j['id'] + '.\n')
                rs.write('Template id,' + j['id'] + '\n')

    # upgrade_template = []
    # for i in rows:
    #     for j in template_list:
    #         if isinstance(i, list) == True: # Check if rows has sub list in it
    #             for sub_list in i:
    #                 print(type(sub_list))
    #                 if (sub_list == j['name']):
    #                     upgrade_template.append(j['id'])
    #                     print('Template name is ' + j['name'] + '. Template id is ' + j['id'] + '.\n')
    #                     rs.write('Template name is ' + j['name'] + '. Template id is ' + j['id'] + '.\n')
    #         else:
    #             if (i[0] == j['name']):
    #                 upgrade_template.append(j['id'])
    #                 print('Template name is ' + j['name'] + '. Template id is ' + j['id'] + '.\n')
    #                 rs.write('Template name is ' + j['name'] + '. Template id is ' + j['id'] + '.\n')


    txt = "Matched {} template for firmware upgrade\n\n"
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
    # Therefore, I have to divide the network id list into groups. Each group has 150 items. There is no error and is also
    # fast in this way. The codes look ugly :-) May need a function to replace it later.
    
    online = 0
    offline = 0
    alerting = 0
    dormant = 0
    off_sn = []
    al_sn = []
    dor_sn = []

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
                    off_sn.append(i['serial'])                    
                    #rs.write('Offline,'+ i['serial']+'\n')
                elif(i['status'] == 'alerting'):
                    alerting += 1
                    al_sn.append(i['serial'])                    
                    #rs.write('Alerting,'+ i['serial']+'\n')
                else:
                    dormant += 1
                    dor_sn.append(i['serial'])                    
                    #rs.write('Dormant,'+ i['serial']+'\n')

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
                    off_sn.append(i['serial'])                    
                    #rs.write('Offline,'+ i['serial']+'\n')
                elif(i['status'] == 'alerting'):
                    alerting += 1
                    al_sn.append(i['serial'])                    
                    #rs.write('Alerting,'+ i['serial']+'\n')
                else:
                    dormant += 1
                    dor_sn.append(i['serial'])                    
                    #rs.write('Dormant,'+ i['serial']+'\n')
        ds += 1

    rs.write('Online devices count is ' + str(online)+'\n') 

    rs.write('\nOffline devices count is ' + str(offline) + '\n')
    for i in off_sn:
        rs.write('Offline,' + i + '\n')

    rs.write('\nAlerting devices count is ' + str(alerting) + '\n') 
    for i in al_sn:
        rs.write('Alerting,' + i + '\n')

    rs.write('\nDormant count is ' + str(dormant) + '\n')
    for i in dor_sn:
        rs.write('Dormant,' + i + '\n')

    # Check VPN status from hub side only, otherwise it takes so long time for a big org with many MX.
    vpn_status_data = dashboard.appliance.getOrganizationApplianceVpnStatuses(
    org_id, networkIds = hub_id_list
    )

    rs.write("\nCheck VPN status:\n")
    rs.write("Hub,Spoke,Status\n")

    unreachable = 0
    checkboth = []
    for x in vpn_status_data:
        if (x['vpnMode'] == 'hub'): # Only check those hubs
            m_vpn_peers = x["merakiVpnPeers"]
            for z in upgrade_nlist:
                for y in m_vpn_peers:
                    if (z == y["networkId"]):
                        if(y["reachability"]) != 'reachable': 
                            line = x["networkName"] + "," + y["networkName"] + "," + y["reachability"] + "\n"
                            checkboth.append(y['networkName'])
                            rs.write(line)
                            print(line)
                            unreachable += 1  

    if(unreachable == 0):
        print('No unreachable spoke sites :-)')
        rs.write("No unreachable spoke sites.")
    else:
        both_unreachable = []
        single_unreachable = []
        checkboth_no_dup = list(dict.fromkeys(checkboth))
        for i in checkboth_no_dup:
            count  = 0
            for j in checkboth:
                if (j == i):
                    count += 1
            if (count == 2):
                both_unreachable.append(i)
            else:
                single_unreachable.append(i)
        rs.write('\nBoth hubs unreachable\n')
        for i in both_unreachable:
            rs.write(i+'\n')
        rs.write('\nSingle hub unreachable\n')
        for i in single_unreachable:
            rs.write(i+'\n')
        
    #Close the output file
    rs.close()

except IOError as ioe:
    # If cannot find the template.csv file or cannot open the output file, you will see this error.
    # Sometimes you open the STBX_result.csv from last testing and forget to close it, you will also see the error.
    # Remember to always close the output file or save it as another file. 
    print('Cannot find template.csv file as input or open STBX_result.csv file as output! Please check both.')