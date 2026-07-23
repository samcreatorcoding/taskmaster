from random import sample
#make pandas optional
try:
    from pandas import DataFrame
    pandas = True
except ImportError:
    pandas = False

class User:
    def __init__(self, name:str, compatible_tasks:list, max_tasks:int) -> None:
        self.name = name
        self.ctasks = compatible_tasks
        self.space = max_tasks
        self.max = max_tasks
    
    def has_space(self, autoresolve:bool=True) -> bool:
        if self.space > 0:
            if autoresolve:
                self.space -= 1
            return True
        return False
    
    def reset(self) -> None:
        self.space = self.max
    
    def is_compatible(self, task) -> bool:
        if isinstance(task, str):
            return task in self.ctasks
        elif hasattr(task, "name"):
            return task.name in self.ctasks
        return False

class DefaultUser:
    def __init__(self, name:str) -> None:
        self.name = name

class Task:
    def __init__(self, name:str, default_user:DefaultUser) -> None:
        self.name = name
        self.default = default_user
        self.users = []
    
    def set_users(self, users:list[User], filter_compatible:bool=True) -> list[User]:
        if filter_compatible:
            users = [u for u in users if u.is_compatible(self)]
        self.users = users
        return users
    
    def shuffle_users(self) -> None:
        self.users = sample(self.users, k=len(self.users))
    
    def pick_user(self) -> User|DefaultUser:
        self.shuffle_users()
        for u in self.users:
            if u.has_space():
                return u
        return self.default

class Weekday:
    def __init__(self, name:str) -> None:
        self.name = name
        self.tasks = []
    
    def set_tasks(self, tasks:list[Task]) -> None:
        self.tasks = tasks
    
    def plan_day(self) -> dict[str, str]:
        planning = {}
        for t in self.tasks:
            u = t.pick_user()
            planning[t.name] = u.name
        return planning

class Planning:
    def __init__(self, name:str) -> None:
        self.name = name
    
    def set_days(self, days:list[Weekday]) -> None:
        self.days = days
    
    def plan(self) -> tuple[dict[str, dict], str]:
        planning = {}
        for d in self.days:
            planning[d.name] = d.plan_day()
            df = ""
        if pandas:
            df = DataFrame(planning)
        return planning, str(df)
    
    def excel(self, file, planned:dict) -> None:
        if pandas:
            df = DataFrame(planned)
            df.to_excel(file, self.name)
        else:
            raise ImportError("Method Planning.excel cannot be used without installing pandas (pip install pandas)")