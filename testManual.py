import unittest
from manage_utils import manage_utils, manage_exeption
import time
import random
import logging

unitLogger = logging.getLogger('unittest')
unitLogger.setLevel(logging.DEBUG)
handler = logging.FileHandler("./manual_test.log")
unitLogger.addHandler(handler)


class TestManual(unittest.TestCase):

    manage_obj = None

    max_wait = 20

    def setUp(self):

        unitLogger.debug("-- setUp at %s --" % time.time())
        self.manage_obj = manage_utils(
            "demo", "secrete", "demo",
            "http://10.0.2.15:5000/v2.0", unitLogger
        )

    def testVolumeList(self):
        """
            test for general usability of connection to cinder
        """
        unitLogger.debug("testVolumeList")
        self.assertIsNotNone(self.manage_obj.volume_list())

    def testInstanceList(self):
        """
            test for general usability of connection to nova
        """
        unitLogger.debug("testInstanceList")
        self.assertIsNotNone(self.manage_obj.instance_list())

    def __search_volume__(self, vol_id):
        """
            search volume in full list, only for check list
        """
        for volume in self.manage_obj.volume_list():
            if volume['id'] == vol_id:
                return volume
        return None

    def __create_volume__(self):
        """
            create volume for tests
        """
        size = random.randint(1, 5)

        desc = str(random.randint(1, 500))

        new_name = "disk%s-%s" % (size, time.time())

        # create something
        created = self.manage_obj.volume_create(size, new_name, desc)

        self.assertIsNotNone(created)
        self.assertEqual(created['name'], new_name)
        self.assertEqual(created['description'], desc)
        self.assertEqual(created['size'], size)

        # search in list
        volume = self.__search_volume__(created['id'])
        self.assertIsNotNone(volume)
        self.assertEqual(volume['name'], new_name)
        self.assertEqual(volume['description'], desc)
        self.assertEqual(volume['size'], size)

        # directly get
        volume = self.manage_obj.volume_get(created['id'])
        self.assertIsNotNone(volume)
        self.assertEqual(volume['name'], new_name)
        self.assertEqual(volume['description'], desc)
        self.assertEqual(volume['size'], size)

        # get by name
        volume = self.manage_obj.volume_get(name=new_name)
        self.assertIsNotNone(volume)
        self.assertEqual(volume['name'], new_name)
        self.assertEqual(volume['description'], desc)
        self.assertEqual(volume['size'], size)

        count_try = 0
        while volume and volume['status'] == "creating" and \
                count_try < self.max_wait:
            time.sleep(5)
            volume = self.manage_obj.volume_get(created['id'])
            unitLogger.debug("Creating...")
        self.assertTrue(count_try < self.max_wait)

        return volume

    def __drop_volume__(self, created):
        """
            drop some volume
        """
        self.manage_obj.volume_delete(created['id'])
        volume = self.__search_volume__(created['id'])
        # must be deleting
        # or if we do everything very fast must be None
        count_try = 0
        while volume and volume['status'] == "deleting" and \
                count_try < self.max_wait:
            time.sleep(5)
            volume = self.__search_volume__(created['id'])
            unitLogger.debug("Deleting...")
        self.assertTrue(count_try < self.max_wait)

        # reget info
        volume = self.__search_volume__(created['id'])
        # so must be deleted
        self.assertIsNone(volume)

    def testGetException(self):
        """
            test throw exeption for not exist volume
        """
        unitLogger.debug("testGetException")
        some_id = "UnExistDisk%s" % (time.time())
        volume = self.__search_volume__(some_id)
        self.assertIsNone(volume)
        with self.assertRaises(manage_exeption):
            self.manage_obj.volume_get(some_id)
        with self.assertRaises(manage_exeption):
            self.manage_obj.volume_get(name=some_id)

    def testCreate(self):
        """
            Only create than drop volume
        """
        unitLogger.debug("testCreate")
        created = self.__create_volume__()
        self.__drop_volume__(created)

    def testDropByName(self):
        """
            Only create than drop volume by name
        """
        unitLogger.debug("testDropByName")
        created = self.__create_volume__()
        self.manage_obj.volume_delete(name=created['name'])
        volume = self.__search_volume__(created['id'])

        # must be deleting
        # or if we do everything very fast must be None
        count_try = 0
        while volume and volume['status'] == "deleting" and \
                count_try < self.max_wait:
            time.sleep(5)
            volume = self.__search_volume__(created['id'])
            count_try += 1
            unitLogger.debug("Deleting...")
        self.assertTrue(count_try < self.max_wait)

        # reget info
        volume = self.__search_volume__(created['id'])
        # so must be deleted
        self.assertIsNone(volume)

    def testFullSequnce(self):
        """
            Check full sequense of availble actions
        """
        unitLogger.debug("testFullSequnce")
        self.assertIsNotNone(self.manage_obj.volume_list())
        created = self.__create_volume__()
        instances = self.manage_obj.instance_list()
        self.assertTrue(instances)
        self.manage_obj.volume_attach(
            "/dev/vdn",
            vol_id=created['id'],
            ins_id=instances[0]['id']
        )

        # try to format volume
        # self.manage_obj.volume_format(
        #    "/dev/vdn", open('./cloud.key', 'r'), 'fedora',
        #    ins_id=instances[0]['id']
        # )

        # drop attached must raise error
        with self.assertRaises(manage_exeption):
            self.__drop_volume__(created)

        # detach
        self.manage_obj.volume_detach(created['id'])

        # drop
        self.__drop_volume__(created)

        self.assertIsNotNone(self.manage_obj.volume_list())

if __name__ == '__main__':
    unittest.main()