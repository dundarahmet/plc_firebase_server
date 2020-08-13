from plc_folder import plc_exception
from snap7.util import set_bool, set_int, set_real, set_string


def create_bytearray(size, lst):
    """
        Create bytearray for plc
        :param size: int
        :param lst: list
        :return holder: bytearray
        :raises
            TypeError
            plc_exception.DatabaseError
        """
    if not isinstance(lst, list):
        raise TypeError("create_bytearray takes list.")

    lst = sorted(lst, key=lambda x: x['Offset'])
    holder = bytearray([0 for _ in range(size)])

    for foo in lst:
        _offset = foo["Offset"]
        _value = foo["Value"]
        if foo['Data_type'] == 'Bool':
            byte, bit = str(float(_offset)).split('.')
            byte, bit = int(byte), int(bit)

            set_bool(holder, byte, bit, _value)

        elif foo['Data_type'] == 'String':
            set_string(holder, int(_offset), _value, 256)

        elif foo['Data_type'] == 'Int':
            set_int(holder, int(_offset), _value)

        elif foo['Data_type'] == 'Real':
            set_real(holder, int(_offset), _value)
        else:
            raise plc_exception.DatabaseError("Data is not correct.")

    return holder
