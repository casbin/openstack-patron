# Copyright 2013 NEC Corporation.  All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from patron.api.validation import parameter_types


create = {
    'type': 'object',
    'properties': {
        'keypair': {
            'type': 'object',
            'properties': {
                'name': parameter_types.name,
                'public_key': {'type': 'string'},
            },
            'required': ['name'],
            'additionalProperties': False,
        },
    },
    'required': ['keypair'],
    'additionalProperties': False,
}

create_v22 = {
    'type': 'object',
    'properties': {
        'keypair': {
            'type': 'object',
            'properties': {
                'name': parameter_types.name,
                'type': {
                    'type': 'string',
                    'enum': ['ssh', 'x509']
                },
                'public_key': {'type': 'string'},
            },
            'required': ['name'],
            'additionalProperties': False,
        },
    },
    'required': ['keypair'],
    'additionalProperties': False,
}

server_create = {
    'key_name': parameter_types.name,
}
