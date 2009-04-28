#!/usr/bin/env python2.5

# Copyright 2008 bjweeks, MZMcBride

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import re
import MySQLdb
import wikitools
import settings

report_title = settings.rootpage + 'Excessively long user blocks'

report_template = '''
Excessively long (more than two years) blocks of users; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! User
! Admin
! Timestamp
! Expiry
! Reason
|-
%s
|}
'''

wiki = wikitools.Wiki(settings.apiurl)
wiki.login(settings.username, settings.password)

conn = MySQLdb.connect(host=settings.host, db=settings.dbname, read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* excessiveusers.py SLOW_OK */
SELECT
  ipb_address,
  ipb_by_text,
  ipb_timestamp,
  ipb_expiry,
  ipb_reason
FROM ipblocks
WHERE ipb_expiry > DATE_FORMAT(DATE_ADD(NOW(),INTERVAL 2 YEAR),'%Y%m%d%H%i%s')
AND ipb_expiry != "infinity"
AND ipb_user != 0;
''')

i = 1
output = []
for row in cursor.fetchall():
    ipb_address = u'[[User talk:%s|]]' % unicode(row[0], 'utf-8')
    ipb_by_text = u'%s' % unicode(row[1], 'utf-8')
    ipb_timestamp = u'%s' % unicode(row[2], 'utf-8')
    ipb_expiry = u'%s' % unicode(row[3], 'utf-8')
    ipb_reason = row[4]
    if ipb_reason:
        ipb_reason = u'<nowiki>%s</nowiki>' % unicode(ipb_reason, 'utf-8')
    else:
        ipb_reason = ''
    table_row = u'''| %d
| %s
| %s
| %s
| %s
| %s
|-''' % (i, ipb_address, ipb_by_text, ipb_timestamp, ipb_expiry, ipb_reason)
    output.append(table_row)
    i += 1

cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
rep_lag = cursor.fetchone()[0]
current_of = (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')

report = wikitools.Page(wiki, report_title)
report_text = report_template % (current_of, '\n'.join(output))
report_text = report_text.encode('utf-8')
report.edit(report_text, summary=settings.editsumm, bot=1)

cursor.close()
conn.close()