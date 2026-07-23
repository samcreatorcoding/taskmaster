import json
from pathlib import Path

def load_config(file) -> tuple[dict, bool]:
    file = Path(file)
    if not file.exists():
        return {
            "defuser":None,
            "days":[],
            "tasks":[],
            "users":{}
        }, False
    with open(file, "r") as c:
        config = json.load(c)
    return config, True

def write_config(file, data:dict) -> None:
    file = Path(file)
    if not file.exists():
        file.touch()
    with open(file, "w") as c:
        json.dump(data, c)

def to_config(storage:Storage) -> dict:
    return {
        "defuser":storage.default_user.name,
        "days":[d.name for d in storage.days],
        "tasks":[t.name for t in storage.tasks],
        "users":{
            u.name:{
                "ctasks":[t.name for t in u.ctasks],
                "mtasks":u.max
            } for u in storage.users
        }
    }

def from_config(config:dict) -> Storage:
    s = Storage()
    for u, d in config["users"].items():
        user = User(u, d["ctasks"], d["mtasks"])
        s.users.append(user)
    s.default_user = DefaultUser(config["defuser"])
    for t in config["tasks"]:
        task = Task(t, s.default_user)
        task.set_users(s.users)
        s.tasks.append(task)
    for d in config["days"]:
        day = Weekday(d)
        day.set_tasks(s.tasks)
        s.days.append(day)
    return s