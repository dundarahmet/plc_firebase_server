import firebase_admin as fb
from firebase_admin import db
from json import load
from requests import get
from fb_folder import fb_exception
import logging


class Firebase(db.Reference):
    """Firebase object"""

    def __init__(self, key_path, options=None):
        """a main contructor of firebase objects"""

        self.__default_app = None
        self.__listen_object = None

        self.__connect_fb(key_path, options=options)

        client = self.__my_reference(self.__default_app)

        super().__init__(client=client, path='/')

    @staticmethod
    def __my_reference(app):
        service = db._utils.get_app_service(app, db._DB_ATTRIBUTE, db._DatabaseService)
        client = service.get_client(None)
        return client

    @staticmethod
    def __key_checker(key_path):
        """
        check whether the key is correct or not
        :param key_path:
        :return tuple
        :raises
            fb_exception.SecurityKeyError
            TypeError
            ValueError
            KeyError
        """

        if not isinstance(key_path, str):
            raise TypeError("key_path parameter must be argument.")

        if not key_path.endswith('.json'):
            raise ValueError("key_path must be json file.")

        with open(key_path, 'r') as key:
            key_dict = load(key)

        for foo in ['type', 'project_id', 'private_key_id', 'private_key', 'client_email', 'client_id',
                    'auth_uri', 'token_uri', 'auth_provider_x509_cert_url', 'client_x509_cert_url']:
            if foo not in key_dict:
                raise KeyError('firebase security key is not correct.')

        link_for_checking = key_dict['client_x509_cert_url']

        if not get(link_for_checking).ok:
            raise fb_exception.SecurityKeyError("Firebase project does not exist.")

        index = link_for_checking.find("%40") + 3
        index2 = link_for_checking.rfind(".iam")

        db_link = "https://{}.firebaseio.com/".format(link_for_checking[index: index2])
        cred = fb.credentials.Certificate(key_path)

        return db_link, cred

    def __connect_fb(self, key_path, options=None):
        """
        Connect to the firebase
        :param key_path:
        :return:
        :raises
            TypeError
            KeyError
        """

        db_link, cred = self.__key_checker(key_path)

        if not options:
            self.__default_app = fb.initialize_app(cred, {'databaseURL': db_link})
        else:
            if not isinstance(options, dict):
                raise TypeError("options must be dict")
            if "databaseURL" not in options:
                raise KeyError("databaseURL not in")

            self.__default_app = fb.initialize_app(cred, options=options)

    def start_listen(self, _function):
        """
        start to listen to the database
        :param _function: function object
        :return:
        :raises
            fb_exception.ListenError
            TypeError
        """

        if isinstance(self.__listen_object, db.ListenerRegistration):
            raise fb_exception.ListenError("Listen is active")
        if not callable(_function):
            raise TypeError("_function must be function")

        def __listen_function(event):
            """
            If server changes data on database, listen function does not process the changes.
            :param event:
            :return:
            """
            if event.data is None:
                # if event.data is None, the data on database was deleted. So the server must delete the plc
                changer_id = 'other'

            elif event.event_type == 'put':
                if event.path == '/':
                    changer_id = 'other'
                else:
                    plc_uid = event.path.split('/')[1]

                    if not isinstance(event.data, dict):
                        changer_id = self.child(plc_uid).child("changer_id").get()
                    else:
                        try:
                            changer_id = event.data['changer_id']
                        except KeyError:
                            logging.error("Wrong data and the data is deleted")
                            self.delete_plc(plc_uid)
                            changer_id = None
            else:
                if event.path == '/':
                    # if event.path is '/', the data was changed via multi-location method
                    plc_uid = list(event.data.keys())[0].split('/')[0]
                else:
                    # if event.path is not '/', the data was changed via single-location method
                    plc_uid = event.path.split('/')[1]

                changer_id = self.child(plc_uid).child("changer_id").get()

            if changer_id == "server":
                my_server = True
            elif changer_id is None:
                my_server = None
            else:
                my_server = False

            if my_server is None:

                print("event_type: ", event.event_type)
                print("path: ", event.path)
                print("data: ", event.data)
                raise TypeError("Something is wrong")

            if not my_server:
                _function(event)

        self.__listen_object = self.listen(__listen_function)

    def close_listen(self):
        """
        Close to listen to the database
        :return:
        :raise fb_exception.ListenError
        """

        if isinstance(self.__listen_object, db.ListenerRegistration) and \
                not self.__listen_object.is_alive or self.__listen_object is None:
            logging.warning("listen is closed")
            return

        self.__listen_object.close()
        self.__listen_object = None

    def update_plc_data(self, lst):
        """
        update plc data
        :param lst: a list contains tuple which a format is (path, value) and lst[0]=plc_uid
        :return:
        :raises
            TypeError
            fb_exception.ChildError
        """
        if lst is None:
            return

        if not isinstance(lst, list):
            raise TypeError("lst must be list")
        "lst = [plc_uid, blabla"
        "gelen data ('current/datablocks/DB{_num}/data', data)"
        _data = {}
        plc_uid = lst[0]

        for foo in lst[1:]:
            path = "{}/{}/{}/Value"
            for key, value in foo[-1].items():
                _data[path.format(plc_uid, foo[0], key)] = value

        _data[plc_uid + '/permission/to_write'] = True
        _data[plc_uid + '/changer_id'] = 'server'
        self.update(_data)

    def change_new(self, plc_uid):
        """
        change new to current
        :param plc_uid
        :return:
        :raises
            TypeError
        """

        if not isinstance(plc_uid, str):
            raise TypeError("plc_uid must be string")

        child_node = self.child(plc_uid + "/new")
        data_ = child_node.get()
        self.update({
            plc_uid + "/new": None,
            plc_uid + "/current": data_,
            plc_uid + "/permission/to_write": True,
            plc_uid + '/changer_id': 'server'
        })

    def delete_plc(self, plc_uid):
        """
        Delete plc on database
        :param plc_uid:
        :return:
        :raise: TypeError
        """

        if not isinstance(plc_uid, str):
            raise TypeError("plc_uid must be str")

        self.child(plc_uid).delete()

    @property
    def does_listen(self):
        """
        return listen situation
        Return
        :return: Boolean
        """

        return self.__listen_object.is_alive
