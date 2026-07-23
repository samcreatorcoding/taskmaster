import sys
import asyncio
import threading
import os
import json
try:
    from core import (
        DefaultUser,
        User,
        Task,
        Weekday,
        Planning
    )
    from files import (
        from_config,
        to_config,
        load_config,
        write_config
    )
except ImportError:
    from src.core.core import (
        DefaultUser,
        User,
        Task,
        Weekday,
        Planning
    )
    from src.core.files import (
        from_config,
        to_config,
        load_config,
        write_config
    )

def log(m:str):
    with open("api.log", "a") as l:
        l.write(m+"\n")

class Storage:
    def __init__(self):
        self.default_user:DefaultUser|None = None
        self.users:list[User] = []
        self.tasks:list[Task] = []
        self.days:list[Weekday] = []
        self.plannings:list[Planning] = []
    
    def update(self):
        for t in self.tasks:
            t.set_users(self.users)
        for d in self.days:
            d.set_tasks(self.tasks)
    
    def reset_users(self):
        for u in self.users:
            u.reset()
    
    def add_user(self, name:str, compatible_tasks:list[Task], max_tasks:int) -> None:
        u = User(name, compatible_tasks, max_tasks)
        self.users.append(u)
        self.update()
    
    def remove_user(self, name:str) -> bool:
        for u in self.users:
            if u.name == name:
                self.users.remove(u)
                self.update()
                return True
        return False
    
    def modify_user(self, name:str, new_name:str|None=None, new_ctasks:list|None=None, new_mtasks:int|None=None) -> bool:
        for u in self.users:
            if u.name == name:
                if new_name is not None:
                    u.name = new_name
                if new_ctasks is not None:
                    u.ctasks = new_ctasks
                if new_mtasks is not None:
                    u.max = new_mtasks
                u.reset()
                return True
        return False
    
    def add_task(self, name:str) -> None:
        task = Task(name, self.default_user)
        self.tasks.append(task)
        self.update()
    
    def remove_task(self, name:str) -> bool:
        for t in self.tasks:
            if t.name == name:
                self.tasks.remove(t)
                self.update()
                return True
        return False

    def create_planning(self, name:str) -> Planning:
        planning = Planning(name)
        planning.set_days(self.days)
        self.plannings.append(planning)
        self.reset_users()
        return planning

def setup(file) -> None:
    with open(file, "w") as f:
        json.dump({
            "defuser":None,
            "days":[],
            "tasks":[],
            "users":{}
        }, f)

def init(file) -> Storage:
    config, success = load_config(file)
    if not success:
        setup(file)
    storage = from_config(config)
    return storage

def save(file, storage:Storage) -> None:
    write_config(file, to_config(storage))

OS = sys.platform

if OS == "win32":
    SOCKET_TYPE = "TCP"
    SOCKET_ADDRESS = ("127.0.0.1", 65432)
else:
    SOCKET_TYPE = "UNIX"
    SOCKET_ADDRESS = "/tmp/my_file_socket"

class Handler:
    def __init__(self) -> None:
        self.storage = Storage()

    async def start(self, ready: threading.Event | None = None) -> None:
        if SOCKET_TYPE == "UNIX":
            if os.path.exists(SOCKET_ADDRESS):
                os.remove(SOCKET_ADDRESS)
            server = await asyncio.start_unix_server(
                self.handle_client,
                path=SOCKET_ADDRESS
            )
        else:
            host, port = SOCKET_ADDRESS
            server = await asyncio.start_server(
                self.handle_client,
                host=host,
                port=port
            )
        log("[Handler] Server started")
        if ready is not None:
            ready.set()
        try:
            async with server:
                await server.serve_forever()
        finally:
            if SOCKET_TYPE == "UNIX" and os.path.exists(SOCKET_ADDRESS):
                os.remove(SOCKET_ADDRESS)

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            data = await reader.read(1024)
            command = data.decode().strip()
            log(f"[Handler] received command {command}")
            response = self.handle_command(command)
            if response:
                writer.write(response.encode())
                await writer.drain()
        except Exception as e:
            log(f"[Handler] Error occurred: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
    
    def handle_command(self, command:str) -> None|str:
        base, args = command[:3], command[3:].split("\xFF")
        if "g" in base:
            planning, pandfr = self.storage.create_planning(args[0]).plan()
            if "e" in base:
                planning.excel(args[1], planning)
            if "o" in base:
                with open(args[2], "w") as of:
                    json.dump(planning, of)
            return pandfr if pandfr != "" else json.dumps(planning)
        elif "u" in base:
            if "a" in base:
                self.storage.add_user(*args)
            elif "r" in base:
                self.storage.remove_user(args[0])
            elif "m" in base:
                self.storage.modify_user(*args)
        elif "t" in base:
            if "a" in base:
                self.storage.add_task(args[0])
                return
            elif "r" in base:
                self.storage.remove_task(args[0])
        elif "x" in base:
            save(args[0], self.storage)
        elif "s" in base:
            setup(args[0])
        elif "i" in base:
            self.storage = init(args[0])

def start_backend() -> tuple[Handler, threading.Thread]:
    backend = Handler()
    ready = threading.Event()
    error = None
    def runner():
        nonlocal error
        try:
            asyncio.run(backend.start(ready))
        except Exception as e:
            error = e
            ready.set()
    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    ready.wait()
    if error is not None:
        raise error
    return backend, thread

class Caller:
    def __init__(self):
        self._b_t = set()

    async def _send_to_socket(self, command: str, wait_for_response: bool) -> str|None:
        """Connects with backend and sends command"""
        try:
            if SOCKET_TYPE == "UNIX":
                reader, writer = await asyncio.open_unix_connection(SOCKET_ADDRESS)
            else:
                host, port = SOCKET_ADDRESS
                reader, writer = await asyncio.open_connection(host, port)
            
            writer.write(command.encode())
            await writer.drain()

            if wait_for_response:
                data = await reader.read(1024)
                response = data.decode()
                writer.close()
                await writer.wait_closed()
                return response
            else:
                writer.close()
                await writer.wait_closed()
                return
                
        except Exception as e:
            log(f"[Caller]: Error occurred: {e}")
            return

    async def send_and_forget(self, command: str) -> None:
        """Sends command and continues"""
        task = asyncio.create_task(self._send_to_socket(command, wait_for_response=False))
        self._b_t.add(task)
        task.add_done_callback(self._b_t.discard)

    async def send_and_wait(self, command: str) -> str:
        """Sends command and awaits answer"""
        return await self._send_to_socket(command, wait_for_response=True)
