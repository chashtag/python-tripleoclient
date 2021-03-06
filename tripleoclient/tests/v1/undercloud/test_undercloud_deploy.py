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
import os

from heatclient import exc as hc_exc

from tripleoclient.tests.v1.test_plugin import TestPluginV1

# Load the plugin init module for the plugin list and show commands
from tripleoclient.v1 import undercloud_deploy


class FakePluginV1Client(object):
    def __init__(self, **kwargs):
        self.auth_token = kwargs['token']
        self.management_url = kwargs['endpoint']


class TestDeployUndercloud(TestPluginV1):

    def setUp(self):
        super(TestDeployUndercloud, self).setUp()

        # Get the command object to test
        self.cmd = undercloud_deploy.DeployUndercloud(self.app, None)

        undercloud_deploy.DeployUndercloud.heat_pid = mock.MagicMock(
            return_value=False)
        undercloud_deploy.DeployUndercloud.tht_render = '/twd/templates'
        undercloud_deploy.DeployUndercloud.tmp_env_dir = '/twd'
        undercloud_deploy.DeployUndercloud.tmp_env_file_name = 'tmp/foo'
        undercloud_deploy.DeployUndercloud.heat_launch = mock.MagicMock(
            side_effect=(lambda *x, **y: None))

        self.tc = self.app.client_manager.tripleoclient = mock.MagicMock()
        self.orc = self.tc.local_orchestration = mock.MagicMock()
        self.orc.stacks.create = mock.MagicMock(
            return_value={'stack': {'id': 'foo'}})

    @mock.patch('os.chmod')
    @mock.patch('os.path.exists')
    @mock.patch('tripleo_common.utils.passwords.generate_passwords')
    @mock.patch('yaml.safe_dump')
    def test_update_passwords_env_init(self, mock_dump, mock_pw,
                                       mock_exists, mock_chmod):
        pw_dict = {"GeneratedPassword": 123}
        pw_conf_path = os.path.join(self.temp_homedir,
                                    'undercloud-passwords.conf')
        t_pw_conf_path = os.path.join(
            self.temp_homedir, 'tripleo-undercloud-passwords.yaml')

        mock_pw.return_value = pw_dict
        mock_exists.return_value = False

        mock_open_context = mock.mock_open()
        with mock.patch('six.moves.builtins.open', mock_open_context):
            self.cmd._update_passwords_env(self.temp_homedir)

        mock_open_handle = mock_open_context()
        mock_dump.assert_called_once_with({'parameter_defaults': pw_dict},
                                          mock_open_handle,
                                          default_flow_style=False)
        chmod_calls = [mock.call(t_pw_conf_path, 0o600),
                       mock.call(pw_conf_path, 0o600)]
        mock_chmod.assert_has_calls(chmod_calls)

    @mock.patch('os.chmod')
    @mock.patch('os.path.exists')
    @mock.patch('tripleo_common.utils.passwords.generate_passwords')
    @mock.patch('yaml.safe_dump')
    def test_update_passwords_env_update(self, mock_dump, mock_pw,
                                         mock_exists, mock_chmod):
        pw_dict = {"GeneratedPassword": 123}
        pw_conf_path = os.path.join(self.temp_homedir,
                                    'undercloud-passwords.conf')
        t_pw_conf_path = os.path.join(
            self.temp_homedir, 'tripleo-undercloud-passwords.yaml')

        mock_pw.return_value = pw_dict
        mock_exists.return_value = True
        with open(t_pw_conf_path, 'w') as t_pw:
            t_pw.write('parameter_defaults: {ExistingKey: xyz}\n')

        with open(pw_conf_path, 'w') as t_pw:
            t_pw.write('[auth]\nundercloud_db_password = abc\n')

        self.cmd._update_passwords_env(self.temp_homedir,
                                       passwords={'ADefault': 456,
                                                  'ExistingKey':
                                                  'dontupdate'})
        expected_dict = {'parameter_defaults': {'GeneratedPassword': 123,
                                                'ExistingKey': 'xyz',
                                                'MysqlRootPassword': 'abc',
                                                'ADefault': 456}}
        mock_dump.assert_called_once_with(expected_dict,
                                          mock.ANY,
                                          default_flow_style=False)
        chmod_calls = [mock.call(t_pw_conf_path, 0o600),
                       mock.call(pw_conf_path, 0o600)]
        mock_chmod.assert_has_calls(chmod_calls)

    @mock.patch('heatclient.common.template_utils.'
                'process_environment_and_files', return_value=({}, {}),
                autospec=True)
    @mock.patch('heatclient.common.template_utils.'
                'get_template_contents', return_value=({}, {}),
                autospec=True)
    @mock.patch('heatclient.common.environment_format.'
                'parse', autospec=True, return_value=dict())
    @mock.patch('heatclient.common.template_format.'
                'parse', autospec=True, return_value=dict())
    @mock.patch('tripleoclient.v1.undercloud_deploy.DeployUndercloud.'
                '_setup_heat_environments', autospec=True)
    def test_deploy_tripleo_heat_templates_redir(self,
                                                 mock_setup_heat_envs,
                                                 mock_hc_templ_parse,
                                                 mock_hc_env_parse,
                                                 mock_hc_get_templ_cont,
                                                 mock_hc_process):
        parsed_args = self.check_parser(self.cmd,
                                        ['--local-ip', '127.0.0.1/8',
                                         '--templates', '/tmp/thtroot'], [])

        mock_setup_heat_envs.return_value = [
            './inside.yaml', '/tmp/thtroot/abs.yaml',
            '/tmp/thtroot/puppet/foo.yaml',
            '/tmp/thtroot/environments/myenv.yaml',
            '/tmp/thtroot42/notouch.yaml',
            '../outside.yaml']

        self.cmd._deploy_tripleo_heat_templates(self.orc, parsed_args)

        mock_hc_process.assert_has_calls([
            mock.call(env_path='./inside.yaml'),
            mock.call(env_path='/twd/templates/abs.yaml'),
            mock.call(env_path='/twd/templates/puppet/foo.yaml'),
            mock.call(env_path='/twd/templates/environments/myenv.yaml'),
            mock.call(env_path='/tmp/thtroot42/notouch.yaml'),
            mock.call(env_path='../outside.yaml')])

    @mock.patch('heatclient.common.template_utils.'
                'process_environment_and_files', return_value=({}, {}),
                autospec=True)
    @mock.patch('heatclient.common.template_utils.'
                'get_template_contents', return_value=({}, {}),
                autospec=True)
    @mock.patch('heatclient.common.environment_format.'
                'parse', autospec=True, return_value=dict())
    @mock.patch('heatclient.common.template_format.'
                'parse', autospec=True, return_value=dict())
    @mock.patch('tripleoclient.v1.undercloud_deploy.DeployUndercloud.'
                '_setup_heat_environments', autospec=True)
    @mock.patch('yaml.safe_dump', autospec=True)
    @mock.patch('yaml.safe_load', autospec=True)
    @mock.patch('six.moves.builtins.open')
    @mock.patch('tempfile.NamedTemporaryFile', autospec=True)
    def test_deploy_tripleo_heat_templates_rewrite(self,
                                                   mock_temp, mock_open,
                                                   mock_yaml_load,
                                                   mock_yaml_dump,
                                                   mock_setup_heat_envs,
                                                   mock_hc_templ_parse,
                                                   mock_hc_env_parse,
                                                   mock_hc_get_templ_cont,
                                                   mock_hc_process):
        def hc_process(*args, **kwargs):
            if 'abs.yaml' in kwargs['env_path']:
                raise hc_exc.CommandError
            else:
                return ({}, {})

        mock_hc_process.side_effect = hc_process

        parsed_args = self.check_parser(self.cmd,
                                        ['--local-ip', '127.0.0.1/8',
                                         '--templates', '/tmp/thtroot'], [])

        rewritten_env = {'resource_registry': {
            'OS::Foo::Bar': '/twd/outside.yaml',
            'OS::Foo::Baz': '/twd/templates/inside.yaml',
            'OS::Foo::Qux': '/twd/templates/abs.yaml',
            'OS::Foo::Quux': '/tmp/thtroot42/notouch.yaml',
            'OS::Foo::Corge': '/twd/templates/puppet/foo.yaml'
            }
        }
        myenv = {'resource_registry': {
            'OS::Foo::Bar': '../outside.yaml',
            'OS::Foo::Baz': './inside.yaml',
            'OS::Foo::Qux': '/tmp/thtroot/abs.yaml',
            'OS::Foo::Quux': '/tmp/thtroot42/notouch.yaml',
            'OS::Foo::Corge': '/tmp/thtroot/puppet/foo.yaml'
            }
        }
        mock_yaml_load.return_value = myenv

        mock_setup_heat_envs.return_value = [
            './inside.yaml', '/tmp/thtroot/abs.yaml',
            '/tmp/thtroot/puppet/foo.yaml',
            '/tmp/thtroot/environments/myenv.yaml',
            '../outside.yaml']

        self.cmd._deploy_tripleo_heat_templates(self.orc, parsed_args)

        mock_yaml_dump.assert_has_calls([mock.call(rewritten_env,
                                        default_flow_style=False)])

    @mock.patch('heatclient.common.template_utils.'
                'process_environment_and_files', return_value=({}, {}),
                autospec=True)
    @mock.patch('heatclient.common.template_utils.'
                'get_template_contents', return_value=({}, {}),
                autospec=True)
    @mock.patch('tripleoclient.utils.'
                'process_multiple_environments', autospec=True)
    @mock.patch('tripleoclient.v1.undercloud_deploy.DeployUndercloud.'
                '_update_passwords_env', autospec=True)
    @mock.patch('subprocess.check_call', autospec=True)
    @mock.patch('tempfile.mkdtemp', autospec=True, return_value='/twd')
    @mock.patch('shutil.copytree', autospec=True)
    def test_setup_heat_environments(self,
                                     mock_copy,
                                     mock_mktemp,
                                     mock_exec,
                                     mock_update_pass_env,
                                     mock_process_multiple_environments,
                                     mock_hc_get_templ_cont,
                                     mock_hc_process):

        parsed_args = self.check_parser(self.cmd,
                                        ['--local-ip', '127.0.0.1/8',
                                         '--templates', '/tmp/thtroot',
                                         '--output-dir', '/my',
                                         '-e', '/tmp/thtroot/puppet/foo.yaml',
                                         '-e', '/tmp/thtroot//docker/bar.yaml',
                                         '-e', '/tmp/thtroot42/notouch.yaml',
                                         '-e', '~/custom.yaml',
                                         '-e', 'something.yaml',
                                         '-e', '../../../outside.yaml'], [])
        expected_env = [
            '/twd/templates/overcloud-resource-registry-puppet.yaml',
            mock.ANY,
            '/twd/templates/environments/undercloud.yaml',
            '/twd/templates/environments/config-download-environment.yaml',
            '/twd/templates/environments/deployed-server-noop-ctlplane.yaml',
            '/tmp/thtroot/puppet/foo.yaml',
            '/tmp/thtroot//docker/bar.yaml',
            '/tmp/thtroot42/notouch.yaml',
            '~/custom.yaml',
            'something.yaml',
            '../../../outside.yaml',
            mock.ANY]

        environment = self.cmd._setup_heat_environments(parsed_args)

        self.assertEqual(environment, expected_env)
