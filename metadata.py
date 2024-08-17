defaults = {
    'keepalived': {
        'router_id': node.name,
        'instances': {
            # 'VI_1': {
            #     'interface': 'eth0',
            #     'state': 'MASTER', # MASTER or SLAVE
            #     'virtual_router_id': 51, # same on all Nodes for this virtual IP
            #     'priority': 100, # priority 100 == Master, higher will become new MASTER
            #     'advert_int': 1, # advertising interval in Sec
            #     'auth_type': 'PASS', # Password Authentication (only supported option for now)
            #     'auth_pass': 'mysecretpass', # Password to use max 8 chars
            #     'virtual_ipaddress': ['192.168.0.20'], # IP address to be used
            # },
        },
    },
    # used to generate instances automaticaly
    # 'interfaces': {
    #     'admin': {
    #         'shared_ip_addresses': ['192.168.0.20'],
    #         'keepalived': {
    #             'state': 'MASTER', # Default MASTER
    #             'virtual_router_id': 51, # same on all Nodes for this virtual IP
    #             'priority': 100, # priority 100 == Master, higher will become new MASTER
    #             'advert_int': 1, # advertising interval in Sec
    #             'auth_type': 'PASS', # Password Authentication (only supported option for now)
    #             'auth_pass': 'mysecretpass', # Password to use max 8 chars - will be generated from the ip and the virtual_router_id
    #         },
    #     },
    # },
}

if node.has_bundle('apt'):
    defaults['apt'] = {
        'packages': {
            'keepalived': {'installed': True, },
        }
    }

@metadata_reactor
def generate_instances_from_interfaces(metadata):
    instances = {}
    for interface, interface_config in metadata.get('interfaces', {}).items():
        k_conf = interface_config.get('keepalived', {})
        if interface_config.get('shared_ip_addresses', []) == []:
            continue

        instances[f'VI_{interface}'] = {
            'interface': interface,
            'state': k_conf.get('state', 'MASTER'),
            'virtual_router_id': k_conf.get('virtual_router_id'),
            'priority': k_conf.get('priority', 100 if k_conf.get('state', 'MASTER') == "MASTER" else 10),
            'advert_int': k_conf.get('advert_int', 1),
            'auth_type': k_conf.get('auth_type', 'PASS'),
            'auth_pass': k_conf.get('auth_path', repo.vault.password_for('KEEPALIVED_PASSWORD_' + str(k_conf.get('virtual_router_id')) + '_' + ''.join(interface_config.get('shared_ip_addresses', []))).value[:8]),
            'virtual_ipaddress': interface_config.get('shared_ip_addresses'),
        }

    return {
        'keepalived': {
            'instances': instances,
        },
    }


@metadata_reactor
def add_iptables_rules(metadata):
    if not node.has_bundle("iptables"):
        raise DoNotRunAgain

    # todo: get from instances
    interfaces = []
    for instance in metadata.get('keepalived/instances', {}).values():
        interface = instance.get('interface', None)
        if interface and interface not in interfaces:
            interfaces += [interface, ]

    iptables_rules = {}
    for interface in interfaces:
        iptables_rules += repo.libs.iptables.accept(). \
                input(interface). \
                state_new(). \
                protocol('vrrp')

    return iptables_rules
