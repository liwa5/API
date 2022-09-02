import meraki
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt 
import numpy as np
import json
import datetime 
from datetime import timedelta
from datetimerange import DateTimeRange

def main():    

    dashboard = meraki.DashboardAPI()

    # Input your network_id here
    network_id = 'N_xxxxxxxxxxxxxxxx'  

    # resolution unit is second. 60 is the smallest, others can be 300, 600, 1800.
    resolution_a = 60

    # Unit is Mbit per second. Set limit to avoid an known bug there is occasionally extremely large value
    # that is not actual usage data. You can adjust this value to match the actual limit in your network.
    # The value larger than 3*bdw_limit will be abandoned and replaced with 0. 
    bdw_limit = 250 

    # wan_usage_history_plot_using_api_key(dashboard, network_id, t0='2022-08-29T16:00:00Z', t1='2022-09-02T16:00:00Z', 
    # reso = resolution_a, bandwidth_limit=bdw_limit)

    # t0 here can be the beginning of the timespan for the data. The maximum lookback period is 365 days from today.
    # t1 is the end of the timespan for the data. You can edit t0 and t1 here to get the data you want. 
    wan_usage_history_output_to_excel(dashboard, network_id, t0='2022-08-30T16:00:00Z', t1='2022-09-01T16:00:00Z', 
    reso = resolution_a)
    #wan_usage_history_plot_using_json_file(resolution_a, bdw_limit)
    #loss_and_latency()  



#def wan_usage_history_plot_using_api_key(dashboard, network_id, t0, t1, time_span, reso):
def wan_usage_history_plot_using_api_key(dashboard, network_id, t0, t1, reso, bandwidth_limit):
    t1_p = t1
    dict_usage_h = {}
    dict_usage_h['wan1_sent'], dict_usage_h['wan1_received'], dict_usage_h['wan1_total'], \
        dict_usage_h['wan2_sent'], dict_usage_h['wan2_received'], dict_usage_h['wan2_total'] = ([] for i in range(6))
    time_range = DateTimeRange(t0, t1)
    for value in time_range.range(datetime.timedelta(days=1)):
        if (value == time_range.end_datetime):
            continue
        t0_i = value.strftime('%Y-%m-%dT%H:%M:%SZ')
        t1_i = (value + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
        usge_history = dashboard.appliance.getNetworkApplianceUplinksUsageHistory(
            network_id, t0 = t0_i, t1 = t1_i, resolution = reso
        ) 
        for i in usge_history: 
            for j in i['byInterface']:
                if (j['sent'] != None):
                    sent = (j['sent']*8)/(1000000*reso) if (j['sent']*8)/(1000000*reso)<3*bandwidth_limit else 0
                else:
                    sent = 0
                if (j['received'] != None):
                    received = (j['received']*8)/(1000000*reso) if (j['received']*8)/(1000000*reso)<3*bandwidth_limit else 0
                else:
                    received = 0
                total = sent + received

                # if (j['interface'] == 'cellular'):
                #     dict_usage_h['cellular_sent'].append(sent)
                #     dict_usage_h['cellular_received'].append(received)
                #     dict_usage_h['cellular_total'].append(total)
                if (j['interface'] == 'wan1'):
                    dict_usage_h['wan1_sent'].append(sent)
                    dict_usage_h['wan1_received'].append(received)
                    dict_usage_h['wan1_total'].append(total)
                elif (j['interface'] == 'wan2'):
                    dict_usage_h['wan2_sent'].append(sent)
                    dict_usage_h['wan2_received'].append(received)
                    dict_usage_h['wan2_total'].append(total) 

        # Need to consider the situation when you input a date in future, usage_history len won't match the 
        # time delta between t0 and t1. It will cause error when plotting.
        if ((reso == 60 and len(usge_history) < 1440) or (reso == 300 and len(usge_history) < 288) 
            or (reso == 600 and len(usge_history) < 144) or (reso == 1800 and len(usge_history) < 48)):  
            t1_p = usge_history[-1]['endTime']        
 
    plot_data('Uplink Usage History From API', dict_usage_h, t0, t1_p, reso)
    return

def wan_usage_history_plot_using_json_file(reso, bandwidth_limit):

    # This is the jason file of uplink history.
    file = 'uplink.json'
    uplink_json_file = open(file)
    usge_history = json.load(uplink_json_file)
    time_start = usge_history[0]['startTime']
    time_end = usge_history[-1]['endTime']

    dict_usage_h = {}
    dict_usage_h['wan1_sent'], dict_usage_h['wan1_received'], dict_usage_h['wan1_total'], \
        dict_usage_h['wan2_sent'], dict_usage_h['wan2_received'], dict_usage_h['wan2_total'] = ([] for i in range(6))

    for i in usge_history: 
        for j in i['byInterface']:
            if (j['sent'] != None):
                #sent = (j['sent']*8)/(1000000*reso) # unit is Mbit per second
                sent = (j['sent']*8)/(1000000*reso) if (j['sent']*8)/(1000000*reso)<3*bandwidth_limit else 0
            else:
                sent = 0
            if (j['received'] != None):
                #received = (j['received']*8)/(1000000*reso)
                received = (j['received']*8)/(1000000*reso) if (j['received']*8)/(1000000*reso)<3*bandwidth_limit else 0
            else:
                received = 0
            total = sent + received

            # if (j['interface'] == 'cellular'):
            #     dict_usage_h['cellular_sent'].append(sent)
            #     dict_usage_h['cellular_received'].append(received)
            #     dict_usage_h['cellular_total'].append(total)
            if (j['interface'] == 'wan1'):
                dict_usage_h['wan1_sent'].append(sent)
                dict_usage_h['wan1_received'].append(received)
                dict_usage_h['wan1_total'].append(total)
            elif (j['interface'] == 'wan2'):
                dict_usage_h['wan2_sent'].append(sent)
                dict_usage_h['wan2_received'].append(received)
                dict_usage_h['wan2_total'].append(total)   

    plot_data('Uplink Usage History From ' + file + ' File', dict_usage_h, time_start, time_end, reso)
    return


def wan_usage_history_output_to_excel(dashboard, network_id, t0, t1, reso):
    wan1_received, wan1_sent, wan2_sent, wan2_received, startTime  = ([] for i in range(5))
    time_range = DateTimeRange(t0, t1)
    for value in time_range.range(datetime.timedelta(days=1)):
        if (value == time_range.end_datetime):
            continue
        t0_i = value.strftime('%Y-%m-%dT%H:%M:%SZ')
        t1_i = (value + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
        usge_history = dashboard.appliance.getNetworkApplianceUplinksUsageHistory(
            network_id, t0 = t0_i, t1 = t1_i, resolution = reso
        ) 
        for i in usge_history:
            startTime.append(i['startTime'])
            for j in i['byInterface']:                
                if (j['sent'] != None):
                    sent = (j['sent']*8)/(1000000*reso)
                else:
                    sent = 0
                if (j['received'] != None):
                    received = (j['received']*8)/(1000000*reso)
                else:
                    received = 0

                if (j['interface'] == 'wan1'):
                    wan1_sent.append(sent)
                    wan1_received.append(received) 
                elif (j['interface'] == 'wan2'):
                    wan2_sent.append(sent)
                    wan2_received.append(received)        

    usage_dict = {}
    if (len(startTime) != 0):
        usage_dict['startTime'] = startTime
    if (len(wan1_received) != 0):
        usage_dict['wan1_received'] = wan1_received
    if (len(wan1_sent) != 0):
        usage_dict['wan1_sent'] = wan1_sent
    if (len(wan2_received) != 0):   
        usage_dict['wan2_received'] = wan2_received
    if (len(wan2_sent) != 0): 
        usage_dict['wan2_sent'] = wan2_sent   

    df1 = pd.DataFrame(usage_dict)
    df1.to_excel("uplink_history_output.xlsx")  

def loss_and_latency():
    # This is the jason file of loss and latency history.
    file = "loss_and_latency.json"
    latency_json_file = open(file)
    latency_history = json.load(latency_json_file)

    time_start = latency_history[0]['startTs']
    # Reand end of time from the last item in list
    time_end = latency_history[-1]['endTs']

    dict_ll = {}
    dict_ll['latencyMs'], dict_ll['lossPercent'] = ([] for i in range(2))   
    for i in latency_history:
        dict_ll['latencyMs'].append(i['latencyMs'])
        dict_ll['lossPercent'].append(i['lossPercent'])
            
    plot_data('LatencyMs and LossPercent from ' + file + ' File', dict_ll, time_start, time_end, 60)


def plot_data(title, data, t0, t1, reso):
    fig, ax = plt.subplots(figsize=(10, 5.4), layout='constrained')
    dates = np.arange(np.datetime64(t0), np.datetime64(t1), np.timedelta64(reso, 's'))

    # Plot the data only when the key is found in dictionary and there is data in the list
    if ('wan1_sent' in data and len(data['wan1_sent']) != 0):
        ax.plot(dates, np.array(data['wan1_sent']), c = 'b', linewidth = '0.3', label = 'wan1_sent')
    if ('wan1_received' in data and len(data['wan1_received']) != 0):    
        ax.plot(dates, np.array(data['wan1_received']), c = 'r', linewidth = '0.3', label = 'wan1_received')
    if ('wan2_sent'in data and len(data['wan2_sent']) != 0):      
        ax.plot(dates, np.array(data['wan2_sent']), c = 'g', linewidth = '0.3', label = 'wan2_sent')
    if ('wan2_received'in data and len(data['wan2_received']) != 0):
        ax.plot(dates, np.array(data['wan2_received']), c = 'y', linewidth = '0.3', label = 'wan2_received')
    if ('latencyMs'in data and len(data['latencyMs']) != 0):
        ax.plot(dates, np.array(data['latencyMs']), c = 'r', linewidth = '0.3', label = 'latencyMs')
    if ('lossPercent'in data and len(data['lossPercent']) != 0):
        ax.plot(dates, np.array(data['lossPercent']), c = 'g', linewidth = '0.3', label = 'lossPercent')

    ax.set_title(title)
    # Below two lines make X date look better
    cdf = mpl.dates.ConciseDateFormatter(ax.xaxis.get_major_locator())
    ax.xaxis.set_major_formatter(cdf)

    # The label won't show without plt.legend.
    plt.legend(loc='best')
    plt.show()    


if __name__ == "__main__":
    main()
