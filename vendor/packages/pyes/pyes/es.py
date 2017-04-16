#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import with_statement

__author__ = 'Alberto Paro'
__all__ = ['ES', 'file_to_attachment', 'decode_json']

try:
    # For Python >= 2.6
    import json
except ImportError:
    # For Python < 2.6 or people using a newer version of simplejson
    import simplejson as json

import logging
from datetime import date, datetime
import base64
import time
from StringIO import StringIO
from decimal import Decimal

try:
    from connection import connect as thrift_connect
    from pyesthrift.ttypes import Method, RestRequest
    thrift_enable = True
except ImportError:
    from fakettypes import Method, RestRequest
    thrift_enable = False

from connection_http import connect as http_connect
log = logging.getLogger('pyes')
from mappings import Mapper

from convert_errors import raise_if_error
import pyes.exceptions

def file_to_attachment(filename):
    """
    Convert a file to attachment
    """
    with open(filename, 'rb') as _file:
        return {'_name':filename,
                'content':base64.b64encode(_file.read())
                }

class ESJsonEncoder(json.JSONEncoder):
    def default(self, value):
        """Convert rogue and mysterious data types.
        Conversion notes:
        
        - ``datetime.date`` and ``datetime.datetime`` objects are
        converted into datetime strings.
        """

        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%dT%H:%M:%S")
        elif isinstance(value, date):
            dt = datetime(value.year, value.month, value.day, 0, 0, 0)
            return dt.strftime("%Y-%m-%dT%H:%M:%S")
        elif isinstance(value, Decimal):
            return float(str(value))
        else:
            # use no special encoding and hope for the best
            return value

class ESJsonDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        kwargs['object_hook'] = self.dict_to_object
        json.JSONDecoder.__init__(self, *args, **kwargs)

    def string_to_datetime(self, obj):
        """Decode a datetime string to a datetime object
        """
        if isinstance(obj, basestring) and len(obj) == 19:
            try:
                return datetime(*obj.strptime("%Y-%m-%dT%H:%M:%S")[:6])
            except:
                pass
        return obj

    def dict_to_object(self, d):
        """
        Decode datetime value from string to datetime
        """
        for k, v in d.items():
            if isinstance(v, basestring) and len(v) == 19:
                try:
                    d[k] = datetime(*time.strptime(v, "%Y-%m-%dT%H:%M:%S")[:6])
                except ValueError:
                    pass
            elif isinstance(v, list):
                d[k] = [self.string_to_datetime(elem) for elem in v]
        return d

class ES(object):
    """
    ES connection object.
    """

    def __init__(self, server, timeout=5.0, bulk_size=400,
                 encoder=None, decoder=None,
                 max_retries=3, autorefresh=False,
                 default_indexes=['_all'],
                 dump_curl=False):
        """
        Init a es object
        
        server: the server name, it can be a list of servers
        timeout: timeout for a call
        bulk_size: size of bulk operation
        encoder: tojson encoder
        max_retries: number of max retries for server if a server is down
        autorefresh: check if need a refresh before a query

        dump_curl: If truthy, this will dump every query to a curl file.  If
        this is set to a string value, it names the file that output is sent
        to.  Otherwise, it should be set to an object with a write() method,
        which output will be written to.

        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.cluster = None
        self.debug_dump = False
        self.cluster_name = "undefined"
        self.connection = None
        self.autorefresh = autorefresh
        self.refreshed = True
        if dump_curl:
            if isinstance(dump_curl, basestring):
                self.dump_curl = open(dump_curl, "wb")
            elif hasattr(dump_curl, 'write'):
                self.dump_curl = dump_curl
            else:
                raise TypeError("dump_curl parameter must be supplied with a "
                                "string or an object with a write() method")
        else:
            self.dump_curl = None

        #used in bulk
        self.bulk_size = bulk_size #size of the bulk
        self.bulk_data = StringIO()
        self.bulk_items = 0

        self.info = {} #info about the current server
        self.encoder = encoder
        if self.encoder is None:
            self.encoder = ESJsonEncoder
        self.decoder = decoder
        if self.decoder is None:
            self.decoder = ESJsonDecoder
        if isinstance(server, (str, unicode)):
            self.servers = [server]
        else:
            self.servers = server
        self.default_indexes = default_indexes
        self._init_connection()

    def __del__(self):
        """
        Destructor
        """
        if self.bulk_items > 0:
            self.flush()

    def _init_connection(self):
        """
        Create initial connection pool
        """
        #detect connectiontype
        port = self.servers[0].split(":")[1]
        if port.startswith("92"):
            self.connection = http_connect(self.servers, timeout=self.timeout, max_retries=self.max_retries)
            return
        if not thrift_enable:
            raise RuntimeError("If you want to use thrift, please install pythrift")
        self.connection = thrift_connect(self.servers, timeout=self.timeout, max_retries=self.max_retries)

    def _discovery(self):
        """
        Find other servers asking nodes to given server
        """
        data = self.cluster_nodes()
        self.cluster_name = data["cluster_name"]
        for _, nodedata in data["nodes"].items():
            server = nodedata['http_address'].replace("]", "").replace("inet[", "http:/")
            if server not in self.servers:
                self.servers.append(server)
        self._init_connection()
        return self.servers

    def _send_request(self, method, path, body=None, params={}):
        # prepare the request
        if not path.startswith("/"):
            path = "/" + path
        if not self.connection:
            self._init_connection()
        if body:
            if isinstance(body, dict):
                body = json.dumps(body, cls=self.encoder)
        else:
            body = ""
        request = RestRequest(method=Method._NAMES_TO_VALUES[method.upper()], uri=path, parameters=params, headers={}, body=body)
        if self.dump_curl is not None:
            self._dump_curl_request(request)

        # execute the request
        response = self.connection.execute(request)

        # handle the response
        try:
            decoded = json.loads(response.body, cls=self.decoder)
        except ValueError:
            try:
                decoded = json.loads(response.body, cls=ESJsonDecoder)
            except ValueError:
                # The only known place where we get back a body which can't be
                # parsed as JSON is when no handler is found for a request URI.
                # In this case, the body is actually a good message to return
                # in the exception.
                raise pyes.exceptions.ElasticSearchException(response.body, response.status, response.body)
        if response.status != 200:
            raise_if_error(response.status, decoded)
        return  decoded

    def _make_path(self, path_components):
        """
        Smush together the path components. Empty components will be ignored.
        """
        path_components = [str(component) for component in path_components if component]
        path = '/'.join(path_components)
        if not path.startswith('/'):
            path = '/' + path
        return path

    def _query_call(self, query_type, query, indexes=None, doc_types=None, **query_params):
        """
        This can be used for search and count calls.
        These are identical api calls, except for the type of query.
        """
        if self.autorefresh and self.refreshed == False:
            self.refresh(indexes)
        querystring_args = query_params
        indexes = self._validate_indexes(indexes)
        if doc_types is None:
            doc_types = []
        if isinstance(doc_types, basestring):
            doc_types = [doc_types]
        body = query
        path = self._make_path([','.join(indexes), ','.join(doc_types), query_type])
        response = self._send_request('GET', path, body, querystring_args)
        return response

    def _validate_indexes(self, indexes=None):
        """Return a valid list of indexes.

        `indexes` may be a string or a list of strings.
        If `indexes` is not supplied, returns the default_indexes.

        """
        indexes = indexes or self.default_indexes
        if isinstance(indexes, basestring):
            indexes = [indexes]
        return indexes

    def _dump_curl_request(self, request):
        self.dump_curl.write("# [%s]\n" % datetime.now().isoformat())
        self.dump_curl.write("curl -X" + Method._VALUES_TO_NAMES[request.method])
        self.dump_curl.write(" http://" + self.servers[0] + request.uri)
        if request.body:
            self.dump_curl.write(" -d \"%s\"" % request.body.replace('"', '\\"'))
        self.dump_curl.write("\n")

    #---- Admin commands
    def status(self, indexes=None):
        """
        Retrieve the status of one or more indices
        """
        indexes = self._validate_indexes(indexes)
        path = self._make_path([','.join(indexes), '_status'])
        return self._send_request('GET', path)

    def create_index(self, index, settings=None):
        """
        Creates an index with optional settings.
        Settings must be a dictionary which will be converted to JSON.
        Elasticsearch also accepts yaml, but we are only passing JSON.
        """
        return self._send_request('PUT', index, settings)

    def create_index_if_missing(self, index, settings=None):
        """Creates an index if it doesn't already exist.

        If supplied, settings must be a dictionary.

        """
        try:
            return self.create_index(index, settings)
        except pyes.exceptions.IndexAlreadyExistsException, e:
            return e.result

    def delete_index(self, index):
        """Deletes an index.

        """
        return self._send_request('DELETE', index)

    def delete_index_if_exists(self, index):
        """Deletes an index if it exists.

        """
        try:
            return self.delete_index(index)
        except pyes.exceptions.IndexMissingException:
            pass
        except pyes.exceptions.NotFoundException, e:
            return e.result

    def get_indices(self, include_aliases=False):
        """Get a dict holding an entry for each index which exists.

        If include_alises is True, the dict will also contain entries for
        aliases.

        The key for each entry in the dict is the index or alias name.  The
        value is a dict holding the following properties:

         - num_docs: Number of documents in the index or alias.
         - alias_for: Only present for an alias: holds a list of indices which
           this is an alias for.

        """
        status = self.status()
        result = {}
        indices = status['indices']
        for index in sorted(indices.keys()):
            info = indices[index]
            num_docs = info['docs']['num_docs']
            result[index] = dict(num_docs=num_docs)
            if not include_aliases:
                continue
            for alias in info['aliases']:
                try:
                    alias_obj = result[alias]
                except KeyError:
                    alias_obj = {}
                    result[alias] = alias_obj
                alias_obj['num_docs'] = alias_obj.get('num_docs', 0) + num_docs
                try:
                    alias_obj['alias_for'].append(index)
                except KeyError:
                    alias_obj['alias_for'] = [index]
        return result

    def get_alias(self, alias):
        """Get the index or indices pointed to by a given alias.

        Raises IndexMissingException if the alias does not exist.

        Otherwise, returns a list of index names.

        """
        status = self.status(alias)
        return status['indices'].keys()

    def change_aliases(self, commands):
        """Change the aliases stored.

        `commands` is a list of 3-tuples; (command, index, alias), where
        `command` is one of "add" or "remove", and `index` and `alias` are the
        index and alias to add or remove.

        """
        body = {
            'actions': [
                 {command: dict(index=index, alias=alias) }
                 for (command, index, alias) in commands
            ]
        }
        return self._send_request('POST', "_aliases", body)

    def add_alias(self, alias, indices):
        """Add an alias to point to a set of indices.

        """
        if isinstance(indices, basestring):
            indices = [indices]
        return self.change_aliases(['add', index, alias]
                                   for index in indices)

    def delete_alias(self, alias, indices):
        """Delete an alias.

        The specified index or indices are deleted from the alias, if they are
        in it to start with.  This won't report an error even if the indices
        aren't present in the alias.

        """
        if isinstance(indices, basestring):
            indices = [indices]
        return self.change_aliases(['remove', index, alias]
                                   for index in indices)

    def set_alias(self, alias, indices):
        """Set an alias.

        This handles removing the old list of indices pointed to by the alias.

        Warning: there is a race condition in the implementation of this
        function - if another client modifies the indices which this alias
        points to during this call, the old value of the alias may not be
        correctly set.

        """
        if isinstance(indices, basestring):
            indices = [indices]
        try:
            old_indices = self.get_alias(alias)
        except pyes.exceptions.IndexMissingException:
            old_indices = []
        commands = [['remove', index, alias] for index in old_indices]
        commands.extend([['add', index, alias] for index in indices])
        if len(commands) > 0:
            return self.change_aliases(commands)

    def close_index(self, index):
        """
        Close an index.
        """
        return self._send_request('POST', "/%s/_close" % index)

    def open_index(self, index):
        """
        Open an index.
        """
        return self._send_request('POST', "/%s/_open" % index)

    def flush(self, indexes=None, refresh=None):
        """
        Flushes one or more indices (clear memory)
        """
        self.force_bulk()

        indexes = self._validate_indexes(indexes)

        path = self._make_path([','.join(indexes), '_flush'])
        args = {}
        if refresh is not None:
            args['refresh'] = refresh
        return self._send_request('POST', path, params=args)

    def refresh(self, indexes=None, timesleep=1):
        """
        Refresh one or more indices
        
        timesleep: seconds to wait
        """
        self.force_bulk()
        indexes = self._validate_indexes(indexes)

        path = self._make_path([','.join(indexes), '_refresh'])
        result = self._send_request('POST', path)
        time.sleep(timesleep)
        self.cluster_health(wait_for_status='green')
        self.refreshed = True
        return result


    def optimize(self, indexes=None,
                 wait_for_merge=False,
                 max_num_segments=None,
                 only_expunge_deletes=False,
                 refresh=True,
                 flush=True):
        """Optimize one or more indices.

        `indexes` is the list of indexes to optimise.  If not supplied, or
        "_all", all indexes are optimised.

        `wait_for_merge` (boolean): If True, the operation will not return
        until the merge has been completed.  Defaults to False.

        `max_num_segments` (integer): The number of segments to optimize to. To
        fully optimize the index, set it to 1. Defaults to half the number
        configured by the merge policy (which in turn defaults to 10).

        `only_expunge_deletes` (boolean): Should the optimize process only
        expunge segments with deletes in it. In Lucene, a document is not
        deleted from a segment, just marked as deleted. During a merge process
        of segments, a new segment is created that does have those deletes.
        This flag allow to only merge segments that have deletes. Defaults to
        false.

        `refresh` (boolean): Should a refresh be performed after the optimize.
        Defaults to true.

        `flush` (boolean): Should a flush be performed after the optimize.
        Defaults to true.

        """
        indexes = self._validate_indexes(indexes)
        path = self._make_path([','.join(indexes), '_optimize'])
        params = dict(
            wait_for_merge=wait_for_merge,
            only_expunge_deletes=only_expunge_deletes,
            refresh=refresh,
            flush=flush,
        )
        if max_num_segments is not None:
            params['max_num_segments'] = max_num_segments
        result = self._send_request('POST', path, params=params)
        self.refreshed = True
        return result
    
    def analyze(self, text, index=None):
        """
        Performs the analysis process on a text and return the tokens breakdown of the text
        """
        path = self._make_path([index, '_analyze'])
        return self._send_request('POST', path, text)

    def gateway_snapshot(self, indexes=None):
        """
        Gateway snapshot one or more indices
        """
        indexes = self._validate_indexes(indexes)
        path = self._make_path([','.join(indexes), '_gateway', 'snapshot'])
        return self._send_request('POST', path)

    def put_mapping(self, doc_type, mapping, indexes=None):
        """
        Register specific mapping definition for a specific type against one or more indices.
        """
        indexes = self._validate_indexes(indexes)
        path = self._make_path([','.join(indexes), doc_type, "_mapping"])
        if hasattr(mapping, "to_json"):
            mapping = mapping.to_json()
        if doc_type not in mapping:
            mapping = {doc_type:mapping}
        self.refreshed = False
        return self._send_request('PUT', path, mapping)

    def get_mapping(self, doc_type=None, indexes=None):
        """
        Register specific mapping definition for a specific type against one or more indices.
        """
        indexes = self._validate_indexes(indexes)
        if doc_type:
            path = self._make_path([','.join(indexes), doc_type, "_mapping"])
        else:
            path = self._make_path([','.join(indexes), "_mapping"])
        result = self._send_request('GET', path)
        return result


    def collect_info(self):
        """
        Collect info about the connection and fill the info dictionary
        """
        self.info = {}
        res = self._send_request('GET', "/")
        self.info['server'] = {}
        self.info['server']['name'] = res['name']
        self.info['server']['version'] = res['version']
        self.info['allinfo'] = res
        self.info['status'] = self.status(["_all"])
        return self.info

    #--- cluster
    def cluster_health(self, indexes=None, level="cluster", wait_for_status=None,
               wait_for_relocating_shards=None, timeout=30):
        """
        Check the current :ref:`cluster health <es-guide-reference-api-admin-cluster-health>`.
        Request Parameters

        The cluster health API accepts the following request parameters:
        
        :param level: Can be one of cluster, indices or shards. Controls the 
                        details level of the health information returned. 
                        Defaults to *cluster*.
        :param wait_for_status: One of green, yellow or red. Will wait (until 
                                the timeout provided) until the status of the 
                                cluster changes to the one provided. 
                                By default, will not wait for any status.
        :param wait_for_relocating_shards: A number controlling to how many 
                                           relocating shards to wait for. 
                                           Usually will be 0 to indicate to 
                                           wait till all relocation have 
                                           happened. Defaults to not to wait.
        :param timeout: A time based parameter controlling how long to wait 
                        if one of the wait_for_XXX are provided. 
                        Defaults to 30s.
        """
        path = self._make_path(["_cluster", "health"])
        mapping = {}
        if level != "cluster":
            if level not in ["cluster", "indices", "shards"]:
                raise ValueError("Invalid level: %s" % level)
            mapping['level'] = level
        if wait_for_status:
            if wait_for_status not in ["green", "yellow", "red"]:
                raise ValueError("Invalid wait_for_status: %s" % wait_for_status)
            mapping['wait_for_status'] = wait_for_status

            mapping['timeout'] = "%ds" % timeout
        return self._send_request('GET', path, mapping)

    def cluster_state(self, filter_nodes=None, filter_routing_table=None,
                      filter_metadata=None, filter_blocks=None,
                      filter_indices=None):
        """
        Retrieve the :ref:`cluster state <es-guide-reference-api-admin-cluster-state>`.

        :param filter_nodes: set to **true** to filter out the **nodes** part 
                             of the response.                            
        :param filter_routing_table: set to **true** to filter out the 
                                     **routing_table** part of the response.                    
        :param filter_metadata: set to **true** to filter out the **metadata** 
                                part of the response.                         
        :param filter_blocks: set to **true** to filter out the **blocks** 
                              part of the response.                           
        :param filter_indices: when not filtering metadata, a comma separated 
                               list of indices to include in the response.   

        """
        path = self._make_path(["_cluster", "state"])
        parameters = {}

        if filter_nodes is not None:
            parameters['filter_nodes'] = filter_nodes

        if filter_routing_table is not None:
            parameters['filter_routing_table'] = filter_routing_table

        if filter_metadata is not None:
            parameters['filter_metadata'] = filter_metadata

        if filter_blocks is not None:
            parameters['filter_blocks'] = filter_blocks

        if filter_blocks is not None:
            if isinstance(filter_indices, basestring):
                parameters['filter_indices'] = filter_indices
            else:
                parameters['filter_indices'] = ",".join(filter_indices)

        return self._send_request('GET', path, params=parameters)

    def cluster_nodes(self, nodes=None):
        """
        The cluster :ref:`nodes info <es-guide-reference-api-admin-cluster-state>` API allows to retrieve one or more (or all) of 
        the cluster nodes information.
        """
        parts = ["_cluster", "nodes"]
        if nodes:
            parts.append(",".join(nodes))
        path = self._make_path(parts)
        return self._send_request('GET', path)

    def cluster_stats(self, nodes=None):
        """
        The cluster :ref:`nodes info <es-guide-reference-api-admin-cluster-nodes-stats>` API allows to retrieve one or more (or all) of 
        the cluster nodes information.
        """
        parts = ["_cluster", "nodes", "stats"]
        if nodes:
            parts = ["_cluster", "nodes", ",".join(nodes), "stats"]

        path = self._make_path(parts)
        return self._send_request('GET', path)

    def index(self, doc, index, doc_type, id=None, parent=None, force_insert=False, bulk=False, version=None, querystring_args=None):
        """
        Index a typed JSON document into a specific index and make it searchable.
        """
        if querystring_args is None:
            querystring_args = {}

        self.refreshed = False

        if bulk:
            optype = "index"
            if force_insert:
                optype = "create"
            cmd = { optype : { "_index" : index, "_type" : doc_type}}
            if parent:
                cmd[optype]['_parent'] = parent
            if version:
                cmd[optype]['_version'] = version
            if id:
                cmd[optype]['_id'] = id
            self.bulk_data.write(json.dumps(cmd, cls=self.encoder))
            self.bulk_data.write("\n")
            if isinstance(doc, dict):
                doc = json.dumps(doc, cls=self.encoder)
            self.bulk_data.write(doc)
            self.bulk_data.write("\n")
            self.bulk_items += 1
            self.flush_bulk()
            return


        if force_insert:
            querystring_args['opType'] = 'create'

        if parent:
            querystring_args['parent'] = parent

        if version:
            querystring_args['version'] = version

        if id is None:
            request_method = 'POST'
        else:
            request_method = 'PUT'

        path = self._make_path([index, doc_type, id])
        return self._send_request(request_method, path, doc, querystring_args)

    def flush_bulk(self, forced=False):
        """
        Wait to process all pending operations
        """
        if not forced and self.bulk_items < self.bulk_size:
            return
        self.force_bulk()

    def force_bulk(self):
        """
        Force executing of all bulk data
        """
        if self.bulk_items == 0:
            return
        self._send_request("POST", "/_bulk", self.bulk_data.getvalue())
        self.bulk_data = StringIO()
        self.bulk_items = 0

    def put_file(self, filename, index, doc_type, id=None):
        """
        Store a file in a index
        """
        querystring_args = {}

        if id is None:
            request_method = 'POST'
        else:
            request_method = 'PUT'
        path = self._make_path([index, doc_type, id])
        doc = file_to_attachment(filename)
        return self._send_request(request_method, path, doc, querystring_args)

    def get_file(self, index, doc_type, id=None):
        """
        Return the filename and memory data stream
        """
        data = self.get(index, doc_type, id)
        return data["_source"]['_name'], base64.standard_b64decode(data["_source"]['content'])

    def delete(self, index, doc_type, id, bulk=False):
        """
        Delete a typed JSON document from a specific index based on its id.
        If bulk is True, the delete operation is put in bulk mode.
        """
        if bulk:
            cmd = { "delete" : { "_index" : index, "_type" : doc_type,
                                "_id": id}}
            self.bulk_data.write(json.dumps(cmd, cls=self.encoder))
            self.bulk_data.write("\n")
            self.bulk_items += 1
            self.flush_bulk()
            return

        path = self._make_path([index, doc_type, id])
        return self._send_request('DELETE', path)

    def deleteByQuery(self, indexes, doc_types, query, **request_params):
        """
        Delete documents from one or more indexes and one or more types based on a query.
        """
        querystring_args = request_params
        indexes = self._validate_indexes(indexes)
        if doc_types is None:
            doc_types = []
        if isinstance(doc_types, basestring):
            doc_types = [doc_types]

        if hasattr(query, 'to_query_json'):
            # Then is a Query object.
            body = query.to_query_json()
        elif isinstance(query, dict):
            # A direct set of search parameters.
            body = json.dumps(query, cls=self.encoder)
        else:
            raise pyes.exceptions.InvalidQuery("deleteByQuery() must be supplied with a Query object, or a dict")

        path = self._make_path([','.join(indexes), ','.join(doc_types), '_query'])
        response = self._send_request('DELETE', path, body, querystring_args)
        return response

    def delete_mapping(self, index, doc_type):
        """
        Delete a typed JSON document type from a specific index.
        """
        path = self._make_path([index, doc_type])
        return self._send_request('DELETE', path)

    def get(self, index, doc_type, id, fields=None, routing=None, **get_params):
        """
        Get a typed JSON document from an index based on its id.
        """
        path = self._make_path([index, doc_type, id])
        if fields is not None:
            get_params["fields"] = ",".join(fields)
        if routing:
            get_params["routing"] = routing
        return self._send_request('GET', path, params=get_params)

    def search(self, query, indexes=None, doc_types=None, **query_params):
        """Execute a search against one or more indices to get the search hits.

        `query` must be a Search object, a Query object, or a custom
        dictionary of search parameters using the query DSL to be passed
        directly.

        """
        indexes = self._validate_indexes(indexes)
        if doc_types is None:
            doc_types = []
        elif isinstance(doc_types, basestring):
            doc_types = [doc_types]

        if hasattr(query, 'to_search_json'):
            # Common case - a Search or Query object.
            body = query.to_search_json()
        elif isinstance(query, dict):
            # A direct set of search parameters.
            body = json.dumps(query, cls=self.encoder)
        else:
            raise pyes.exceptions.InvalidQuery("search() must be supplied with a Search or Query object, or a dict")

        return self._query_call("_search", body, indexes, doc_types, **query_params)

    def scan(self, query, indexes=None, doc_types=None, scroll_timeout="10m", **query_params):
        """Return a generator which will scan against one or more indices and iterate over the search hits. (currently support only by ES Master)

        `query` must be a Search object, a Query object, or a custom
        dictionary of search parameters using the query DSL to be passed
        directly.

        """
        results = self.search(query=query, indexes=indexes, doc_types=doc_types, search_type="scan", scroll=scroll_timeout, **query_params)
        while True:
            scroll_id = results["_scroll_id"]
            results = self._send_request('GET', "_search/scroll", scroll_id, {"scroll":scroll_timeout})
            total = len(results["hits"]["hits"])
            if not total:
                break
            yield results

    def reindex(self, query, indexes=None, doc_types=None, **query_params):
        """
        Execute a search query against one or more indices and and reindex the hits.
        query must be a dictionary or a Query object that will convert to Query DSL.
        Note: reindex is only available in my ElasticSearch branch on github.
        """
        indexes = self._validate_indexes(indexes)
        if doc_types is None:
            doc_types = []
        if isinstance(doc_types, basestring):
            doc_types = [doc_types]
        if not isinstance(query, basestring):
            if isinstance(query, dict):
                if 'query' in query:
                    query = query['query']
                query = json.dumps(query, cls=self.encoder)
            elif hasattr(query, "to_query_json"):
                query = query.to_query_json(inner=True)
        querystring_args = query_params
        indexes = self._validate_indexes(indexes)
        body = query
        path = self._make_path([','.join(indexes), ','.join(doc_types), "_reindexbyquery"])
        return self._send_request('POST', path, body, querystring_args)

    def count(self, query, indexes=None, doc_types=None, **query_params):
        """
        Execute a query against one or more indices and get hits count.
        """
        indexes = self._validate_indexes(indexes)
        if doc_types is None:
            doc_types = []
        if hasattr(query, 'to_query_json'):
            query = query.to_query_json()
        return self._query_call("_count", query, indexes, doc_types, **query_params)

    def morelikethis(self, index, doc_type, id, fields, **query_params):
        """
        Execute a "more like this" search query against one or more fields and get back search hits.
        """
        path = self._make_path([index, doc_type, id, '_mlt'])
        query_params['fields'] = ','.join(fields)
        return self._send_request('GET', path, params=query_params)

    #--- river management
    def create_river(self, river, river_name=None):
        """
        Create a river
        """
        if hasattr(river, "q"):
            river_name = river.name
            river = river.q
        return self._send_request('PUT', '/_river/%s/_meta' % river_name, river)

    def delete_river(self, river, river_name=None):
        """
        Delete a river
        """
        if hasattr(river, "q"):
            river_name = river.name
        return self._send_request('DELETE', '/_river/%s/' % river_name)

    #--- settings management
    def update_settings(self, index, newvalues):
        """
        Update Settings of an index.
        
        """
        path = self._make_path([index, "_settings"])
        return self._send_request('PUT', path, newvalues)

#    def terms(self, fields, indexes=None, **query_params):
#        """
#        Extract terms and their document frequencies from one or more fields.
#        The fields argument must be a list or tuple of fields.
#        For valid query params see: 
#        http://www.elasticsearch.com/docs/elasticsearch/rest_api/terms/
#        """
#        indexes = self._validate_indexes(indexes)
#        path = self._make_path([','.join(indexes), "_terms"])
#        query_params['fields'] = ','.join(fields)
#        return self._send_request('GET', path, params=query_params)
#    
    def morelikethis(self, index, doc_type, id, fields, **query_params):
        """
        Execute a "more like this" search query against one or more fields and get back search hits.
        """
        path = self._make_path([index, doc_type, id, '_mlt'])
        query_params['fields'] = ','.join(fields)
        return self._send_request('GET', path, params=query_params)

    def create_percolator(self, index, name, query, **kwargs):
        """
        Create a percolator document

        Any kwargs will be added to the document as extra properties.

        """
        path = self._make_path(['_percolator', index, name])
        body = None

        if hasattr(query, 'serialize'):
            query = {'query': query.serialize()}

        if isinstance(query, dict):
            # A direct set of search parameters.
            query.update(kwargs)
            body = json.dumps(query, cls=self.encoder)
        else:
            raise pyes.exceptions.InvalidQuery("create_percolator() must be supplied with a Query object or dict")

        return self._send_request('PUT', path, body=body)

    def delete_percolator(self, index, name):
        """
        Delete a percolator document
        """
        return self.delete('_percolator', index, name)

    def percolate(self, index, doc_types, query):
        """
        Match a query with a document
        """

        if doc_types is None:
            raise RuntimeError('percolate() must be supplied with at least one doc_type')
        elif not isinstance(doc_types, list):
            doc_types = [doc_types]

        path = self._make_path([index, ','.join(doc_types), '_percolate'])
        body = None

        if hasattr(query, 'to_query_json'):
            # Then is a Query object.
            body = query.to_query_json()
        elif isinstance(query, dict):
            # A direct set of search parameters.
            body = json.dumps(query, cls=self.encoder)
        else:
            raise pyes.exceptions.InvalidQuery("percolate() must be supplied with a Query object, or a dict")

        return self._send_request('GET', path, body=body)

    def update_settings(self, index, newvalues):
        """
        Update Settings of an index.
        
        """
        path = self._make_path([index, "_settings"])
        return self._send_request('PUT', path, newvalues)

def decode_json(data):
    """ Decode some json to dict"""
    return json.loads(data, cls=ESJsonDecoder)

def encode_json(data):
    """ Encode some json to dict"""
    return json.dumps(data, cls=ESJsonEncoder)

