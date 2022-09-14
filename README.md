# Kistler-maintenance
Server side script that checks the need of Kistler pressing unit maintenance on a PLC request

Use case:
Assembly line with a Kistler pressing unit that produces NOK parts because of gradual deterioration of pressing properties and therefore the need for maintenance/lubrication.

The problem that the script solves is when is the right time to perform maintenance.

When the pressing is done, PLC asks script if it is maintenance time.

The script downloads the newest pressing record a perform evaluation based on the moving average of the last two pieces.

Then the script replies whether or not is right time to PLC.

Directory structure:
\Watchdog-server-FTP.py (script)
\conf\OiLog.csv (log of records when the maintenance is needed)
\conf\Watchdog.txt (limit settings)
\notOK\*.csv (subdirectory with NOK operations)
