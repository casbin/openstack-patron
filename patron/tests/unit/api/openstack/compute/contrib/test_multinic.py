# Copyright 2011 OpenStack Foundation
# All Rights Reserved.
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

import mock
import webob

from patron.api.openstack.compute.contrib import multinic as multinic_v2
from patron.api.openstack.compute.plugins.v3 import multinic as multinic_v21
from patron import compute
from patron import exception
from patron import objects
from patron import test
from patron.tests.unit.api.openstack import fakes


UUID = '70f6db34-de8d-4fbd-aafb-4065bdfa6114'
last_add_fixed_ip = (None, None)
last_remove_fixed_ip = (None, None)


def compute_api_add_fixed_ip(self, context, instance, network_id):
    global last_add_fixed_ip

    last_add_fixed_ip = (instance['uuid'], network_id)


def compute_api_remove_fixed_ip(self, context, instance, address):
    global last_remove_fixed_ip

    last_remove_fixed_ip = (instance['uuid'], address)


def compute_api_get(self, context, instance_id, want_objects=False,
                    expected_attrs=None):
    instance = objects.Instance()
    instance.uuid = instance_id
    instance.id = 1
    instance.vm_state = 'fake'
    instance.task_state = 'fake'
    instance.obj_reset_changes()
    return instance


class FixedIpTestV21(test.NoDBTestCase):
    controller_class = multinic_v21
    validation_error = exception.ValidationError

    def setUp(self):
        super(FixedIpTestV21, self).setUp()
        fakes.stub_out_networking(self.stubs)
        fakes.stub_out_rate_limiting(self.stubs)
        self.stubs.Set(compute.api.API, "add_fixed_ip",
                       compute_api_add_fixed_ip)
        self.stubs.Set(compute.api.API, "remove_fixed_ip",
                       compute_api_remove_fixed_ip)
        self.stubs.Set(compute.api.API, 'get', compute_api_get)
        self.controller = self.controller_class.MultinicController()
        self.fake_req = fakes.HTTPRequest.blank('')

    def test_add_fixed_ip(self):
        global last_add_fixed_ip
        last_add_fixed_ip = (None, None)

        body = dict(addFixedIp=dict(networkId='test_net'))
        resp = self.controller._add_fixed_ip(self.fake_req, UUID, body=body)
        # NOTE: on v2.1, http status code is set as wsgi_code of API
        # method instead of status_int in a response object.
        if isinstance(self.controller,
                      multinic_v21.MultinicController):
            status_int = self.controller._add_fixed_ip.wsgi_code
        else:
            status_int = resp.status_int
        self.assertEqual(status_int, 202)
        self.assertEqual(last_add_fixed_ip, (UUID, 'test_net'))

    def _test_add_fixed_ip_bad_request(self, body):
        self.assertRaises(self.validation_error,
                          self.controller._add_fixed_ip,
                          self.fake_req,
                          UUID, body=body)

    def test_add_fixed_ip_empty_network_id(self):
        body = {'addFixedIp': {'network_id': ''}}
        self._test_add_fixed_ip_bad_request(body)

    def test_add_fixed_ip_network_id_bigger_than_36(self):
        body = {'addFixedIp': {'network_id': 'a' * 37}}
        self._test_add_fixed_ip_bad_request(body)

    def test_add_fixed_ip_no_network(self):
        global last_add_fixed_ip
        last_add_fixed_ip = (None, None)

        body = dict(addFixedIp=dict())
        self._test_add_fixed_ip_bad_request(body)
        self.assertEqual(last_add_fixed_ip, (None, None))

    @mock.patch.object(compute.api.API, 'add_fixed_ip')
    def test_add_fixed_ip_no_more_ips_available(self, mock_add_fixed_ip):
        mock_add_fixed_ip.side_effect = exception.NoMoreFixedIps(net='netid')

        body = dict(addFixedIp=dict(networkId='test_net'))
        self.assertRaises(webob.exc.HTTPBadRequest,
                          self.controller._add_fixed_ip,
                          self.fake_req,
                          UUID, body=body)

    def test_remove_fixed_ip(self):
        global last_remove_fixed_ip
        last_remove_fixed_ip = (None, None)

        body = dict(removeFixedIp=dict(address='10.10.10.1'))
        resp = self.controller._remove_fixed_ip(self.fake_req, UUID, body=body)
        # NOTE: on v2.1, http status code is set as wsgi_code of API
        # method instead of status_int in a response object.
        if isinstance(self.controller,
                      multinic_v21.MultinicController):
            status_int = self.controller._remove_fixed_ip.wsgi_code
        else:
            status_int = resp.status_int
        self.assertEqual(status_int, 202)
        self.assertEqual(last_remove_fixed_ip, (UUID, '10.10.10.1'))

    def test_remove_fixed_ip_no_address(self):
        global last_remove_fixed_ip
        last_remove_fixed_ip = (None, None)

        body = dict(removeFixedIp=dict())
        self.assertRaises(self.validation_error,
                          self.controller._remove_fixed_ip,
                          self.fake_req,
                          UUID, body=body)
        self.assertEqual(last_remove_fixed_ip, (None, None))

    def test_remove_fixed_ip_invalid_address(self):
        body = {'removeFixedIp': {'address': ''}}
        self.assertRaises(self.validation_error,
                          self.controller._remove_fixed_ip,
                          self.fake_req,
                          UUID, body=body)

    @mock.patch.object(compute.api.API, 'remove_fixed_ip',
        side_effect=exception.FixedIpNotFoundForSpecificInstance(
            instance_uuid=UUID, ip='10.10.10.1'))
    def test_remove_fixed_ip_not_found(self, _remove_fixed_ip):

        body = {'removeFixedIp': {'address': '10.10.10.1'}}
        self.assertRaises(webob.exc.HTTPBadRequest,
                          self.controller._remove_fixed_ip,
                          self.fake_req,
                          UUID, body=body)


class FixedIpTestV2(FixedIpTestV21):
    controller_class = multinic_v2
    validation_error = webob.exc.HTTPBadRequest

    def test_remove_fixed_ip_invalid_address(self):
        # NOTE(cyeoh): This test is disabled for the V2 API because it is
        # has poorer input validation.
        pass


class MultinicPolicyEnforcementV21(test.NoDBTestCase):

    def setUp(self):
        super(MultinicPolicyEnforcementV21, self).setUp()
        self.controller = multinic_v21.MultinicController()
        self.req = fakes.HTTPRequest.blank('')

    def test_add_fixed_ip_policy_failed(self):
        rule_name = "os_compute_api:os-multinic"
        self.policy.set_rules({rule_name: "project:non_fake"})
        exc = self.assertRaises(
            exception.PolicyNotAuthorized,
            self.controller._add_fixed_ip, self.req, fakes.FAKE_UUID,
            body={'addFixedIp': {'networkId': fakes.FAKE_UUID}})
        self.assertEqual(
            "Policy doesn't allow %s to be performed." % rule_name,
            exc.format_message())

    def test_remove_fixed_ip_policy_failed(self):
        rule_name = "os_compute_api:os-multinic"
        self.policy.set_rules({rule_name: "project:non_fake"})
        exc = self.assertRaises(
            exception.PolicyNotAuthorized,
            self.controller._remove_fixed_ip, self.req, fakes.FAKE_UUID,
            body={'removeFixedIp': {'address': "10.0.0.1"}})
        self.assertEqual(
            "Policy doesn't allow %s to be performed." % rule_name,
            exc.format_message())
