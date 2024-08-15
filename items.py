
svc_systemd = {
        "keepalived": {
            'needs': ['pkg_apt:keepalived'],
            }
        }

files = {
    '/etc/keepalived/keepalived.conf': {
        'content_type': 'jinja2',
        'mode': "0640",
        'owner': 'root',
        'group': 'root',
        'context': {
            'instances': node.metadata.get('keepalived/instances', {}),
        },
        'triggers': [
            "svc_systemd:keepalived:restart"
        ],
    }
}
