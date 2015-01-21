import unittest
import logging
from mock import patch, MagicMock, Mock
import cinderclient
import novaclient
import paramiko
import sys
import os

sys.path.append(os.path.dirname(__file__) + "/..")
from rednic.manage_utils import ManageUtils, ManageExeption

unitLogger = logging.getLogger('unittest')
unitLogger.setLevel(logging.DEBUG)
handler = logging.FileHandler("./manual_test.log")
unitLogger.addHandler(handler)


class mockNovaInstance(object):
    """
        object for use as instance description in mocks
        (used insted real server/instance in nova inside)
    """

    id = None

    name = None

    status = None

    key_name = None

    human_id = None

    networks = None

    def __init__(
        self, id=None, name=None, status=None, key_name=None,
        human_id=None, networks=None
    ):
        self.id = id
        self.name = name
        self.status = status
        self.key_name = key_name
        self.human_id = human_id
        self.networks = networks


class mockCinderVolume(object):
    """
        object for use as volume description in mocks
        (used insted real volume in cinder inside)
    """

    id = None

    size = None

    status = None

    display_name = None

    display_description = None

    loaded = False

    def is_loaded(self):
        return self.loaded

    volume_type = None

    bootable = None

    attachments = None

    def __init__(
        self, id=None, size=None, status=None, display_name=None,
        display_description=None, loaded=False, volume_type=None,
        bootable=None, attachments=None
    ):
            self.id = id
            self.size = size
            self.status = status
            self.display_name = display_name
            self.display_description = display_description
            self.loaded = loaded
            self.volume_type = volume_type
            self.bootable = bootable
            self.attachments = attachments


class TestMock(unittest.TestCase):

    manage_obj = None

    def __init_checks__(self, mock_cinder, mock_nova):
        """
            check init
        """
        # check init
        self.manage_obj = ManageUtils(
            "demo", "secrete", "demo",
            "http://10.0.2.15:5000/v2.0", unitLogger
        )

        # check correct calls inside
        mock_nova.assert_called_once_with(
            "2", "demo", "secrete", "demo",
            "http://10.0.2.15:5000/v2.0"
        )
        mock_cinder.assert_called_once_with(
            "1", "demo", "secrete", "demo",
            "http://10.0.2.15:5000/v2.0"
        )

    def testCheckInit(self):
        """
            check correct init for managment object
        """
        with patch.object(
            cinderclient.client, 'Client', return_value=Mock()
        ) as mock_cinder:
            with patch.object(
                novaclient.client, 'Client', return_value=Mock()
            ) as mock_nova:
                self.__init_checks__(mock_cinder, mock_nova)

    def __compare_instance__(self, result, origin):
        """
            compare instances in result and set in mock
        """
        self.assertEqual(result["id"], origin.id)
        self.assertEqual(result["name"], origin.name)
        self.assertEqual(result["status"], origin.status)
        self.assertEqual(result["key_name"], origin.key_name)
        self.assertEqual(result["human_id"], origin.human_id)
        self.assertEqual(result["networks"], origin.networks)

    def __compare_volume__(self, result, origin):
        """
            compare volumes in result and set in mock
        """
        self.assertEqual(
            result["id"], origin.id
        )
        self.assertEqual(
            result["size"], origin.size
        )
        self.assertEqual(
            result["status"], origin.status
        )
        self.assertEqual(
            result["name"], origin.display_name
        )
        self.assertEqual(
            result["description"], origin.display_description
        )
        self.assertEqual(
            result["loaded"], origin.is_loaded()
        )
        self.assertEqual(
            result["type"], origin.volume_type
        )
        self.assertEqual(
            result["boot"], origin.bootable
        )
        self.assertEqual(
            result["attach"], origin.attachments
        )

    def testInstanceGet(self):
        """
            test for instance get
        """
        will_be_nova = Mock()
        will_be_cinder = Mock()
        instance = mockNovaInstance(
            id="id", name="name", status="status",
            key_name="key_name",  human_id="human_id",
            networks="networks"
        )
        with patch.object(
            cinderclient.client, 'Client', return_value=will_be_cinder
        ) as mock_cinder:
            with patch.object(
                novaclient.client, 'Client', return_value=will_be_nova
            ) as mock_nova:
                self.__init_checks__(mock_cinder, mock_nova)

                # get instance by id
                will_be_nova.servers.get = MagicMock(
                    return_value=instance
                )
                res_instance = self.manage_obj.instance_get(ins_id="id")
                will_be_nova.servers.get.assert_called_with("id")
                self.__compare_instance__(res_instance, instance)

                # check get instance by name
                will_be_nova.servers.list = MagicMock(
                    return_value=[instance]
                )
                res_instance = self.manage_obj.instance_get(name="name")
                will_be_nova.servers.list.assert_called_with()
                self.__compare_instance__(res_instance, instance)

    def testInstanceList(self):
        """
            check list instances
        """
        will_be_nova = Mock()
        instance = mockNovaInstance(
            id="id", name="name", status="status",
            key_name="key_name",  human_id="human_id",
            networks="networks"
        )
        with patch.object(
            cinderclient.client, 'Client', return_value=Mock()
        ) as mock_cinder:
            with patch.object(
                novaclient.client, 'Client', return_value=will_be_nova
            ) as mock_nova:
                self.__init_checks__(mock_cinder, mock_nova)
                will_be_nova.servers.list = MagicMock(
                    return_value=[instance]
                )
                list_instances = self.manage_obj.instance_list()
                will_be_nova.servers.list.assert_called_with()
                self.assertIsNotNone(list_instances)
                self.assertEqual(len(list_instances), 1)
                self.__compare_instance__(list_instances[0], instance)

    def testVolumeAttachId(self):
        """
            check attach by id
        """
        # some objects for replace cinder and nova
        will_be_cinder = Mock()
        will_be_nova = Mock()
        # object that will replace volume
        volume = mockCinderVolume(
            id="id", size="size", status="status",
            display_name="display_name",
            display_description="display_description",
            loaded="loaded", volume_type="volume_type",
            bootable="bootable", attachments="attachments"
        )
        with patch.object(
            cinderclient.client, 'Client', return_value=will_be_cinder
        ) as mock_cinder:
            with patch.object(
                novaclient.client, 'Client', return_value=will_be_nova
            ) as mock_nova:
                self.__init_checks__(mock_cinder, mock_nova)
                # prepere mock functions for get by ids
                will_be_cinder.volumes.get = MagicMock(
                    return_value=volume
                )
                volume.attach = MagicMock(return_value=False)
                # real run
                res_volume = self.manage_obj.volume_attach(
                    "/some/place", vol_id="id", ins_id="id"
                )
                self.__compare_volume__(res_volume, volume)
                # check calls
                will_be_cinder.volumes.get.assert_called_with("id")
                volume.attach.assert_called_with(
                    "id", "/some/place"
                )

    def testVolumeAttachName(self):
        """
            check attach by name
        """
        # some objects for replace cinder and nova
        will_be_cinder = Mock()
        will_be_nova = Mock()
        # object that will replace volume and instance
        instance = mockNovaInstance(
            id="id", name="name", status="status",
            key_name="key_name",  human_id="human_id",
            networks="networks"
        )
        volume = mockCinderVolume(
            id="id", size="size", status="status",
            display_name="display_name",
            display_description="display_description",
            loaded="loaded", volume_type="volume_type",
            bootable="bootable", attachments="attachments"
        )
        with patch.object(
            cinderclient.client, 'Client', return_value=will_be_cinder
        ) as mock_cinder:
            with patch.object(
                novaclient.client, 'Client', return_value=will_be_nova
            ) as mock_nova:
                self.__init_checks__(mock_cinder, mock_nova)

                # prepere mock functions for get by name
                will_be_cinder.volumes.get = MagicMock(
                    return_value=volume
                )
                volume.attach = MagicMock(return_value=False)
                will_be_cinder.volumes.list = MagicMock(
                    return_value=[volume]
                )
                will_be_nova.servers.list = MagicMock(
                    return_value=[instance]
                )
                # real run
                with self.assertRaises(ManageExeption):
                    # wrong name
                    self.manage_obj.volume_attach(
                        "/some/place", vol_name="name", ins_name="name"
                    )
                # correct name
                res_volume = self.manage_obj.volume_attach(
                    "/some/place", vol_name="display_name", ins_name="name"
                )
                self.__compare_volume__(res_volume, volume)
                # check calls
                will_be_cinder.volumes.get.assert_called_with("id")
                volume.attach.assert_called_with(
                    "id", "/some/place"
                )

    def testVolumeCreate(self):
        # some objects for replace cinder and nova
        will_be_cinder = Mock()
        will_be_nova = Mock()
        volume = mockCinderVolume(
            id="id", size="size", status="status",
            display_name="display_name",
            display_description="display_description",
            loaded="loaded", volume_type="volume_type",
            bootable="bootable", attachments="attachments"
        )
        with patch.object(
            cinderclient.client, 'Client', return_value=will_be_cinder
        ) as mock_cinder:
            with patch.object(
                novaclient.client, 'Client', return_value=will_be_nova
            ) as mock_nova:
                self.__init_checks__(mock_cinder, mock_nova)
                # create mocks for create
                will_be_cinder.volumes.create = MagicMock(
                    return_value=volume
                )
                # real run
                res_volume = self.manage_obj.volume_create(
                    "size", "new_name", "desc"
                )
                # compare calls and results
                self.__compare_volume__(res_volume, volume)
                will_be_cinder.volumes.create.assert_called_with(
                    display_name='new_name', display_description='desc',
                    size='size'
                )

    def testVolumeGetId(self):
        """
            check get volume by id
        """
        # some objects for replace cinder and nova
        will_be_cinder = Mock()
        will_be_nova = Mock()
        volume = mockCinderVolume(
            id="id", size="size", status="status",
            display_name="display_name",
            display_description="display_description",
            loaded="loaded", volume_type="volume_type",
            bootable="bootable", attachments="attachments"
        )
        with patch.object(
            cinderclient.client, 'Client', return_value=will_be_cinder
        ) as mock_cinder:
            with patch.object(
                novaclient.client, 'Client', return_value=will_be_nova
            ) as mock_nova:
                self.__init_checks__(mock_cinder, mock_nova)
                # create mocks for get
                will_be_cinder.volumes.get = MagicMock(
                    return_value=volume
                )
                # real run
                res_volume = self.manage_obj.volume_get("id")
                # compare calls and results
                self.__compare_volume__(res_volume, volume)
                will_be_cinder.volumes.get.assert_called_with("id")

    def testVolumeGetName(self):
        """
            check get volume by name
        """
        # some objects for replace cinder and nova
        will_be_cinder = Mock()
        will_be_nova = Mock()
        volume = mockCinderVolume(
            id="id", size="size", status="status",
            display_name="display_name",
            display_description="display_description",
            loaded="loaded", volume_type="volume_type",
            bootable="bootable", attachments="attachments"
        )
        with patch.object(
            cinderclient.client, 'Client', return_value=will_be_cinder
        ) as mock_cinder:
            with patch.object(
                novaclient.client, 'Client', return_value=will_be_nova
            ) as mock_nova:
                self.__init_checks__(mock_cinder, mock_nova)
                # create mocks for get
                will_be_cinder.volumes.list = MagicMock(
                    return_value=[volume]
                )
                # real run
                with self.assertRaises(ManageExeption):
                    # wrong name
                    self.manage_obj.volume_get(name="id")
                res_volume = self.manage_obj.volume_get(
                    name="display_name"
                )
                # compare calls and results
                self.__compare_volume__(res_volume, volume)
                will_be_cinder.volumes.list.assert_called_with()

    def testVolumeDeleteId(self):
        """
            check delete volume by id
        """
        # some objects for replace cinder and nova
        will_be_cinder = Mock()
        will_be_nova = Mock()
        volume = mockCinderVolume(
            id="id", size="size", status="status",
            display_name="display_name",
            display_description="display_description",
            loaded="loaded", volume_type="volume_type",
            bootable="bootable", attachments="attachments"
        )
        with patch.object(
            cinderclient.client, 'Client', return_value=will_be_cinder
        ) as mock_cinder:
            with patch.object(
                novaclient.client, 'Client', return_value=will_be_nova
            ) as mock_nova:
                self.__init_checks__(mock_cinder, mock_nova)
                # create mocks for get
                will_be_cinder.volumes.get = MagicMock(
                    return_value=volume
                )
                will_be_cinder.volumes.delete = MagicMock(
                    return_value="Correct"
                )
                # real run
                result = self.manage_obj.volume_delete("id")
                self.assertEqual("Correct", result)
                will_be_cinder.volumes.get.assert_called_with("id")
                will_be_cinder.volumes.delete.assert_called_with(volume)

    def testVolumeDeleteName(self):
        """
            check delete volume by name
        """
        # some objects for replace cinder and nova
        will_be_cinder = Mock()
        will_be_nova = Mock()
        volume = mockCinderVolume(
            id="id", size="size", status="status",
            display_name="display_name",
            display_description="display_description",
            loaded="loaded", volume_type="volume_type",
            bootable="bootable", attachments="attachments"
        )
        with patch.object(
            cinderclient.client, 'Client', return_value=will_be_cinder
        ) as mock_cinder:
            with patch.object(
                novaclient.client, 'Client', return_value=will_be_nova
            ) as mock_nova:
                self.__init_checks__(mock_cinder, mock_nova)
                # create mocks for get
                will_be_cinder.volumes.list = MagicMock(
                    return_value=[volume]
                )
                will_be_cinder.volumes.get = MagicMock(
                    return_value=volume
                )
                will_be_cinder.volumes.delete = MagicMock(
                    return_value="Correct"
                )
                # real run
                result = self.manage_obj.volume_delete(name="display_name")
                self.assertEqual("Correct", result)
                will_be_cinder.volumes.get.assert_called_with("id")
                will_be_cinder.volumes.delete.assert_called_with(volume)
                will_be_cinder.volumes.list.assert_called_with()

    def testVolumeDetachId(self):
        """
            check detach volume by id
        """
        # some objects for replace cinder and nova
        will_be_cinder = Mock()
        will_be_nova = Mock()
        volume = mockCinderVolume(
            id="id", size="size", status="status",
            display_name="display_name",
            display_description="display_description",
            loaded="loaded", volume_type="volume_type",
            bootable="bootable", attachments="attachments"
        )
        with patch.object(
            cinderclient.client, 'Client', return_value=will_be_cinder
        ) as mock_cinder:
            with patch.object(
                novaclient.client, 'Client', return_value=will_be_nova
            ) as mock_nova:
                self.__init_checks__(mock_cinder, mock_nova)
                # create mocks for get
                will_be_cinder.volumes.get = MagicMock(
                    return_value=volume
                )
                will_be_cinder.volumes.detach = MagicMock(
                    return_value="Correct"
                )
                # real run
                result = self.manage_obj.volume_detach("id")
                self.assertEqual("Correct", result)
                will_be_cinder.volumes.get.assert_called_with("id")
                will_be_cinder.volumes.detach.assert_called_with(volume)

    def testVolumeDetachName(self):
        """
            check detach volume by name
        """
        # some objects for replace cinder and nova
        will_be_cinder = Mock()
        will_be_nova = Mock()
        volume = mockCinderVolume(
            id="id", size="size", status="status",
            display_name="display_name",
            display_description="display_description",
            loaded="loaded", volume_type="volume_type",
            bootable="bootable", attachments="attachments"
        )
        with patch.object(
            cinderclient.client, 'Client', return_value=will_be_cinder
        ) as mock_cinder:
            with patch.object(
                novaclient.client, 'Client', return_value=will_be_nova
            ) as mock_nova:
                self.__init_checks__(mock_cinder, mock_nova)
                # create mocks for get
                will_be_cinder.volumes.list = MagicMock(
                    return_value=[volume]
                )
                will_be_cinder.volumes.get = MagicMock(
                    return_value=volume
                )
                will_be_cinder.volumes.detach = MagicMock(
                    return_value="Correct"
                )
                # real run
                result = self.manage_obj.volume_detach(name="display_name")
                self.assertEqual("Correct", result)
                will_be_cinder.volumes.get.assert_called_with("id")
                will_be_cinder.volumes.detach.assert_called_with(volume)
                will_be_cinder.volumes.list.assert_called_with()

    @patch.object(novaclient.client, 'Client')
    @patch.object(cinderclient.client, 'Client')
    def testVolumeFormat(self, mock_cinder, mock_nova):
        """
            test ssh/connect logic
        """
        # add minimal check for cinder/nova connect
        self.__init_checks__(mock_cinder, mock_nova)
        key = open(
            os.path.dirname(__file__) + "/../configs/cloud.key"
        )
        # ssh mock
        will_be_ssh = Mock()
        will_be_ssh.set_missing_host_key_policy = MagicMock()
        will_be_ssh.connect = MagicMock()
        # channel mock
        channel_mock = Mock()
        channel_mock.get_pty = MagicMock()
        channel_mock.exec_command = MagicMock()
        channel_mock.recv = MagicMock(return_value="RECV\nOK")
        # transport mock
        transport_mock = MagicMock()
        transport_mock.open_session = MagicMock(return_value=channel_mock)
        will_be_ssh.get_transport = MagicMock(return_value=transport_mock)

        with patch.object(
            paramiko, 'SSHClient', return_value=will_be_ssh
        ) as mock_ssh_client:
            with patch.object(
                paramiko, 'AutoAddPolicy', return_value="I'm policy"
            ) as mock_policy:
                with patch.object(
                    paramiko.RSAKey, 'from_private_key', return_value="secret"
                ) as mock_rsa_key:
                    result = self.manage_obj.volume_format(
                        "mount_point", key, "username", "ins_ip"
                    )
                    mock_ssh_client.assert_called_with()
                    mock_policy.assert_called_with()
                    will_be_ssh.set_missing_host_key_policy.assert_called_with(
                        "I'm policy"
                    )
                    mock_rsa_key.assert_called_with(key)
                    will_be_ssh.connect.assert_called_with(
                        'ins_ip', username='username', pkey='secret'
                    )
                    will_be_ssh.get_transport.assert_called_with()
                    transport_mock.open_session.assert_called_with()
                    channel_mock.get_pty.assert_called_with()
                    channel_mock.exec_command.assert_called_with(
                        "sudo /sbin/mkfs.ext4 mount_point && " +
                        "echo OK || echo FAIL"
                    )
                    self.assertEqual(result, "RECV\nOK")
        key.close()

    def testVolumeList(self):
        """
            test list call
        """

        will_be_cinder = Mock()

        with patch.object(
            cinderclient.client, 'Client', return_value=will_be_cinder
        ) as mock_cinder:
            with patch.object(
                novaclient.client, 'Client', return_value=Mock()
            ) as mock_nova:

                self.__init_checks__(mock_cinder, mock_nova)

                volume = mockCinderVolume(
                    id="id", size="size", status="status",
                    display_name="display_name",
                    display_description="display_description",
                    loaded="loaded", volume_type="volume_type",
                    bootable="bootable", attachments="attachments"
                )

                will_be_cinder.volumes.list = MagicMock(return_value=[volume])

                list_volumes = self.manage_obj.volume_list()

                will_be_cinder.volumes.list.assert_called_with()

                # check correct convert
                self.assertIsNotNone(list_volumes)
                self.assertEqual(len(list_volumes), 1)
                self.__compare_volume__(list_volumes[0], volume)

if __name__ == '__main__':
    unittest.main()
