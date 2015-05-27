Stouts.elasticsearch
====================

[![Build Status](http://img.shields.io/travis/Stouts/Stouts.elasticsearch.svg?style=flat-square)](https://travis-ci.org/Stouts/Stouts.elasticsearch)
[![Galaxy](http://img.shields.io/badge/galaxy-Stouts.elasticsearch-blue.svg?style=flat-square)](https://galaxy.ansible.com/list#/roles/876)

Ansible role for manage [Elasticsearch](www.elasticsearch.org)

* Install and configure Elasticsearch;
* Install/remove Elasticsearch plugins;
* Setup Nginx as proxy to Elasticseach;
* Setup HTTP Authorization;

#### Dependencies

The roles are recomended to install:

* [Stouts.nginx](https://github.com/Stouts/Stouts.nginx) - for proxing Elasticsearch with Nginx


#### Variables

Here is the list of all variables and their default values:
```yaml
elasticsearch_enabled: yes                      # The role is enabled
elasticsearch_version: 1.1.1                    # Elasticsearch version
elasticsearch_download_url: https://download.elasticsearch.org/elasticsearch/elasticsearch
elasticsearch_apt_repos:
- 'ppa:webupd8team/java'
elasticsearch_apt_java_package: oracle-java7-installer

elasticsearch_user: elasticsearch               # Elasticsearch user
elasticsearch_group: elasticsearch              # Elasticsearch group

elasticsearch_home: /usr/share/elasticsearch
elasticsearch_confdir: /etc/elasticsearch
elasticsearch_datadir: /var/lib/elasticsearch
elasticsearch_workdir: /tmp/elasticsearch
elasticsearch_logdir: /var/log/elasticsearch

elasticsearch_plugindir: "{{elasticsearch_home}}/plugins"
elasticsearch_plugins: []                       # Manage elasticsearch plugins (install/remove)
                                                # Ex. elasticsearch_plugins:
                                                #       - name: <plugin name>
                                                #         url: <optional plugin url>
                                                #         dir: <optional plugin dir>
                                                #         remove: yes # Optional the plugin will be removed

# Options
elasticsearch_network_host: 127.0.0.1           # Listen the host
elasticsearch_http_port: 9200                   # Listen the port fot HTTP traffic
elasticsearch_http_cors_enabled: yes            # Enable CORS
elasticsearch_http_cors_allow_origin: "*"       # Set allowed origins
elasticsearch_http_cors_allow_methods: OPTIONS, HEAD, GET, POST, PUT, DELETE
elasticsearch_max_open_files: 65535
elasticsearch_gateway_type: local
elasticsearch_script_disable_dynamic: yes

# Setup a proxy
elasticsearch_proxy: no                           # Enable nginx as elasticsearch proxy
elasticsearch_proxy_hostname:                     # Listen a hostname (leave empty for skip)
elasticsearch_proxy_port: 80                      # Listen a port
elasticsearch_proxy_auth: no                      # Enable HTTP Auth
elasticsearch_proxy_auth_users: []                # Setup users for HTTP Auth. Example:
                                                  # elasticsearch_proxy_auth_users:
                                                  # - { name: username, password: userpassword }
```

Additional variables could be defined, see Elasticsearch documentation about:
```yaml
elasticsearch_bootstrap_mlockall:
elasticsearch_cluster_name:
elasticsearch_gateway_expected_nodes:
elasticsearch_gateway_recover_after_nodes:
elasticsearch_gateway_recover_after_time:
elasticsearch_heap_size:
elasticsearch_http_enabled:
elasticsearch_http_max_content_length:
elasticsearch_index_mapper_dynamic:
elasticsearch_index_number_of_replicas:
elasticsearch_index_number_of_shards:
elasticsearch_index_query_bool_max_clause_count:
elasticsearch_java_opts:
elasticsearch_max_locked_memory:
elasticsearch_network_bind_host:
elasticsearch_network_publish_host:
elasticsearch_node_data:
elasticsearch_node_master:
elasticsearch_node_max_local_storage_nodes:
elasticsearch_node_name:
elasticsearch_node_rack:
elasticsearch_plugin_mandatory:
elasticsearch_recovery_concurrent_streams:
elasticsearch_recovery_max_size_per_sec:
elasticsearch_recovery_node_concurrent_recoveries:
elasticsearch_recovery_node_initial_primaries_recoveries:
elasticsearch_script_disable_dynamic
elasticsearch_script_groovy_sandbox_enabled
elasticsearch_transport_tcp_compress:
elasticsearch_transport_tcp_port:
elasticsearch_use_gc_logging:
```

#### Usage

Add `Stouts.elasticsearch` to your roles and setup the variables in your playbook file.
Example:

```yaml

- hosts: all

  roles:
    - Stouts.elasticsearch

  vars:
    elasticsearch_plugins:
    - name: lukas-vlcek/bigdesk
```

#### License

Licensed under the MIT License. See the LICENSE file for details.

#### Feedback, bug-reports, requests, ...

Are [welcome](https://github.com/Stouts/Stouts.elasticsearch/issues)!
