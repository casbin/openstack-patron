# Copyright 2012 Nebula, Inc.
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

from oslo_config import cfg

from patron.api.metadata import password
from patron.api.openstack.compute.contrib import server_password \
    as server_password_v2
from patron.api.openstack.compute.plugins.v3 import server_password \
    as server_password_v21
from patron import compute
from patron import exception
from patron import test
from patron.tests.unit.api.openstack import fakes
from patron.tests.unit import fake_instance


CONF = cfg.CONF
CONF.import_opt('osapi_compute_ext_list', 'patron.api.openstack.compute.contrib')


class ServerPasswordTestV21(test.NoDBTestCase):
    content_type = 'application/json'
    server_password = server_password_v21
    delete_call = 'self.controller.clear'

    def setUp(self):
        super(ServerPasswordTestV21, self).setUp()
        fakes.stub_out_nw_api(self.stubs)
        self.stubs.Set(
            compute.api.API, 'get',
            lambda self, ctxt, *a, **kw:
                fake_instance.fake_instance_obj(
                ctxt,
                system_metadata={},
                expected_attrs=['system_metadata']))
        self.password = 'fakepass'
        self.controller = self.server_password.ServerPasswordController()
        self.fake_req = fakes.HTTPRequest.blank('')

        def fake_extract_password(instance):
            return self.password

        def fake_convert_password(context, password):
            self.password = password
            return {}

        self.stubs.Set(password, 'extract_password', fake_extract_password)
        self.stubs.Set(password, 'convert_password', fake_convert_password)

    def test_get_password(self):
        res = self.controller.index(self.fake_req, 'fake')
        self.assertEqual(res['password'], 'fakepass')

    def test_reset_password(self):
        eval(self.delete_call)(self.fake_req, 'fake')
        self.assertEqual(eval(self.delete_call).wsgi_code, 204)

        res = self.controller.index(self.fake_req, 'fake')
        self.assertEqual(res['password'], '')


class ServerPasswordTestV2(ServerPasswordTestV21):
    server_password = server_password_v2
    delete_call = 'self.controller.delete'


class ServerPasswordPolicyEnforcementV21(test.NoDBTestCase):

    def setUp(self):
        super(ServerPasswordPolicyEnforcementV21, self).setUp()
        self.controller = server_password_v21.ServerPasswordController()
        self.req = fakes.HTTPRequest.blank('')

    def _test_policy_failed(self, method, rule_name):
        self.policy.set_rules({rule_name: "project:non_fake"})
        exc = self.assertRaises(
            exception.PolicyNotAuthorized,
            method, self.req, fakes.FAKE_UUID)

        self.assertEqual(
            "Policy doesn't allow %s to be performed." % rule_name,
            exc.format_message())

    def test_get_password_policy_failed(self):
        rule_name = "os_compute_api:os-server-password"
        self._test_policy_failed(self.controller.index, rule_name)

    def test_clear_password_policy_failed(self):
        rule_name = "os_compute_api:os-server-password"
        self._test_policy_failed(self.controller.clear, rule_name)
