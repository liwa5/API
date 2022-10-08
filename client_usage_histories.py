import meraki
import pandas as pd

def main():    
    dashboard = meraki.DashboardAPI(output_log=False)

    # Input your network_id here 
    network_id = 'L_xxxxxxxxxxxxxx' 

    #Input mac address list here, separated by ','. There shouldn't be any space between the client MAC. 
    clients = 'xx:yy:zz:hh:aa:bb,xx:yy:zz:hh:aa:cc,xx:yy:zz:hh:aa:ww'

    # Export the clients usage histories into excel file. 
    # You can either input timespan or t0/t1. timespan is in unit of second. t0 can be 31 days ago in maximum. 
    client_usage_histories_export_to_excel(dashboard, network_id, clients, timespan=3600*24*7)
    #client_usage_histories_export_to_excel(dashboard, network_id, clients, t0='2022-09-15T16:00:00Z', t1='2022-09-25T16:00:00Z')
    return
 

def client_usage_histories_export_to_excel(dashboard, network_id, clients, **kwargs):

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

    loop_count = 0
    for client_usage_histories in usage_histories:        
        # MAC address has special char ":" which cannot be used as excel sheet name. 
        sheet_name_01 = client_usage_histories['clientIp']

        client_received, client_sent, time_stamp = ([] for i in range(3))

        for usage_history in client_usage_histories['usageHistory']:
            time_stamp.append(usage_history['ts'])
            client_received.append(usage_history['received'])
            client_sent.append(usage_history['sent'])

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
                df1.to_excel(writer, sheet_name=sheet_name_01)
        else:
            # Append to an existing excel file
            with pd.ExcelWriter('client_usage_histories.xlsx', mode='a') as writer:
                df1.to_excel(writer, sheet_name=sheet_name_01)        

        loop_count += 1
        
    return

if __name__ == "__main__":
    main()
