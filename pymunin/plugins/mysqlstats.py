#!/usr/bin/env python
"""mysqlstats - Munin Plugin to monitor stats for MySQL Database Server.

Requirements
  - Access permissions for MySQL Database.


Wild Card Plugin - No


Multigraph Plugin - Graph Structure
    - mysql_connections
    - mysql_traffic
    - mysql_slowqueries
    - mysql_rowmodifications
    - mysql_rowreads
    - mysql_tablelocks
    - mysql_threads
    - mysql_commits_rollbacks
   

Environment Variables

  host:           MySQL Server IP. 
                  (Defaults to UNIX socket if not provided.)
  port:           MySQL Server Port (3306 by default.)
  database:       MySQL Database
  user:           Database User Name
  password:       Database User Password
  include_graphs: Comma separated list of enabled graphs. 
                  (All graphs enabled by default.)
  exclude_graphs: Comma separated list of disabled graphs.
  include_engine: Comma separated list of storage engines to include graphs.
                  (All enabled by default.)
  exclude_engine: Comma separated list of storage engines to exclude from graphs.
  

  Example:
    [mysqlstats]
        user root
        env.exclude_graphs mysql_threads
        env.include_engine innodb

"""
# Munin  - Magic Markers
#%# family=auto
#%# capabilities=autoconf nosuggest

import sys
from pymunin import MuninGraph, MuninPlugin, muninMain
from pysysinfo.mysql import MySQLinfo

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = ["Kjell-Magne Oierud (kjellm at GitHub)"]
__license__ = "GPL"
__version__ = "0.7"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


class MuninMySQLplugin(MuninPlugin):
    """Multigraph Munin Plugin for monitoring MySQL Database Server.

    """
    plugin_name = 'pgstats'
    isMultigraph = True

    def __init__(self, argv=(), env={}, debug=False):
        """Populate Munin Plugin with MuninGraph instances.
        
        @param argv:  List of command line arguments.
        @param env:   Dictionary of environment variables.
        @param debug: Print debugging messages if True. (Default: False)
        
        """
        MuninPlugin.__init__(self, argv, env, debug)
        
        self.envRegisterFilter('engine', '^\w+$')
        
        self._host = self.envGet('host')
        self._port = self.envGet('port', None, int)
        self._database = self.envGet('database')
        self._user = self.envGet('user')
        self._password = self.envGet('password')
        
        self._dbconn = MySQLinfo(self._host, self._port, self._database, 
                              self._user, self._password)
        
        if self.graphEnabled('mysql_connections'):
            graph = MuninGraph('MySQL - Connections per second', 
                'MySQL',
                info='MySQL Database Server new and aborted connections per second.',
                args='--base 1000 --lower-limit 0')
            graph.addField('conn', 'conn', draw='LINE2', 
                type='DERIVE', min=0,
                info='The number of connection attempts to the MySQL server.')
            graph.addField('abort_conn', 'abort_conn', draw='LINE2', 
                type='DERIVE', min=0,
                info='The number of failed attempts to connect to the MySQL server.')
            graph.addField('abort_client', 'abort_client', draw='LINE2', 
                type='DERIVE', min=0,
                info='The number of connections that were aborted, because '
                     'the client died without closing the connection properly.')
            self.appendGraph('mysql_connections', graph)
        
        if self.graphEnabled('mysql_traffic'):
            graph = MuninGraph('MySQL - Network Traffic (bytes/sec)', 
                'MySQL',
                info='MySQL Database Server Network Traffic in bytes per second.',
                args='--base 1000 --lower-limit 0',
                vlabel='bytes in (-) / out (+) per second')
            graph.addField('rx', 'bytes', draw='LINE2', type='DERIVE', 
                           min=0, graph=False)
            graph.addField('tx', 'bytes', draw='LINE2', type='DERIVE', 
                           min=0, negative='rx',
                    info="Bytes In (-) / Out (+) per second.")
            self.appendGraph('mysql_traffic', graph)
            
        if self.graphEnabled('mysql_slowqueries'):
            graph = MuninGraph('MySQL - Slow Queries per second', 
                'MySQL',
                info='The number of queries that have taken more than '
                     'long_query_time seconds.',
                args='--base 1000 --lower-limit 0')
            graph.addField('queries', 'queries', draw='LINE2', 
                           type='DERIVE', min=0)
            self.appendGraph('mysql_slowqueries', graph)
            
        if self.graphEnabled('mysql_rowmodifications'):
            graph = MuninGraph('MySQL - Row Insert, Delete, Updates per second', 
                'MySQL',
                info='MySQL Inserted, Deleted, Updated Rows per second.',
                args='--base 1000 --lower-limit 0')
            graph.addField('insert', 'insert', draw='AREASTACK', 
                type='DERIVE', min=0,
                info='The number of requests to insert a rows into tables.')
            graph.addField('update', 'update', draw='AREASTACK', 
                type='DERIVE', min=0,
                info='The number of requests to update a rows in a tables.')
            graph.addField('delete', 'delete', draw='AREASTACK', 
                type='DERIVE', min=0,
                info='The number of requests to delete rows from tables.')
            self.appendGraph('mysql_rowmodifications', graph)
            
        if self.graphEnabled('mysql_rowreads'):
            graph = MuninGraph('MySQL - Row Reads per second', 
                'MySQL',
                info='MySQL Row Reads per second.',
                args='--base 1000 --lower-limit 0')
            for (field, desc) in (('first', 
                                   'Requests to read first entry in index.'),
                                  ('key', 
                                   'Requests to read a row based on a key.'),
                                  ('next', 
                                   'Requests to read the next row in key order.'),
                                  ('prev', 
                                   'Requests to read the previous row in key order.'),
                                  ('rnd', 
                                   'Requests to read a row based on a fixed position.'),
                                  ('rnd_next', 
                                   'Requests to read the next row in the data file.'),):
                graph.addField(field, field, draw='AREASTACK', 
                    type='DERIVE', min=0, info=desc)
            self.appendGraph('mysql_rowreads', graph)
            
        if self.graphEnabled('mysql_tablelocks'):
            graph = MuninGraph('MySQL - Table Locks per second', 
                'MySQL',
                info='MySQL Table Locks per second.',
                args='--base 1000 --lower-limit 0')
            graph.addField('waited', 'waited', draw='AREASTACK', 
                type='DERIVE', min=0,
                info='The number of times that a request for a table lock '
                     'could not be granted immediately and a wait was needed.')
            graph.addField('immediate', 'immediate', draw='AREASTACK', 
                type='DERIVE', min=0,
                info='The number of times that a request for a table lock '
                     'could be granted immediately.')
            self.appendGraph('mysql_tablelocks', graph)
        
        if self.graphEnabled('mysql_threads'):
            graph = MuninGraph('MySQL - Threads', 
                'MySQL',
                info='MySQL Database Server threads status.',
                args='--base 1000 --lower-limit 0')
            graph.addField('running', 'running', draw='AREASTACK', type='GAUGE', 
                info="Number of threads executing queries.")
            graph.addField('idle', 'idle', draw='AREASTACK', type='GAUGE', 
                info="Number of idle threads with connected clients.")
            graph.addField('cached', 'cached', draw='AREASTACK', type='GAUGE', 
                info="Number of cached threads without connected clients.")
            graph.addField('total', 'total', draw='LINE2', type='GAUGE', 
                           colour='000000',
                           info="Total number of threads.")
            self.appendGraph('mysql_threads', graph)
            
        if self.graphEnabled('mysql_commits_rollbacks'):
            graph = MuninGraph('MySQL - Commits and Rollbacks', 
                'MySQL',
                info='MySQL Commits and Rollbacks per second.',
                args='--base 1000 --lower-limit 0')
            graph.addField('commit', 'commit', draw='LINE2', 
                type='DERIVE', min=0,
                info='The number of commits per second.')
            graph.addField('rollback', 'rollback', draw='LINE2', 
                type='DERIVE', min=0,
                info='The number of rollbacks per second.')
            self.appendGraph('mysql_commits_rollbacks', graph)
                    
    def retrieveVals(self):
        """Retrieve values for graphs."""
        self._genStats = None
        if self.hasGraph('mysql_connections'):
            if self._genStats is None:
                self._genStats = self._dbconn.getStats()
            self.setGraphVal('mysql_connections', 'conn',
                             self._genStats.get('Connections'))
            self.setGraphVal('mysql_connections', 'abort_conn',
                             self._genStats.get('Aborted_connects'))
            self.setGraphVal('mysql_connections', 'abort_client',
                             self._genStats.get('Aborted_clients'))
        if self.hasGraph('mysql_traffic'):
            if self._genStats is None:
                self._genStats = self._dbconn.getStats()
            self.setGraphVal('mysql_traffic', 'rx',
                             self._genStats.get('Bytes_received'))
            self.setGraphVal('mysql_traffic', 'tx',
                             self._genStats.get('Bytes_sent'))
        if self.graphEnabled('mysql_slowqueries'):
            if self._genStats is None:
                self._genStats = self._dbconn.getStats()
            self.setGraphVal('mysql_slowqueries', 'queries',
                             self._genStats.get('Slow_queries'))
        if self.hasGraph('mysql_rowmodifications'):
            if self._genStats is None:
                self._genStats = self._dbconn.getStats()
            self.setGraphVal('mysql_rowmodifications', 'insert',
                             self._genStats.get('Handler_write'))
            self.setGraphVal('mysql_rowmodifications', 'update',
                             self._genStats.get('Handler_update'))
            self.setGraphVal('mysql_rowmodifications', 'delete',
                             self._genStats.get('Handler_delete'))
        if self.hasGraph('mysql_rowreads'):
            if self._genStats is None:
                self._genStats = self._dbconn.getStats()
            for field in self.getGraphFieldList('mysql_rowreads'):
                self.setGraphVal('mysql_rowreads', field, 
                                 self._genStats.get('Handler_read_%s' % field))
        if self.hasGraph('mysql_tablelocks'):
            if self._genStats is None:
                self._genStats = self._dbconn.getStats()
            self.setGraphVal('mysql_tablelocks', 'waited',
                             self._genStats.get('Table_locks_waited'))
            self.setGraphVal('mysql_tablelocks', 'immediate',
                             self._genStats.get('Table_locks_immediate'))
        if self.hasGraph('mysql_threads'):
            if self._genStats is None:
                self._genStats = self._dbconn.getStats()
            self.setGraphVal('mysql_threads', 'running',
                             self._genStats.get('Threads_running'))
            self.setGraphVal('mysql_threads', 'idle',
                             self._genStats.get('Threads_connected')
                             - self._genStats.get('Threads_running'))
            self.setGraphVal('mysql_threads', 'cached',
                             self._genStats.get('Threads_cached'))
            self.setGraphVal('mysql_threads', 'total',
                             self._genStats.get('Threads_connected') 
                             + self._genStats.get('Threads_cached'))
        if self.hasGraph('mysql_commits_rollbacks'):
            if self._genStats is None:
                self._genStats = self._dbconn.getStats()
            self.setGraphVal('mysql_commits_rollbacks', 'commit',
                             self._genStats.get('Handler_commit'))
            self.setGraphVal('mysql_commits_rollbacks', 'rollback',
                             self._genStats.get('Handler_rollback'))
            
    def engineIncluded(self, name):
        """Utility method to check if a storage engine is included in graphs.
        
        @param name: Name of storage engine.
        @return:     Returns True if included in graphs, False otherwise.
            
        """
        return self.envCheckFilter('engine', name)
    
    def autoconf(self):
        """Implements Munin Plugin Auto-Configuration Option.
        
        @return: True if plugin can be  auto-configured, False otherwise.
                 
        """
        return (self._dbconn is not None 
                and len(self._dbconn.getDatabases()) > 0)
              

def main():
    sys.exit(muninMain(MuninMySQLplugin))


if __name__ == "__main__":
    main()
