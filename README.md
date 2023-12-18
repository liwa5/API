Use case #1: Firmware upgrade check

Files used:
check_firmware_upgrade_general.py
requirements.txt
config.xlsx

We observe some failures could occasionally happen after the firmware upgrade:
1. Device fails to upgrade to the configured version
2. Device becomes offline
3. The MX is online but the AutoVPN is down.
The code is to check device status (online/offline/dormant) and AutoVPN status (MX only) within a given scope of networks or templates (usually the networks and/or templates you'd like to upgrade during a maitenance window), as well as whether the device is running the configured version.

How to use it?
Run it before and after the firmware upgrade, compare the results difference to identify whether any device becomes offline or AutoVPN connection becomes unreacheable after firmware upgrade, or any device is not running the configured version.
You can run it right before and after the firmware upgrade. Or you can run it before the firmare upgrade to get a baseline. If you don't have any resource to run it right after the firmware upgrade(the firmware upgrade usually happens in the midnight), you can at least run it as soon as possible when you have the resource (e.g. in the early morning), identify the potential issues and take pro-active actions. 

Input: config.xlxs 
Put this xlxs file in the same directory as the check_firmware_upgrade_general.py file. Input your org name, DC name key word (optional), template list or network name list, as well as which product you'd like to check onto this xlxs file. 

Output: result.csv
The code will generate an output file such as result_switch_wireless_2023_12_18-02_29_02_PM.csv in the same directory. The naming convention is result_<product type>_<the time when the code is run>.csv



The below two use cases haven't been worked on for a while. Feel free to test as you want. 

Use case #2: Review MX uplink history to plan for bandwidth upgrade

uplink_history_export.py
This file is to export MX uplink history to excel sheet or draw picture. 

Input: N/A
Output: Picture of excel file depends on which funciton is called.

Use case #3: Review client usage histories

client_usage_histories.py
This file is to export client usage histories to excel sheet. 

Input: N/A
Output: client_usage_histories.xlsx
