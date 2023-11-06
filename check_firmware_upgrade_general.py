import pandas as pd
import meraki
from datetime import datetime

def main():
    # Defining your API key as a variable in source code is not recommended
    #API_KEY = MERAKI_DASHBOARD_API_KEY
    # Instead, use an environment variable as shown under the Usage section
    # @ https://github.com/meraki/dashboard-api-python/

    try:

        dict_df = pd.read_excel('config.xlsx', sheet_name=['Parameter','Network_Name'])
 
        parameters = dict_df.get('Parameter')
        org_name = parameters['Org Name'][0]
        product_for_checking = parameters['Product For Checking'][0]   
        
        if (product_for_checking != 'appliance' and product_for_checking != 'switch' and product_for_checking != 'wireless' and product_for_checking != 'switch+wireless'):
            print('Wrong product type!')
            return 
         
        dc_name_key_words = parameters['DC Name Key words'][0]
        #parameters = parameters.to_dict()
        name = dict_df.get('Network_Name')    
        network_name = name['template name or network name']


        # Open the result CSV file as output and record the time for tracking purpose. 
        date = datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")  
        if (product_for_checking == 'switch+wireless'):        
            output_file_name = 'result_switch_wireless_' + date +'.csv'
        else:
            output_file_name = 'result_' + product_for_checking +'_' + date +'.csv'
        rs = open(output_file_name, 'w', encoding='utf-8')       
        
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

        # Get the possible hub id list based on the DC name convention. Only needed for appliance.
        if (product_for_checking == 'appliance'):  
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


        # rs.write('\n Upgrade time\n')
        # for n_id in upgrade_nlist:
        #     upgrade_info = dashboard.networks.getNetworkFirmwareUpgrades(
        #     n_id
        #     )
        #     rs.write(n_id+','+upgrade_info['products']['appliance']['nextUpgrade']['toVersion']['firmware']+','+ upgrade_info['products']['appliance']['nextUpgrade']['time']+'\n')



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
                # if (product_for_checking == 'appliance'):                
                #     device_status = dashboard.organizations.getOrganizationDevicesStatuses(
                #     org_id, total_pages = 'all', networkIds = upgrade_nlist[ds*150:], productTypes = ['appliance']
                #     )
                # elif (product_for_checking == 'switch'):
                #     device_status = dashboard.organizations.getOrganizationDevicesStatuses(
                #     org_id, total_pages = 'all', networkIds = upgrade_nlist[ds*150:], productTypes = ['switch']
                #     )
                # else:
                #     device_status = dashboard.organizations.getOrganizationDevicesStatuses(
                #     org_id, total_pages = 'all', networkIds = upgrade_nlist[ds*150:], productTypes = ['wireless']
                #     )
                if (product_for_checking == 'switch+wireless'):
                    device_status = dashboard.organizations.getOrganizationDevicesStatuses(
                    org_id, total_pages = 'all', networkIds = upgrade_nlist[ds*150:], productTypes = ['switch','wireless']
                    )
                else:
                    device_status = dashboard.organizations.getOrganizationDevicesStatuses(
                    org_id, total_pages = 'all', networkIds = upgrade_nlist[ds*150:], productTypes = [product_for_checking]
                    )

                for i in device_status:
                    # print(type(i), i)
                    if(i['status']) == 'online':
                        online += 1
                    elif(i['status']) == 'offline':
                        offline += 1
                        off_sn.append([i['productType'],i['serial']])                    
                        #rs.write('Offline,'+ i['serial']+'\n')
                    elif(i['status'] == 'alerting'):
                        alerting += 1
                        al_sn.append([i['productType'],i['serial']])                    
                        #rs.write('Alerting,'+ i['serial']+'\n')
                    else:
                        dormant += 1
                        dor_sn.append([i['productType'],i['serial']])                    
                        #rs.write('Dormant,'+ i['serial']+'\n')

            elif (ds == ulist_len//150 and ulist_rem == 0):
                break

            else:
                if (product_for_checking == 'switch+wireless'):
                    device_status = dashboard.organizations.getOrganizationDevicesStatuses(
                    org_id, total_pages = 'all', networkIds = upgrade_nlist[ds*150:(ds+1)*150], productTypes = ['switch','wireless']
                    )
                else:
                    device_status = dashboard.organizations.getOrganizationDevicesStatuses(
                    org_id, total_pages = 'all', networkIds = upgrade_nlist[ds*150:(ds+1)*150], productTypes = [product_for_checking]
                    )    

                # device_status = dashboard.organizations.getOrganizationDevicesStatuses(
                # org_id, total_pages = 'all', networkIds = upgrade_nlist[ds*150:(ds+1)*150], productTypes = [product_for_checking]
                # )
                # if (product_for_checking == 'appliance'):                
                #     device_status = dashboard.organizations.getOrganizationDevicesStatuses(
                #     org_id, total_pages = 'all', networkIds = upgrade_nlist[ds*150:(ds+1)*150], productTypes = ['appliance']
                #     )
                # elif (product_for_checking == 'switch'):
                #     device_status = dashboard.organizations.getOrganizationDevicesStatuses(
                #     org_id, total_pages = 'all', networkIds = upgrade_nlist[ds*150:(ds+1)*150], productTypes = ['switch']
                #     )
                # else:
                #     device_status = dashboard.organizations.getOrganizationDevicesStatuses(
                #     org_id, total_pages = 'all', networkIds = upgrade_nlist[ds*150:(ds+1)*150], productTypes = ['wireless']
                #     )
                for i in device_status:
                    # print(type(i), i)
                    if(i['status']) == 'online':
                        online += 1
                    elif(i['status']) == 'offline':
                        offline += 1
                        off_sn.append([i['productType'],i['serial']])                    
                        #rs.write('Offline,'+ i['serial']+'\n')
                    elif(i['status'] == 'alerting'):
                        alerting += 1
                        al_sn.append([i['productType'],i['serial']])                    
                        #rs.write('Alerting,'+ i['serial']+'\n')
                    else:
                        dormant += 1
                        dor_sn.append([i['productType'],i['serial']])                    
                        #rs.write('Dormant,'+ i['serial']+'\n')
            ds += 1

        rs.write('Online devices count is ' + str(online)+'\n') 

        rs.write('\nOffline devices count is ' + str(offline) + '\n')
        for i in off_sn:
            rs.write('Offline,' + i[0]+','+i[1]+',' + '\n')

        rs.write('\nAlerting devices count is ' + str(alerting) + '\n') 
        for i in al_sn:
            rs.write('Alerting,' + i[0]+','+i[1]+',' +'\n')

        rs.write('\nDormant count is ' + str(dormant) + '\n')
        for i in dor_sn:
            rs.write('Dormant,' + i[0]+','+i[1]+',' + '\n')
            

       

        # Check VPN status from hub side only. If there is hub list, search for those only.
        # Otherwise, search for all vpn status. It took 7+ min for a very big customer org
        # to get VPN status with total pages as all. 
        # Only do the checking for appliance.
        if (product_for_checking == 'appliance'): 
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
            hub_spoke_different = []
            for x in vpn_status_data:
                if (x['vpnMode'] == 'hub'): # Only check those hubs
                    m_vpn_peers = x["merakiVpnPeers"]
                    for z in upgrade_nlist:
                        for y in m_vpn_peers:
                            if (z == y["networkId"]):
                                if(y["reachability"]) != 'reachable': 
                                    # If the VPN status shows as unreachable from hub side, double check it from spoke side as well. 
                                    # The codes ran pretty well before. On July 3rd 2023, I found an issue the VPN status shows as unreachable 
                                    # from hub side but reachable from spoke side. Therefore, I added this piece of codes. 

                                    vpn_status_spoke = dashboard.appliance.getOrganizationApplianceVpnStatuses(
                                    org_id, networkIds = y["networkId"]
                                    )
                                    for vpn_status_spoke_item in vpn_status_spoke:
                                        if (vpn_status_spoke_item['vpnMode'] == 'spoke'):
                                            spoke_vpn_peers = vpn_status_spoke_item['merakiVpnPeers']
                                            for spoke_vpn_peers_item in spoke_vpn_peers:
                                                if (spoke_vpn_peers_item['networkId'] == x['networkId']):
                                                    if (spoke_vpn_peers_item['reachability'] == 'reachable'):
                                                        # Hub shows unreachable but spoke shows reachable
                                                        hub_spoke_different.append(y["networkName"])
                                                    else:
                                                        # Both hub and spoke show VPN unreacheable
                                                        line = x["networkName"] + "," + y["networkName"] + "," + y["reachability"] + "\n"
                                                        checkboth.append(y['networkName'])
                                                        rs.write(line)
                                                        print(line)
                                                        unreachable += 1  
                                                    break             

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
                rs.write('\nBoth hubs unreachable: ' + str(len(both_unreachable)) + '\n') 
                for i in both_unreachable:
                    rs.write(i+'\n')
                rs.write('\nSingle hub unreachable: ' + str(len(single_unreachable)) + '\n')
                for i in single_unreachable:
                    rs.write(i+'\n')

                if(len(hub_spoke_different)) != 0:
                    rs.write('\nBelow spokes have unconsistent VPN status between hub and spoke. Please double check from UI.\n')
                    for item in hub_spoke_different:
                        rs.write(item+'\n')
            
        #Close the output file
        rs.close()

    except IOError as ioe:
        # If cannot find the template.csv file or cannot open the output file, you will see this error.
        # Sometimes you open the STBX_result.csv from last testing and forget to close it, you will also see the error.
        # Remember to always close the output file or save it as another file. 
        print('Cannot find config file as input or open result.csv file as output! Please check both.')

if __name__ == "__main__":
    main()
