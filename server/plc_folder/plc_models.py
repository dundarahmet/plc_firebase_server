from plc_folder.plc_util import create_bytearray
from snap7.util import get_bool, get_string, get_int, get_real


class Datablock:
    """Datablock object"""

    def __init__(self, **kwargs):
        """
        Datablock contructor.
        :param inside the kwargs, _name: datablock's name
        :param kwargs : other information.
        __template: list contains dicts
        __datablock_number: int
        __size: int
        __datablock: bytearray
        """

        self.__template = sorted(kwargs['data'], key=lambda x: x['Offset'])

        self.__datablock_number = int(kwargs['_name'][2:])
        self.__size = int(kwargs['size'])
        self.__datablock = create_bytearray(size=self.__size, lst=kwargs['data'])

    def create_data_for_fb(self, _bytearray):
        """
        Create data for firebase
        :param _bytearray
        :return tuple (path, dict)
        :raises
            TypeError
            OverflowError
            ValueError
        """

        if not isinstance(_bytearray, bytearray):
            raise TypeError("A parameter must be bytearray")

        if self.__size != len(_bytearray):
            raise OverflowError("Bytearray is not correct")

        holder = {}

        for index, foo in enumerate(self.__template):
            data_type = foo['Data_type']
            offset = float(foo['Offset'])
            row = None
            old = None

            if data_type == 'Bool':
                byte, bit = str(offset).split('.')
                byte, bit = int(byte), int(bit)
                old = get_bool(self.__datablock, byte, bit)
                row = get_bool(_bytearray, byte, bit)

            elif data_type == 'String':
                offset = int(offset)
                old = get_string(self.__datablock, offset, 256)
                row = get_string(_bytearray, offset, 256)

            elif data_type == 'Int':
                offset = int(offset)
                old = get_int(self.__datablock, offset)
                row = get_int(_bytearray, offset)

            elif data_type == 'Real':
                offset = int(offset)
                old = get_real(self.__datablock, offset)
                row = get_real(_bytearray, offset)
            else:
                raise ValueError("data_type error")

            if old == row:
                continue

            holder[index] = row

        self.__datablock = _bytearray
        return 'current/datablocks/DB{_num}/data'.format(_num=self.__datablock_number), holder

    @property
    def datablock_number(self):
        """
        return db number
        :return: int
        """
        return self.__datablock_number

    @property
    def size(self):
        """
        return db size
        :return: int
        """

        return self.__size

    @property
    def datablock(self):
        """
        return __datablock
        :return: list
        """

        return self.__datablock


class Version_Model:
    """Version model for datum on database"""

    def __init__(self, **kwargs):
        """
        __version_model contructor.
        :param kwargs:

        :raises
            ValueError
        """
        self.__datablocks = []
        self.__version = kwargs['_name']

        self.__plc_information = kwargs['plc_informations']

        for foo in kwargs['datablocks']['data_block_names']:
            self.__datablocks.append(Datablock(_name=foo, **kwargs['datablocks'][foo]))

        self.__datablocks.sort(key=lambda x: x.datablock_number)
        if not self.__datablocks:
            raise ValueError('Datablock does not exist')

        self.__datablocks.sort(key=lambda x: x.datablock_number)

    @property
    def datablocks(self):
        """
        return __datablocks
        :return: list
        """
        return self.__datablocks

    @property
    def plc_information(self):
        """
        return __plc_information
        :return: dict
        """
        return self.__plc_information

    @property
    def name(self):
        """
        return a version. new or current
        :return: str
        """
        return self.__version

    @name.setter
    def name(self, _name):
        """set the __version"""
        self.__version = _name
