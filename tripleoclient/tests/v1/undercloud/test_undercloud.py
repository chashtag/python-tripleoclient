#   Copyright 2015 Red Hat, Inc.
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#

import mock

from oslo_config import cfg
from oslo_config import fixture as oslo_fixture

from tripleoclient.tests.v1.test_plugin import TestPluginV1

# Load the plugin init module for the plugin list and show commands
from tripleoclient.v1 import undercloud


class FakePluginV1Client(object):
    def __init__(self, **kwargs):
        self.auth_token = kwargs['token']
        self.management_url = kwargs['endpoint']


class TestUndercloudInstall(TestPluginV1):

    def setUp(self):
        super(TestUndercloudInstall, self).setUp()

        conf = self.useFixture(oslo_fixture.Config(cfg.CONF))
        conf.config(container_images_file='/home/stack/foo.yaml')
        # Get the command object to test
        self.cmd = undercloud.InstallUndercloud(self.app, None)

    @mock.patch('subprocess.check_call', autospec=True)
    def test_undercloud_install(self, mock_subprocess):
        arglist = []
        verifylist = []
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        # DisplayCommandBase.take_action() returns two tuples
        self.cmd.take_action(parsed_args)

        mock_subprocess.assert_called_with(['instack-install-undercloud'])

    @mock.patch('subprocess.check_call', autospec=True)
    def test_undercloud_install_with_heat(self, mock_subprocess):
        arglist = ['--use-heat', '--no-validations']
        verifylist = []
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        # DisplayCommandBase.take_action() returns two tuples
        self.cmd.take_action(parsed_args)

        mock_subprocess.assert_called_with(
            ['sudo', 'openstack', 'undercloud',
             'deploy', '--local-domain=localdomain',
             '--local-ip=192.168.24.1/24',
             '--templates=/usr/share/openstack-tripleo-heat-templates/',
             '--heat-native', '-e', '/home/stack/foo.yaml', '-e',
             '/usr/share/openstack-tripleo-heat-templates/environments/'
             'services-docker/ironic.yaml',
             '-e',
             '/usr/share/openstack-tripleo-heat-templates/environments/'
             'services-docker/ironic-inspector.yaml', '-e',
             '/usr/share/openstack-tripleo-heat-templates/environments/'
             'services-docker/mistral.yaml', '-e',
             '/usr/share/openstack-tripleo-heat-templates/environments/'
             'services-docker/zaqar.yaml', '-e',
             '/usr/share/openstack-tripleo-heat-templates/environments/'
             'services-docker/tripleo-ui.yaml', '-e',
             '/usr/share/openstack-tripleo-heat-templates/environments/'
             'public-tls-undercloud.yaml',
             '--public-virtual-ip', '192.168.24.2',
             '--control-virtual-ip', '192.168.24.3', '-e',
             '/usr/share/openstack-tripleo-heat-templates/environments/'
             'tls-endpoints-public-ip.yaml', '-e',
             '/usr/share/openstack-tripleo-heat-templates/environments/'
             'use-dns-for-vips.yaml', '-e',
             '/usr/share/openstack-tripleo-heat-templates/environments/'
             'services-docker/undercloud-haproxy.yaml', '-e',
             '/usr/share/openstack-tripleo-heat-templates/environments/'
             'services-docker/undercloud-keepalived.yaml', '-e',
             '/usr/share/openstack-tripleo-heat-templates/environments/'
             'docker.yaml', '-e',
             '/usr/share/openstack-tripleo-heat-templates/environments/'
             'config-download-environment.yaml', '-e',
             '/usr/share/openstack-tripleo-heat-templates/environments/'
             'undercloud.yaml', '-e', '/tmp/undercloud_parameters.yaml',
             mock.ANY, '--debug'])


class TestUndercloudUpgrade(TestPluginV1):
    def setUp(self):
        super(TestUndercloudUpgrade, self).setUp()

        conf = self.useFixture(oslo_fixture.Config(cfg.CONF))
        conf.config(container_images_file='/home/stack/foo.yaml')
        # Get the command object to test
        self.cmd = undercloud.UpgradeUndercloud(self.app, None)

    @mock.patch('subprocess.check_call', autospec=True)
    def test_undercloud_upgrade(self, mock_subprocess):
        arglist = []
        verifylist = []
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        # DisplayCommandBase.take_action() returns two tuples
        self.cmd.take_action(parsed_args)

        mock_subprocess.assert_has_calls(
            [
                mock.call(['sudo', 'yum', 'update', '-y',
                           'instack-undercloud']),
                mock.call('instack-pre-upgrade-undercloud'),
                mock.call('instack-upgrade-undercloud'),
                mock.call(['sudo', 'systemctl', 'restart',
                          'openstack-nova-api'])
            ]
        )

    @mock.patch('subprocess.check_call', autospec=True)
    def test_undercloud_upgrade_with_heat(self, mock_subprocess):
        arglist = ['--use-heat', '--no-validations']
        verifylist = []
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        # DisplayCommandBase.take_action() returns two tuples
        self.cmd.take_action(parsed_args)

        mock_subprocess.assert_called_with(
            ['sudo', 'openstack', 'undercloud',
             'deploy', '--local-domain=localdomain',
             '--local-ip=192.168.24.1/24',
             '--templates=/usr/share/openstack-tripleo-heat-templates/',
             '-e',
             '/usr/share/openstack-tripleo-heat-templates/environments/'
             'major-upgrade-composable-steps-docker.yaml',
             '--heat-native', '-e', '/home/stack/foo.yaml', '-e',
             '/usr/share/openstack-tripleo-heat-templates/environments/'
             'services-docker/ironic.yaml',
             '-e',
             '/usr/share/openstack-tripleo-heat-templates/environments/'
             'services-docker/ironic-inspector.yaml', '-e',
             '/usr/share/openstack-tripleo-heat-templates/environments/'
             'services-docker/mistral.yaml', '-e',
             '/usr/share/openstack-tripleo-heat-templates/environments/'
             'services-docker/zaqar.yaml', '-e',
             '/usr/share/openstack-tripleo-heat-templates/environments/'
             'services-docker/tripleo-ui.yaml', '-e',
             '/usr/share/openstack-tripleo-heat-templates/environments/'
             'public-tls-undercloud.yaml',
             '--public-virtual-ip', '192.168.24.2',
             '--control-virtual-ip', '192.168.24.3', '-e',
             '/usr/share/openstack-tripleo-heat-templates/environments/'
             'tls-endpoints-public-ip.yaml', '-e',
             '/usr/share/openstack-tripleo-heat-templates/environments/'
             'use-dns-for-vips.yaml', '-e',
             '/usr/share/openstack-tripleo-heat-templates/environments/'
             'services-docker/undercloud-haproxy.yaml', '-e',
             '/usr/share/openstack-tripleo-heat-templates/environments/'
             'services-docker/undercloud-keepalived.yaml', '-e',
             '/usr/share/openstack-tripleo-heat-templates/environments/'
             'docker.yaml', '-e',
             '/usr/share/openstack-tripleo-heat-templates/environments/'
             'config-download-environment.yaml', '-e',
             '/usr/share/openstack-tripleo-heat-templates/environments/'
             'undercloud.yaml', '-e', '/tmp/undercloud_parameters.yaml',
             mock.ANY, '--debug'])
