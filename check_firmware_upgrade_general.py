import pandas as pd
import meraki
import csv, numpy
from datetime import datetime

def main():
    # Defining your API key as a variable in source code is not recommended
    #API_KEY = MERAKI_DASHBOARD_API_KEY
    # Instead, use an environment variable as shown under the Usage section
    # @ https://github.com/meraki/dashboard-api-python/

    try:
        # rows = []
        # with open('network_or_template.csv', newline='', encoding = 'utf-8') as f:
        # #with open('template.csv', newline='', encoding = 'utf-8-sig') as f:
        # #with open('template.csv', newline='') as f:
        # # I've met the issue that the template name copied from somewhere has the mixed en-coding issue
        # # and the scipts wil crash here. Make sure the encoding of the template network name is correct. 
        #     reader = csv.reader(f)
        #     for row in reader:
        #         rows.append(row)

        dict_df = pd.read_excel('config.xlsx', sheet_name=['Parameter','Network_Name'])

        parameters = dict_df.get('Parameter')
        org_name = parameters['Org Name'][0]
        dc_name_key_words = parameters['DC Name Key words'][0]
        #parameters = parameters.to_dict()
        name = dict_df.get('Network_Name')    
        network_name = name['template name or network name']


        # Open the result CSV file as output and record the time for tracking purpose. 
        rs = open('result.csv', 'w', encoding='utf-8')
        date = datetime.now().strftime("%Y_%m_%d-%I:%M:%S_%p")    
        print(date)
        rs.write(date + '\n')

        # api_key = '11d6b66ffacd8f38e84d20973daf813585e75e75'
        # dashboard = meraki.DashboardAPI(api_key)
        dashboard = meraki.DashboardAPI()

        orgs = dashboard.organizations.getOrganizations()

        foundOrg = False
        for x in orgs:
            if x['name'] == org_name:
                foundOrg = True
                org_id = x['id']
                print(org_id)
                break

        if (foundOrg):
            template_list = dashboard.organizations.getOrganizationConfigTemplates(
                org_id
            )
        else:
            rs.write('Cannot find org with specified name.')
            rs.close()
            return

        upgrade_template = []
        for i in network_name:
            for j in template_list:
                if (i == j['name']):
                    upgrade_template.append(j['id'])
                    #print('Template name is ' + j['name'] + '. Template id is ' + j['id'] + '.\n')
                    rs.write('Template id,' + j['id'] + '\n')

        txt = "Matched {} template for status check\n\n"
        print(txt.format(len(upgrade_template)))
        rs.write(txt.format(len(upgrade_template)))

        # Find the network ID list for upgrade under the specified templates
        network_list = dashboard.organizations.getOrganizationNetworks(
        org_id, total_pages='all'
        )
        
        # Get network list for upgrade which are bound to template
        upgrade_nlist = []    
        for i in upgrade_template:
            for j in network_list:
                if (j['isBoundToConfigTemplate']):
                    if(i == j['configTemplateId']):
                        upgrade_nlist.append(j['id'])        

        single_net = 0
        for i in network_name:
            for j in network_list:
                if (i == j['name']):
                    upgrade_nlist.append(j['id'])
                    single_net += 1
                    rs.write('Network id,' + j['id'] + '\n')
        rs.write('Matched '+str(single_net)+' network for status check\n\n')    

        # Get the possible hub id list based on the DC name convention
        po_hub_id_list = []
        hub_id_list = []
        if(isinstance(dc_name_key_words, str)):
            for j in network_list:
                if (dc_name_key_words in j['name']):
                    po_hub_id_list.append(j['id']) 
            # Validate if it's hub or not              
            for h in po_hub_id_list:
                response = dashboard.appliance.getNetworkApplianceVpnSiteToSiteVpn(h)
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

       

        # Check VPN status from hub side only. If there is hub list, search for those only.
        # Otherwise, search for all vpn status. It took 7+ min for an org like Starbucks China
        # to get VPN status with total pages as all. 
        if(len(hub_id_list) == 0):
            try:
                vpn_status_data = dashboard.appliance.getOrganizationApplianceVpnStatuses(
                org_id, total_pages='all'
                )
            except:
                rs.write('\nVPN not enabled in this org.\n')
                rs.close()
                return
        else:
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
            # To find those networks unreachable from both hubs and those unreachable from single hub
            # In this way, it's much easier to compare the results if you run the scipt before the 
            # firmware and after the firmware upgrade.
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
        print('Cannot find config file as input or open result.csv file as output! Please check both.')

if __name__ == "__main__":
    main()