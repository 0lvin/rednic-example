# code for manage cinder volumes
from cinderclient import client as cinder_client
from cinderclient import exceptions as cinder_exceptions
from novaclient import client as nova_client
import paramiko
import logging


class manage_exeption(BaseException):
    """
        some exeption with communication
    """
    pass


class manage_utils(object):

    cinder = None

    nova = None

    log = None

    def __init__(self, user, password, tenant, auth_url, log=None):

        self.cinder = cinder_client.Client(
            '1', user, password, tenant, auth_url
        )

        self.nova = nova_client.Client(
            '2', user, password, tenant, auth_url
        )

        if log:
            self.log = log
        else:
            self.log = logging.getLogger('rednic.manage_utils')

    def __instance_convert__(self, instance):
        if not instance:
            self.log.error("empty instance")
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
        if not volume:
            self.log.error("empty volume")
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
        """
            get list of existed volumes
        """
        self.log.debug("get list volumes")

        volumes = self.cinder.volumes.list()

        return [self.__volume_convert__(v) for v in volumes]

    def volume_create(self, size, name=None, description=None):
        """
            create volume
        """
        self.log.debug("create volume")

        return self.__volume_convert__(
            self.cinder.volumes.create(
                size=size,
                display_name=name,
                display_description=description
            )
        )

    def volume_get(self, vol_id=None, name=None):
        """
            get volume by vol_id or name,
            vol_id - mush faster and have priority

            return volume or raise manage_exeption
        """
        if vol_id:
            self.log.debug("get volume by vol_id")
            try:
                return self.__volume_convert__(
                    self.cinder.volumes.get(vol_id)
                )
            except cinder_exceptions.NotFound:
                raise manage_exeption()
        else:
            self.log.debug("get volume by name")
            for volume in self.volume_list():
                if volume['name'] == name:
                    return volume
        raise manage_exeption()

    def instance_get(self, ins_id=None, name=None):
        """
            get instance by ins_id or name,
            ins_id - mush faster and have priority

            return instance or raise manage_exeption
        """
        if ins_id:
            self.log.debug("get instance by ins_id")
            try:
                return self.__instance_convert__(
                    self.nova.servers.get(ins_id)
                )
            except cinder_exceptions.NotFound:
                raise manage_exeption()
        else:
            self.log.debug("get instance by name")
            for instance in self.instance_list():
                if instance['name'] == name:
                    return instance
        raise manage_exeption()

    def volume_detach(self, vol_id=None, name=None):
        """
            deatach volume by vol_id or name,
            vol_id - mush faster and have priority

            return volume or raise manage_exeption
        """
        if vol_id:
            self.log.debug("delete volume by vol_id")
            volume = self.cinder.volumes.get(vol_id)
        else:
            self.log.debug("delete volume by name")
            # use our get for get volume by name
            internal_volume = self.volume_get(name=name)
            volume = self.cinder.volumes.get(internal_volume['id'])
        try:
            return self.cinder.volumes.detach(volume)
        except cinder_exceptions.BadRequest:
                raise manage_exeption()

    def volume_delete(self, vol_id=None, name=None):
        """
            drop volume by vol_id or name,
            vol_id - mush faster and have priority

            return volume or raise manage_exeption
        """
        if vol_id:
            self.log.debug("delete volume by vol_id")
            volume = self.cinder.volumes.get(vol_id)
        else:
            self.log.debug("delete volume by name")
            # use our get for get volume by name
            internal_volume = self.volume_get(name=name)
            volume = self.cinder.volumes.get(internal_volume['id'])
        try:
            return self.cinder.volumes.delete(volume)
        except cinder_exceptions.BadRequest:
                raise manage_exeption()

    def instance_list(self):
        """
            get full list of avaible instnaces
        """
        instances = self.nova.servers.list()
        return [
            self.__instance_convert__(i) for i in instances
        ]

    def volume_attach(
        self,
        mount_point,
        vol_id=None, vol_name=None,
        ins_id=None, ins_name=None,
    ):
        """
            attach volume to instance,
            vol_id and ins_id have higher prority
                then vol_name and ins_name and mush faster
        """
        if not vol_id:
            internal_volume = self.volume_get(name=vol_name)
            vol_id = internal_volume['id']

        volume = self.cinder.volumes.get(vol_id)

        if not ins_id:
            internal_instance = self.instance_get(name=ins_name)
            ins_id = internal_instance['id']

        volume.attach(ins_id, mount_point)

        return self.volume_get(vol_id=vol_id)

    def volume_format(
        self, mount_point, key_file, username, ins_id=None,
        ins_name=None
    ):
        """
            connect by ssh to instance and format volume,
            moint_point - name of device
            key_file - file handler for private key,
            username - user name on instance
            ins_id have higher prority
                then ins_name and mush faster
        """
        internal_instance = self.instance_get(
            name=ins_name, ins_id=ins_id
        )

        if internal_instance:
            ip = internal_instance['networks']['private'][0]
        else:
            raise manage_exeption()
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        with key_file:
            ssh.connect(
                ip, username=username,
                pkey=paramiko.RSAKey.from_private_key(key_file)
            )
            chan = ssh.get_transport().open_session()
            chan.get_pty()
            chan.exec_command(
                'sudo /sbin/mkfs.ext4 /dev/vdb && echo OK || echo FAIL'
            )
            buff = chan.recv(80)
            while buff.find("\nOK") == -1 and buff.find("\nFAIL") == -1:
                buff += chan.recv(80)
            chan.close()
        ssh.close()
