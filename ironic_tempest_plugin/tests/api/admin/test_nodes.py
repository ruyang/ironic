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

import six
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

from ironic_tempest_plugin.common import waiters
from ironic_tempest_plugin.tests.api.admin import api_microversion_fixture
from ironic_tempest_plugin.tests.api.admin import base


class TestNodes(base.BaseBaremetalTest):
    """Tests for baremetal nodes."""

    def setUp(self):
        super(TestNodes, self).setUp()

        _, self.chassis = self.create_chassis()
        _, self.node = self.create_node(self.chassis['uuid'])

    def _assertExpected(self, expected, actual):
        # Check if not expected keys/values exists in actual response body
        for key, value in expected.items():
            if key not in ('created_at', 'updated_at'):
                self.assertIn(key, actual)
                self.assertEqual(value, actual[key])

    def _associate_node_with_instance(self):
        self.client.set_node_power_state(self.node['uuid'], 'power off')
        waiters.wait_for_bm_node_status(self.client, self.node['uuid'],
                                        'power_state', 'power off')
        instance_uuid = data_utils.rand_uuid()
        self.client.update_node(self.node['uuid'],
                                instance_uuid=instance_uuid)
        self.addCleanup(self.client.update_node,
                        uuid=self.node['uuid'], instance_uuid=None)
        return instance_uuid

    @decorators.idempotent_id('4e939eb2-8a69-4e84-8652-6fffcbc9db8f')
    def test_create_node(self):
        params = {'cpu_arch': 'x86_64',
                  'cpus': '12',
                  'local_gb': '10',
                  'memory_mb': '1024'}

        _, body = self.create_node(self.chassis['uuid'], **params)
        self._assertExpected(params, body['properties'])

    @decorators.idempotent_id('9ade60a4-505e-4259-9ec4-71352cbbaf47')
    def test_delete_node(self):
        _, node = self.create_node(self.chassis['uuid'])

        self.delete_node(node['uuid'])

        self.assertRaises(lib_exc.NotFound, self.client.show_node,
                          node['uuid'])

    @decorators.idempotent_id('55451300-057c-4ecf-8255-ba42a83d3a03')
    def test_show_node(self):
        _, loaded_node = self.client.show_node(self.node['uuid'])
        self._assertExpected(self.node, loaded_node)

    @decorators.idempotent_id('4ca123c4-160d-4d8d-a3f7-15feda812263')
    def test_list_nodes(self):
        _, body = self.client.list_nodes()
        self.assertIn(self.node['uuid'],
                      [i['uuid'] for i in body['nodes']])

    @decorators.idempotent_id('85b1f6e0-57fd-424c-aeff-c3422920556f')
    def test_list_nodes_association(self):
        _, body = self.client.list_nodes(associated=True)
        self.assertNotIn(self.node['uuid'],
                         [n['uuid'] for n in body['nodes']])

        self._associate_node_with_instance()

        _, body = self.client.list_nodes(associated=True)
        self.assertIn(self.node['uuid'], [n['uuid'] for n in body['nodes']])

        _, body = self.client.list_nodes(associated=False)
        self.assertNotIn(self.node['uuid'], [n['uuid'] for n in body['nodes']])

    @decorators.idempotent_id('18c4ebd8-f83a-4df7-9653-9fb33a329730')
    def test_node_port_list(self):
        _, port = self.create_port(self.node['uuid'],
                                   data_utils.rand_mac_address())
        _, body = self.client.list_node_ports(self.node['uuid'])
        self.assertIn(port['uuid'],
                      [p['uuid'] for p in body['ports']])

    @decorators.idempotent_id('72591acb-f215-49db-8395-710d14eb86ab')
    def test_node_port_list_no_ports(self):
        _, node = self.create_node(self.chassis['uuid'])
        _, body = self.client.list_node_ports(node['uuid'])
        self.assertEmpty(body['ports'])

    @decorators.idempotent_id('4fed270a-677a-4d19-be87-fd38ae490320')
    def test_update_node(self):
        props = {'cpu_arch': 'x86_64',
                 'cpus': '12',
                 'local_gb': '10',
                 'memory_mb': '128'}

        _, node = self.create_node(self.chassis['uuid'], **props)

        new_p = {'cpu_arch': 'x86',
                 'cpus': '1',
                 'local_gb': '10000',
                 'memory_mb': '12300'}

        _, body = self.client.update_node(node['uuid'], properties=new_p)
        _, node = self.client.show_node(node['uuid'])
        self._assertExpected(new_p, node['properties'])

    @decorators.idempotent_id('cbf1f515-5f4b-4e49-945c-86bcaccfeb1d')
    def test_validate_driver_interface(self):
        _, body = self.client.validate_driver_interface(self.node['uuid'])
        core_interfaces = ['power', 'deploy']
        for interface in core_interfaces:
            self.assertIn(interface, body)

    @decorators.idempotent_id('5519371c-26a2-46e9-aa1a-f74226e9d71f')
    def test_set_node_boot_device(self):
        self.client.set_node_boot_device(self.node['uuid'], 'pxe')

    @decorators.idempotent_id('9ea73775-f578-40b9-bc34-efc639c4f21f')
    def test_get_node_boot_device(self):
        body = self.client.get_node_boot_device(self.node['uuid'])
        self.assertIn('boot_device', body)
        self.assertIn('persistent', body)
        self.assertIsInstance(body['boot_device'], six.string_types)
        self.assertIsInstance(body['persistent'], bool)

    @decorators.idempotent_id('3622bc6f-3589-4bc2-89f3-50419c66b133')
    def test_get_node_supported_boot_devices(self):
        body = self.client.get_node_supported_boot_devices(self.node['uuid'])
        self.assertIn('supported_boot_devices', body)
        self.assertIsInstance(body['supported_boot_devices'], list)

    @decorators.idempotent_id('f63b6288-1137-4426-8cfe-0d5b7eb87c06')
    def test_get_console(self):
        _, body = self.client.get_console(self.node['uuid'])
        con_info = ['console_enabled', 'console_info']
        for key in con_info:
            self.assertIn(key, body)

    @decorators.idempotent_id('80504575-9b21-4670-92d1-143b948f9437')
    def test_set_console_mode(self):
        self.client.set_console_mode(self.node['uuid'], True)
        waiters.wait_for_bm_node_status(self.client, self.node['uuid'],
                                        'console_enabled', True)

    @decorators.idempotent_id('b02a4f38-5e8b-44b2-aed2-a69a36ecfd69')
    def test_get_node_by_instance_uuid(self):
        instance_uuid = self._associate_node_with_instance()
        _, body = self.client.show_node_by_instance_uuid(instance_uuid)
        self.assertEqual(1, len(body['nodes']))
        self.assertIn(self.node['uuid'], [n['uuid'] for n in body['nodes']])


class TestNodesVif(base.BaseBaremetalTest):

    min_microversion = '1.28'

    def setUp(self):
        super(TestNodesVif, self).setUp()

        _, self.chassis = self.create_chassis()
        _, self.node = self.create_node(self.chassis['uuid'])

    @decorators.idempotent_id('a3d319d0-cacb-4e55-a3dc-3fa8b74880f1')
    def test_vifs(self):
        self.useFixture(
            api_microversion_fixture.APIMicroversionFixture('1.28'))
        _, self.port = self.create_port(self.node['uuid'],
                                        data_utils.rand_mac_address())
        self.client.vif_attach(self.node['uuid'], 'test-vif')
        _, body = self.client.vif_list(self.node['uuid'])
        self.assertEqual(body, {'vifs': [{'id': 'test-vif'}]})
        self.client.vif_detach(self.node['uuid'], 'test-vif')

    @decorators.idempotent_id('a3d319d0-cacb-4e55-a3dc-3fa8b74880f2')
    def test_vif_already_set_on_extra(self):
        self.useFixture(
            api_microversion_fixture.APIMicroversionFixture('1.28'))
        _, self.port = self.create_port(self.node['uuid'],
                                        data_utils.rand_mac_address())
        patch = [{'path': '/extra/vif_port_id',
                  'op': 'add',
                  'value': 'test-vif'}]
        self.client.update_port(self.port['uuid'], patch)

        _, body = self.client.vif_list(self.node['uuid'])
        self.assertEqual(body, {'vifs': [{'id': 'test-vif'}]})

        self.assertRaises(lib_exc.Conflict, self.client.vif_attach,
                          self.node['uuid'], 'test-vif')

        self.client.vif_detach(self.node['uuid'], 'test-vif')
