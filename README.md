check_firmware_upgrade_general.py
This file is to check device status (online/offline/dormant, MX only) and AutoVPN status within a given scope of networks or templates. 

Use case: Run it before and after the firmware upgrade, compare the results delta to identify whether any MX become offline or AutoVPN connection become unreacheable after firmware upgrade. 

Input: config.xlxs contains org name, DC name key word (optional), template list or network name list

Output: result.csv

uplink_history_export.py
This file is to export MX uplink history to excel sheet or draw picture. 

Use case: Review MX uplink history to plan for bandwidth upgrade, etc. 
Input: N/A
Output: Picture of excel file depends on which funciton is called.

client_usage_histories.py
This file is to export client usage histories to excel sheet. 
Use case: Review client usage histories. 
Input: N/A
Output: client_usage_histories.xlsx
