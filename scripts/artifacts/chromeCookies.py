import os
import sqlite3
import textwrap

from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv, timeline, is_platform_windows, get_next_unused_name, open_sqlite_db_readonly

def get_browser_name(file_name):

    if 'brave' in file_name.lower():
        return 'Brave'
    elif 'microsoft' in file_name.lower():
        return 'Edge'
    elif 'opera' in file_name.lower():
        return 'Opera'
    elif 'android.chrome' in file_name.lower():
        return 'Chrome'
    else:
        return 'Unknown'

def get_chromeCookies(files_found, report_folder, seeker, wrap_text):
    
    for file_found in files_found:
        file_found = str(file_found)
        if not os.path.basename(file_found) == 'Cookies': # skip -journal and other files
            continue
        browser_name = get_browser_name(file_found)
        if file_found.find('app_sbrowser') >= 0:
            browser_name = 'Browser'
        elif file_found.find('.magisk') >= 0 and file_found.find('mirror') >= 0:
            continue # Skip sbin/.magisk/mirror/data/.. , it should be duplicate data??

        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()
        cursor.execute('''
        SELECT
        CASE
            last_access_utc 
            WHEN
                "0" 
            THEN
                "" 
            ELSE
                datetime(last_access_utc / 1000000 + (strftime('%s', '1601-01-01')), "unixepoch")
        END AS "last_access_utc", 
        host_key,
        name,
        value,
        CASE
            creation_utc 
            WHEN
                "0" 
            THEN
                "" 
            ELSE
                datetime(creation_utc / 1000000 + (strftime('%s', '1601-01-01')), "unixepoch")
        END AS "creation_utc", 
        CASE
            expires_utc 
            WHEN
                "0" 
            THEN
                "" 
            ELSE
                datetime(expires_utc / 1000000 + (strftime('%s', '1601-01-01')), "unixepoch")
        END AS "expires_utc", 
        path
        FROM
        cookies
        ''')

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        if usageentries > 0:
            report = ArtifactHtmlReport(f'{browser_name} - Cookies')
            #check for existing and get next name for report file, so report from another file does not get overwritten
            report_path = os.path.join(report_folder, f'{browser_name} - Cookies.temphtml')
            report_path = get_next_unused_name(report_path)[:-9] # remove .temphtml
            report.start_artifact_report(report_folder, os.path.basename(report_path))
            report.add_script()
            data_headers = ('Last Access Date','Host','Name','Value','Created Date','Expiration Date','Path')
            data_list = []
            for row in all_rows:
                if wrap_text:
                    data_list.append((row[0],row[1],(textwrap.fill(row[2], width=50)),row[3],row[4],row[5],row[6]))
                else:
                    data_list.append((row[0],row[1],row[2],row[3],row[4],row[5],row[6]))

            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()
            
            tsvname = f'{browser_name} - Cookies'
            tsv(report_folder, data_headers, data_list, tsvname)
            
            tlactivity = f'{browser_name} - Cookies'
            timeline(report_folder, tlactivity, data_list, data_headers)
        else:
            logfunc(f'No {browser_name} - Cookies data available')
        
        db.close()
