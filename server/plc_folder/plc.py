from snap7 import client, snap7exceptions
from plc_folder.plc_models import Version_Model
from plc_folder import plc_exception
from copy import deepcopy


class PLC(client.Client):
    """A PLC object"""

    def __init__(self, **kwargs):
        """
        PLC object constructor
        :param kwargs: dict
        :raise plc_exception.DatabaseError
        """

        super().__init__()

        self.__new = None
        self.__current = None
        self.__old_data = None
        self.__plc_name = kwargs['plc_name']
        self.__plc_uid = kwargs['plc_uid']
        self.__db_read = client.Client()

        if 'new' in kwargs:
            self.__new = Version_Model(_name='new', plc_name=kwargs['plc_name'], **kwargs['new'])
        else:
            raise plc_exception.DatabaseError("new does not exist in the database")

        self.__parameters = (
            kwargs['plc_parameters']['Ip_Address'],
            kwargs['plc_parameters']['Rack'],
            kwargs['plc_parameters']['Slot'],
            kwargs['plc_parameters']['Port']
        )

        self.__plc_connection()
        self.__upload_new_data()

    def update_plc(self, **kwargs):
        """
        update method to update plc's current datablock
        :param kwargs:
        :return:
        :raises
            plc_exception.DatabaseError
            plc_exception.MissingConnection
        """
        if 'current' not in kwargs:
            raise plc_exception.DatabaseError("current does not exist in the database")

        try:
            self.__check_connection()
        except plc_exception.MissingConnection:
            self.__try_connection()

        self.__current = Version_Model(_name='current', **kwargs['current'])
        if self.__plc_name != kwargs['plc_name']:
            self.__plc_name = kwargs['plc_name']
        self.__check_datablock_size(_type='current')
        self.__update_current_data()

    def __update_current_data(self):
        """
        update method
        :return:
        :raises
            plc_exception.CurrentError
            plc_exception.WriteError
        """
        if not self.__current:
            raise plc_exception.CurrentError("Current data is empty.")

        try:
            self.__check_connection()
        except plc_exception.MissingConnection:
            self.__try_connection()

        for foo in self.__current.datablocks:
            try:
                self.db_write(foo.datablock_number, 0, foo.datablock)
            except snap7exceptions.Snap7Exception as Error:
                print("error is: ", Error)
                raise plc_exception.WriteError("something was wrong")

        self.__old_data = deepcopy(self.__current)
        self.__old_data.name = 'old_data'
        del self.__current
        self.__current = None

    def upload_new_data(self, **kwargs):
        """
        upload new data to plc.
        :param kwargs:
        :return:
        :raise plc_exception.DatabseError
        """
        if 'new' in kwargs:
            self.__new = Version_Model(_name='new', **kwargs['new'])
        else:
            raise plc_exception.DatabaseError("new does not exist in the database")

        self.__upload_new_data()

    def __upload_new_data(self):
        """
        Upload only new data
        :return:
        :raise plc_exception.WriteError
        """

        self.__check_connection()
        self.__check_datablock_size(_type='new')

        for foo in self.__new.datablocks:
            try:
                self.db_write(foo.datablock_number, 0, foo.datablock)
            except snap7exceptions.Snap7Exception:
                raise plc_exception.WriteError("something was wrong")

        self.__old_data = deepcopy(self.__new)
        self.__old_data.name = 'old_data'
        del self.__new
        self.__new = None

    def __plc_connection(self):
        """
        Connect the PLC
        :return
        :raise plc_exception.PLCConnectionError
        """

        try:
            self.connect(*self.__parameters)
            self.__db_read.connect(*self.__parameters)
            print(*self.__parameters)
        except snap7exceptions.Snap7Exception:
            raise plc_exception.PLCConnectionError("Parameters are not correct.")

    def __check_connection(self):
        """
        Check if the plc is connected
        :return
        :raise plc_exception.InitializeError
        """
        try:
            if not self.get_connected() or not self.__db_read.get_connected():
                self.__try_connection()
        except AttributeError:
            raise plc_exception.InitializeError("PLC object is not correct")

    def __try_connection(self):
        """
        try to connect plc
        :return
        :raise plc_exception.PLCConnectionError
        """

        self.disconnect()
        self.__db_read.disconnect()
        self.__plc_connection()

        if not self.get_connected() or not self.__db_read.get_connected():
            raise plc_exception.PLCConnectionError("PLC isn't been connecting")

    def __check_datablock_size(self, _type):
        """
        Check the datablock size before upload the data to plc
        :param _type boolean
        :return
        :raises
            plc_exception.NewError
            plc_exception.DatablockSizeError
            plc_exception.CurrentError
            plc_exception.OldDataError
            ValueError

        """
        if isinstance(_type, str):
            self.__check_connection()
            if _type == 'new':
                if not self.__new:
                    raise plc_exception.NewError("New is empty")

                for foo in self.__new.datablocks:
                    try:
                        self.__db_read.db_read(foo.datablock_number, 0, foo.size)
                    except snap7exceptions.Snap7Exception:
                        raise plc_exception.DatablockSizeError("Datablock size is smaller than a plc's size.")

                    try:
                        self.__db_read.db_read(foo.datablock_number, 0, foo.size + 2)
                        raise plc_exception.DatablockSizeError("Datablock size is bigger than a plc's size. ")
                    except snap7exceptions.Snap7Exception:
                        continue

            elif _type == 'current':
                if not self.__current:
                    raise plc_exception.CurrentError("Current is empty.")
                if not self.__old_data:
                    raise plc_exception.OldDataError("Old_data is empty.")
                if len(self.__current.datablocks) != len(self.__old_data.datablocks):
                    raise plc_exception.CurrentError("Current data has more datablock than old_data")

                for foo, bar in zip(self.__current.datablocks, self.__old_data.datablocks):
                    if len(foo.datablock) != len(foo.datablock):
                        raise plc_exception.CurrentError("Current has more data than old_data in datablock")
                    if foo.datablock_number != bar.datablock_number:
                        raise plc_exception.CurrentError("Current data has different datablock number")
                    if foo.size != bar.size:
                        raise plc_exception.CurrentError("Current data has different size")

            else:
                raise ValueError("Wrong _type key")
        else:
            raise ValueError("_type must be str.")

    @property
    def data_from_plc(self):
        """
        Data to upload firebase
        :return: list contains tuples or None
        :raise plc_exception.OldDataError
        """

        if not self.__old_data or not isinstance(self.__old_data, Version_Model):
            raise plc_exception.OldDataError("Old data is not correct")

        self.__check_connection()

        holder_database = [self.__plc_uid]

        for foo in list(self.__old_data.datablocks):

            db_read = self.__db_read.db_read(foo.datablock_number, 0, foo.size)

            if foo.datablock != db_read:
                holder_database.append(foo.create_data_for_fb(_bytearray=db_read))

        if not holder_database[1:]:
            return

        return holder_database

    @property
    def plc_parameters(self):
        """
        Return ip_address, rack and slot
        :return dict
        """

        return self.__parameters

    @property
    def plc_connection_info(self):
        """
        Return the state of plc
        :return Boolean
        """

        return self.get_connected()

    @property
    def plc_name(self):
        """
        Return plc_name
        :return: str
        """

        return self.__plc_name

    @property
    def plc_uid(self):
        """
        return plc_uid
        :return: str
        """

        return self.__plc_uid
