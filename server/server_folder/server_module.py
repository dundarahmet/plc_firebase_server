from requests import get
from requests.exceptions import ConnectionError
import logging
from time import sleep
from threading import Thread
from server_folder import server_exception
from plc_folder import plc
from fb_folder.fb_module import Firebase


class __Server:
    __plc_holder = {}

    def __init__(self):
        """
        default contructor of Server object
        :return
        """
        pass

    def __initializing(self, fb_key_path, options=None):
        """
        initialize the __server object
        :param fb_key_path:
        :return:
        """
        self.__firebase = Firebase(fb_key_path, options=options)
        self.__firebase.start_listen(self.__listener)
        self.__continue_thread = [True]
        self.__thread = None

        self.__check_and_start_thread()

    def __check_and_start_thread(self):
        """
        start thread
        :return:
        """

        if isinstance(self.__thread, Thread) and self.__thread.is_alive():
            logging.warning("thread is active")
            return
        else:
            try:
                del self.__thread
            finally:
                self.__thread = None

        self.__thread = Thread(target=self.__threat_function)
        self.__thread.start()

    def __threat_function(self):
        """
        check plc connection in thread
        :return:
        """
        counter = 0
        while True:
            if not self.__continue_thread[0]:
                break
            if counter == 5:
                counter = 0
                self.__check_plcs_connection(True)
                self.__upload_plc_data_to_fb()
                sleep(1)
            counter += 1

    def __check_plcs_connection(self, in_thread):
        """
        to check if plcs are still connected
        :return:
        """

        if not self.__plc_holder:
            if not in_thread and isinstance(self.__thread, Thread) and self.__thread.is_alive():
                self.__continue_thread[0] = False
                self.__thread.join()
                self.__thread = None

            return

        for key, value in list(self.__plc_holder.items()):
            if not value.plc_connection_info:
                self.__delete_plc(key)

    def __plc_object(self, **kwargs):
        """
        to create a new plc object by using firebase database data
        :param: kwargs: dict
        :return:
        """
        if not kwargs:
            return
        plc_uid = kwargs['plc_uid']
        try:
            self.__plc_holder[plc_uid] = plc.PLC(**kwargs)
            self.__firebase.change_new(plc_uid)
        except Exception:
            self.__firebase.delete_plc(plc_uid)
            logging.warning('"{}" was not correct and now will delete'.format(plc_uid))

    def __create_plc(self, **database):
        """
        create plc by using firebase data
        :return:
        """

        self.__check_and_start_thread()

        if database is None or database == {}:
            logging.warning("Database is empty")
            return

        for key, value in list(database.items()):
            if key not in self.__plc_holder:
                self.__plc_object(plc_uid=key, **value)

    def __update_plc(self, plc_uid):
        """
        to update existed plc object by using firebase database data
        :param plc_uid: string
        :return:
        :raise TypeError
        """
        if not isinstance(plc_uid, str):
            raise TypeError("plc_uid must be string")

        data = self.__firebase.child(plc_uid).get()
        try:
            self.__plc_holder[plc_uid].update_plc(**data)
        except KeyError:
            logging.error("something was wrong")
            self.__plc_object(plc_uid=plc_uid, **data)

    def __delete_plc(self, key):
        """
        delete a plc object in dict and plc data on database
        :return:
        """
        try:
            del self.__plc_holder[key]
        except KeyError:
            return

        self.__firebase.delete_plc(key)
        logging.warning('"{}" is deleted.'.format(key))

    def __upload_plc_data_to_fb(self):
        """
        to update changes of a plc to database
        :return:
        """
        if not self.__plc_holder:
            return

        for value in list(self.__plc_holder.values()):
            holder = value.data_from_plc
            if holder:
                self.__firebase.update_plc_data(holder)

    def __show_plcs(self):
        """
        show all connected plcs
        :return:
        """
        if not self.__plc_holder:
            print("There are not any connected plcs")
            return

        for enum, value in enumerate(self.__plc_holder.values()):
            print("{num_}: {plc_uid}: {active}".format(
                num_=enum, plc_uid=value.plc_uid, active=value.plc_connection_info))

    def __stop_server(self):
        """
        stop server
        :return:
        """
        logging.warning("server is closing")
        self.__continue_thread[0] = False
        self.__thread.join()
        self.__thread = None
        self.__firebase.close_listen()
        self.__firebase = None

        for value in list(self.__plc_holder.values()):
            value.disconnect()

        self.__plc_holder = {}

    def __server_interface(self):
        """
        server interface
        :return: boolean
        """
        choices = """
        *************************
        **1-show choices       **
        **2-show connected plcs**
        **3-show database      **
        **4-stop server        **
        *************************
        """

        choice = input("=> ")

        if choice == "2":
            self.__show_plcs()
        elif choice == "3":
            print(self.__firebase.get())
        elif choice == "4":
            print("Are you sure? If it is yes, enter y")
            last_chance = input("Are you sure? =>")
            if last_chance.lower() == 'y':
                self.__stop_server()
                return True
            else:
                print(choices)
        else:
            print(choices)

        return False

    def __listener(self, event):
        """
        a function which is sent start_listen method of firebase object
        :param event
        :return:
        :raises:
            server_exception.UnexpectedVariable
            server_exception.DatabaseWrongDataForm
        """
        if event.data is None:
            # if event.data is None, the data are deleted on database

            if event.path == '/':
                logging.warning("Database is empty")
                return

            plc_uid = event.path.split('/')[1]
            self.__delete_plc(plc_uid)

        else:
            # if event.data is not Nona, the data are changed or updated
            if event.event_type.lower() == 'put':
                # if event_type is put, a new plc is added or the data on database are changed via firebase
                path = event.path.split("/")

                if event.path == '/':
                    # if event.path is /, listener is beginning.
                    self.__create_plc(**event.data)
                elif len(path) == 2:
                    # if a size of path is 2, a new plc is added.
                    if not isinstance(event.data, dict):
                        raise server_exception.DatabaseWrongDataForm("data")
                    plc_uid = path[1]
                    self.__plc_object(plc_uid=plc_uid, **event.data)

                elif len(path) > 2:
                    # if a size of path is greater than 2, the data on database are updated via firebase
                    plc_uid = path[1]
                    self.__update_plc(plc_uid=plc_uid)

                else:
                    raise server_exception.UnexpectedVariable("path")

            elif event.event_type.lower() == 'patch':
                # if event_type is patch, a current data is updated
                if event.path == '/':
                    # if event.path is '/', the data is updated via multi-location method
                    plc_uid = list(event.data.keys())[0].split('/')[0]
                else:
                    # if event.path is like '/some_path', the data is updated via single-location method
                    plc_uid = event.path.split('/')[1]

                self.__update_plc(plc_uid)

            else:
                raise server_exception.UnexpectedVariable("event_type")

    def start_server(self, fb_key_path, options=None):
        """
        main server loop
        :param:
            fb_key_path: string
            options: dict
        :return:
        :raises:
            TypeError
        """
        if not isinstance(fb_key_path, str):
            raise TypeError("fb_key_path must be string")
        if not isinstance(options, dict) and options is not None:
            raise TypeError("options must be dict or none")

        self.__check_internet_connection()
        self.__initializing(fb_key_path, options=options)

        print("""
        *************************
        **Welcome to the server**
        **1-show choices       **
        **2-show connected plcs**
        **3-show database      **
        **4-stop server        **
        *************************
        """)

        while True:
            condition = self.__server_interface()
            if condition:
                break

    @staticmethod
    def __check_internet_connection():
        """
        to check the internet connection
        :return:
        :raise server_exception.LostInternetConnection
        """
        try:
            get("https://www.google.com")
        except ConnectionError:
            raise server_exception.LostInternetConnection("")


server = __Server()
