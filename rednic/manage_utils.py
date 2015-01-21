# code for manage cinder volumes
from cinderclient import client as cinder_client
from cinderclient import exceptions as cinder_exceptions
from novaclient import client as nova_client
import paramiko
import logging


class ManageExeption(BaseException):
    """
        some exeption with communication
    """
    pass


class ManageUtils(object):
    """ Collection of tools for manage cinder volumes """

    # connection to cinder
    __cinder__ = None

    # connection to nova
    __nova__ = None

    # logging object
    __log__ = None

    def __init__(self, user, password, tenant, auth_url, log=None):
        """ Connect to cinder and nova:

        Args:
            user: user name in opensack
            password: password for this user
            tenant: project name
            auth_url: authentication url
            log: logging object that can be used for logging,
                can be None
        """
        self.__cinder__ = cinder_client.Client(
            '1', user, password, tenant, auth_url
        )

        self.__nova__ = nova_client.Client(
            '2', user, password, tenant, auth_url
        )

        if log:
            self.__log__ = log
        else:
            self.__log__ = logging.getLogger('rednic.manage_utils')

    def __instance_convert__(self, instance):
        """ Convert internal instance description to dict format.

        Args:
            instance - object to convert

        Returns:
            dictionary with all meaningful information
        """

        if not instance:
            self.__log__.error("empty instance")
            return None
        return {
            "id": instance.id,
            "name": instance.name,
            "status": instance.status,
            "key_name": instance.key_name,
            "human_id": instance.human_id,
            "networks": instance.networks
        }

    def __volume_convert__(self, volume):
        """ Convert internal volume description to dict format.

        Args:
            volume - object to convert

        Returns:
            dictionary with all meaningful information
        """
        if not volume:
            self.__log__.error("empty volume")
            return volume
        return {
            "id": volume.id,
            "size": volume.size,
            "status": volume.status,
            "name": volume.display_name,
            "description": volume.display_description,
            "loaded": volume.is_loaded(),
            "type": volume.volume_type,
            "boot": volume.bootable,
            "attach": volume.attachments
        }

    def volume_list(self):
        """get list of existed volumes

        Returns:
            list of dictionaries with volumes description
        """
        self.__log__.debug("get list volumes")

        volumes = self.__cinder__.volumes.list()

        return [self.__volume_convert__(v) for v in volumes]

    def volume_create(self, size, name=None, description=None):
        """create volume

        Args:
            name: name of new volume
            description: description for new volume

        Returns:
            dictionary with description of new volume
        """
        self.__log__.debug("create volume")

        return self.__volume_convert__(
            self.__cinder__.volumes.create(
                size=size,
                display_name=name,
                display_description=description
            )
        )

    def volume_get(self, vol_id=None, name=None):
        """get volume by vol_id or name

        Args:
            vol_id: volume id for search,
                    much faster and have higher priority than name
            name:
                volume name for search
        Returns:
            volume as dictionary

        Raises:
            ManageExeption: in case when can't get volume
        """
        if vol_id:
            self.__log__.debug("get volume by vol_id")
            try:
                return self.__volume_convert__(
                    self.__cinder__.volumes.get(vol_id)
                )
            except cinder_exceptions.NotFound:
                raise ManageExeption()
        else:
            self.__log__.debug("get volume by name")
            for volume in self.volume_list():
                if volume['name'] == name:
                    return volume
        raise ManageExeption()

    def instance_get(self, ins_id=None, name=None):
        """ get instance by ins_id or name,

        Args:
            ins_id - mush faster and have priority

        Returns:
            instance description in dictionary format

        Raises:
            ManageExeption: in case when can't get instance
        """
        if ins_id:
            self.__log__.debug("get instance by ins_id")
            try:
                return self.__instance_convert__(
                    self.__nova__.servers.get(ins_id)
                )
            except cinder_exceptions.NotFound:
                raise ManageExeption()
        else:
            self.__log__.debug("get instance by name")
            for instance in self.instance_list():
                if instance['name'] == name:
                    return instance
        raise ManageExeption()

    def instance_attach_ip(self, ip, ins_id=None, name=None):
        """ attach some ip to instance

        Args:
            ip: ip that will be used
            ins_id: id of instance
            name: instance name

        Raises:
            ManageExeption: in case when can't attach ip
        """
        self.__log__.debug("attach ip")

        if name:
            internal_instance = self.instance_get(name=name)
            ins_id = internal_instance['id']

        instance = self.__nova__.servers.get(ins_id)
        try:
            instance.add_floating_ip(ip)
        except cinder_exceptions.NotFound:
            raise ManageExeption()

    def instance_detach_ip(self, ip, ins_id=None, name=None):
        """ detach some ip from instance

        Args:
            ip: ip that will be used
            ins_id: id of instance
            name: instance name

        Raises:
            ManageExeption: in case when can't detach ip
        """
        self.__log__.debug("attach ip")

        if name:
            internal_instance = self.instance_get(name=name)
            ins_id = internal_instance['id']

        instance = self.__nova__.servers.get(ins_id)
        try:
            instance.remove_floating_ip(ip)
        except cinder_exceptions.NotFound:
            raise ManageExeption()

    def volume_detach(self, vol_id=None, name=None):
        """detach volume by vol_id or name

        Args:
            vol_id: volume id for detach,
                    much faster and have higher priority than name
            name:
                volume name for detach

        Raises:
            ManageExeption: in case when can't detach volume
        """
        if vol_id:
            self.__log__.debug("delete volume by vol_id")
            volume = self.__cinder__.volumes.get(vol_id)
        else:
            self.__log__.debug("delete volume by name")
            # use our get for get volume by name
            internal_volume = self.volume_get(name=name)
            volume = self.__cinder__.volumes.get(internal_volume['id'])
        try:
            return self.__cinder__.volumes.detach(volume)
        except cinder_exceptions.BadRequest:
                raise ManageExeption()

    def volume_delete(self, vol_id=None, name=None):
        """drop volume by vol_id or name

        Args:
            vol_id: volume id for delete,
                    much faster and have higher priority than name
            name:
                volume name for delete

        Raises:
            ManageExeption: in case when can't drop volume
        """
        if vol_id:
            self.__log__.debug("delete volume by vol_id")
            volume = self.__cinder__.volumes.get(vol_id)
        else:
            self.__log__.debug("delete volume by name")
            # use our get for get volume by name
            internal_volume = self.volume_get(name=name)
            volume = self.__cinder__.volumes.get(internal_volume['id'])
        try:
            return self.__cinder__.volumes.delete(volume)
        except cinder_exceptions.BadRequest:
                raise ManageExeption()

    def instance_list(self):
        """ get full list of avaible instnaces

        Returns:
            list of dictionaries with instances description
        """
        instances = self.__nova__.servers.list()
        return [
            self.__instance_convert__(i) for i in instances
        ]

    def volume_attach(
        self,
        mount_point,
        vol_id=None, vol_name=None,
        ins_id=None, ins_name=None,
    ):
        """attach volume to instance

        Args:
            mount_point: dev name for new attachment
            vol_id: volume id,
                much faster and have higher priority than vol_name
            vol_name:
                volume name for search
            ins_id: instance id,
                much faster and have higher priority than ins_name
            ins_name:
                instance name
        Returns:
            volume as dictionary

        Raises:
            ManageExeption: in case when can't get volume or instance
        """
        if not vol_id:
            internal_volume = self.volume_get(name=vol_name)
            vol_id = internal_volume['id']

        volume = self.__cinder__.volumes.get(vol_id)

        if not ins_id:
            internal_instance = self.instance_get(name=ins_name)
            ins_id = internal_instance['id']

        volume.attach(ins_id, mount_point)

        return self.volume_get(vol_id=vol_id)

    def volume_format(
        self, mount_point, key_file, username, ins_ip
    ):
        """connect by ssh to instance and format volume

        Args:
            mount_point: dev name for format
            key_file: file handler for private key,
            username: user name on instance
            ins_ip: ip for connect

        Raises:
            ManageExeption: in case when can't get volume
        """
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        buff = ""
        with key_file:
            ssh.connect(
                ins_ip, username=username,
                pkey=paramiko.RSAKey.from_private_key(key_file)
            )
            chan = ssh.get_transport().open_session()
            chan.get_pty()
            chan.exec_command(
                'sudo /sbin/mkfs.ext4 %s && echo OK || echo FAIL' % (
                    mount_point
                )
            )
            buff += chan.recv(80)
            while buff.find("\nOK") == -1 and buff.find("\nFAIL") == -1:
                buff += chan.recv(80)
            chan.close()
        ssh.close()
        return buff
