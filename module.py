from typing import Optional

from client.api import API
from core.message_queue.worker import start_message_sender_worker
from core.plugins.loader import (
    discover_py_files,
    find_routers_in_module,
    import_module_from_path,
)
from core.polling.runner import PollingRunner
from core.routers.loader import load_routers
from core.routers.router import Router


class Module:
    def __init__(
        self,
        api: Optional[API] = None,
        access_token: Optional[str] = None,
        routers: Optional[list[Router]] = None,
        plugins: Optional[list[str]] = None,
    ):
        self.api = api or API(access_token=access_token)
        self.routers = routers or []

        if plugins:
            for directory in plugins:
                self.load_plugins_from_directory(directory)

    def load_plugins_from_directory(self, directory: str):
        """
        Load all plugins from the given directory.

        :param directory: The path to the directory with plugins
        """
        for file_path in discover_py_files(directory):
            module = import_module_from_path(file_path)
            if module:
                routers = find_routers_in_module(module)
                self.add_routers(*routers)

    def add_router(self, router: Router):
        """
        Add a single router to the module and register it.

        :param router: A Router instance to be added and registered.
        """
        self.routers.append(router)
        load_routers([router])

    def add_routers(self, *routers: Router):
        """
        Add multiple routers to the module and register them.

        :param routers: Zero or more Router instances to be added and registered.
        """
        self.routers.extend(routers)
        load_routers(routers)

    async def run_polling(self):
        """
        Starts the longpolling worker.

        This method starts an instance of :class:`PollingRunner` with the given
        API instance and routers. The worker will listen to the longpolling
        server and pass the events to the routers.

        :return: None
        """
        await start_message_sender_worker(self.api)

        runner = PollingRunner(self.api, self.routers)
        await runner.start()

    def method(self, name: str, params: dict):
        """
        Calls a VK API method with the given name and parameters.

        :param name: The name of the VK API method
        :param params: The parameters for the method
        :return: The response of the method
        """
        return self.api.request(name, params)
