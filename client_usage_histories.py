import meraki
import pandas as pd

def main():    
    dashboard = meraki.DashboardAPI(output_log=False)

    # Input your network_id here 
    network_id = 'L_xxxxxxxxxxxxxxxxxxx' 

    #Input mac address list here, separated by ','. There shouldn't be any space between the client MAC. 
    # The client count has limit set by API. So far I've tested 40 or 50 clients, it's OK. 200 clients failed. But I don't know
    # the extact limit yet. 
    clients = 'aa:bb:cc:dd:ee:ff,aa:bb:cc:dd:ee:ff,aa:bb:cc:dd:ee:ff,aa:bb:cc:dd:ee:ff'
    
    # Export the clients usage histories into excel file. 
    # You can either input timespan or t0/t1. timespan is in unit of second. t0 can be 31 days ago in maximum. 
    #client_usage_histories_export_to_excel_with_summary(dashboard, network_id, clients, t0='2022-09-15T16:00:00Z', t1='2022-09-25T16:00:00Z')
    client_usage_histories_export_to_excel_with_summary(dashboard, network_id, clients, timespan=3600*24*7)
    return
 

def client_usage_histories_export_to_excel_with_summary(dashboard, network_id, clients, **kwargs):

    if ('timespan' in kwargs):
        usage_histories = dashboard.networks.getNetworkClientsUsageHistories(
            network_id, clients, total_pages='all', timespan = kwargs['timespan']
        )
    elif ('t0' in kwargs and 't1' in kwargs):
        # If t1 - t0 >= 10 days, the resolution is 4 hours, otherwise it's 20 minutes. 
        usage_histories = dashboard.networks.getNetworkClientsUsageHistories(
            network_id, clients, total_pages='all', t0=kwargs['t0'], t1=kwargs['t1']
        )
    else:
        print('Wrong parameters of t0 or t1.')
        return

    # uh is a list of dictionary sr_dict. sr_dict has time_stamp as key, and value of the key is also dict containing 'received',
    # 'sent' and 'client' info. 
    uh = []
    key_list = []

    loop_count = 0
    for client_usage_histories in usage_histories:     
        sr_dict = {}   
        # MAC address has special char ":" which cannot be used as excel sheet name. 
        # Sometimes the client IP is null.
        client_Ip = client_usage_histories['clientIp']
        client_Id = client_usage_histories['clientId']

        client_received, client_sent, time_stamp = ([] for i in range(3))

        for usage_history in client_usage_histories['usageHistory']:
            # Below data structure is for creating each client sheet
            time_stamp.append(usage_history['ts'])
            client_received.append(usage_history['received'])
            client_sent.append(usage_history['sent'])

            # Below data structure is for creating the summary sheet
            sent_receive = {}
            sent_receive['received']=usage_history['received']
            sent_receive['sent']=usage_history['sent']
            if (client_Ip is None):
                sent_receive['client']=client_Id
            else:
                sent_receive['client']=client_Ip
            sr_dict[usage_history['ts']] = sent_receive
            key_list.append(usage_history['ts'])
            
        uh.append(sr_dict)
        
        # Create each client sheet
        usage_dict = {}
        if (len(time_stamp) != 0):
            usage_dict['time_stamp'] = time_stamp
        if (len(client_received) != 0):
            usage_dict['client_received'] = client_received
        if (len(client_sent) != 0):
            usage_dict['client_sent'] = client_sent
        

        df1 = pd.DataFrame(usage_dict)
        if (loop_count == 0):
            with pd.ExcelWriter('client_usage_histories.xlsx') as writer:
                if (client_Ip is None):
                    df1.to_excel(writer, sheet_name=client_Id)
                else:
                    df1.to_excel(writer, sheet_name=client_Ip)
                
        else:
            # Append to an existing excel file
            with pd.ExcelWriter('client_usage_histories.xlsx', mode='a') as writer:
                if (client_Ip is None):
                    df1.to_excel(writer, sheet_name=client_Id)
                else:
                    df1.to_excel(writer, sheet_name=client_Ip) 

        loop_count += 1       

    # Create the summary sheet
    # Get the unique time stamp list. Convert from list to dict then back to list to make sure keys are unique.
    key_list = list(dict.fromkeys(key_list))  

    summary = {}
    received_summary_list, sent_summary_list, client_online_count_list, client_list = ([] for i in range(4))    
    
    summary['time_stamp'] = key_list
    for key in key_list:
        client_online_count = 0
        received_summary = 0
        sent_summary = 0
        client_str = ''
        for uh_item in uh:
            if key in uh_item: 
                client_online_count += 1
                received_summary += uh_item[key]['received']
                sent_summary += uh_item[key]['sent']
                client_str = client_str + uh_item[key]['client'] + ','

        received_summary_list.append(received_summary)
        sent_summary_list.append(sent_summary)
        client_online_count_list.append(client_online_count)
        client_list.append(client_str)

    summary['received_summary'] = received_summary_list
    summary['sent_summary'] = sent_summary_list
    summary['online_client_count'] = client_online_count_list
    summary['client_list'] = client_list

    df1 = pd.DataFrame(summary) 
    # Append to an existing excel file
    with pd.ExcelWriter('client_usage_histories.xlsx', mode='a') as writer:
        df1.to_excel(writer, sheet_name='summary')

    return

if __name__ == "__main__":
    main()
