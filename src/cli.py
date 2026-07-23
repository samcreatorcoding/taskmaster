from sys import argv as args
from shlex import split
import asyncio
import json
try:
    from core.api import (
        start_backend,
        Caller
    )
except ImportError:
    from src.core.api import (
        start_backend,
        Caller
    )

def nlen(a:list, i:int) -> bool:
    return len(a) < i

def helper(context: str = "") -> None:
    print("\n--- Syntax Help ---")
    if not context:
        print("Beschikbare commando's:")
        print("  user [add|rem|mod] ...")
        print("  task [add|rem] ...")
        print("  generate")
        print("  init <file:str>")
        print("  setup <file:str>")
        print("  exit <file:str>")
    elif context == "u":
        print("Fout in user commando. Kies uit:")
        print("  user add <name:str> <tasks:\"[task, task...]\"> <maxtasks:int>")
        print("  user rem <name:str>")
        print("  user mod <name:str> [name <name:str>|tasks <tasks:\"[task, task...]\">|maxtasks <maxtasks:int>]")
    elif context == "ua_":
        print("Foutieve argumenten voor 'user add'.")
        print("Syntax: user add <name:str> <tasks:\"[task, task...]\"> <maxtasks:int>")
        print("Voorbeeld: user add 'John' '[task1, task2]' 5")
    elif context == "ur_":
        print("Foutieve argumenten voor 'user rem'.")
        print("Syntax: user rem <name:str>")
    elif context == "um_":
        print("Foutieve argumenten voor 'user mod'.")
        print("Syntax: user mod <name:str> <field: name|tasks|maxtasks> <value>")
        print("Voorbeeld: user mod 'John' 'maxtasks' 8")
    elif context == "t":
        print("Fout in task commando. Kies uit:")
        print("  task add <name:str>")
        print("  task rem <name:str>")
    elif context == "ta_":
        print("Foutieve argumenten voor 'task add'.")
        print("Syntax: task add <name:str>")
    elif context == "tr_":
        print("Foutieve argumenten voor 'task rem'.")
        print("Syntax: task rem <name:str>")
    elif context == "g":
        print("Foutieve argumenten voor 'generate'.")
        print("Syntax: generate [-e <excel_file:str>] [-o <json_file:str>]")
        print("Voorbeelden:")
        print("  generate")
        print("  generate -e rapport.xlsx")
        print("  generate -o data.json")
        print("  generate -e rapport.xlsx -o data.json")
    print("-------------------\n")

def iparse(args:list, caller:Caller) -> bool:
    if not args:
        helper()
        return False
    match args[0]:
        case "user":
            if len(args) < 2:
                helper("u")
                return False
            match args[1]:
                case "add":
                    if len(args) != 5:
                        helper("ua_")
                        return False
                    cmd = f"ua_\xFF{args[2]}\xFF{args[3]}\xFF{args[4]}"
                    caller.send_and_forget(cmd)
                    return False
                case "rem":
                    if len(args) != 3:
                        helper("ur_")
                        return False
                    cmd = f"ur_\xFF{args[2]}"
                    caller.send_and_forget(cmd)
                    return False
                case "mod":
                    if len(args) != 5:
                        helper("um_")
                        return False
                    target_user = args[2]
                    field = args[3]
                    new_val = args[4]
                    cmd = f"um_\xFF{target_user}\xFF{field}\xFF{new_val}"
                    caller.send_and_forget(cmd)
                    return False
                case _:
                    helper("u")
                    return False
        case "task":
            if len(args) < 2:
                helper("t")
                return False
            match args[1]:
                case "add":
                    if len(args) != 3:
                        helper("ta_")
                        return False
                    cmd = f"ta_\xFF{args[2]}"
                    caller.send_and_forget(cmd)
                    return False
                case "rem":
                    if len(args) != 3:
                        helper("tr_")
                        return False
                    cmd = f"tr_\xFF{args[2]}"
                    caller.send_and_forget(cmd)
                    return False
                case _:
                    helper("t")
                    return False
        case "generate":
            excel_file = ""
            json_file = ""
            i = 1
            while i < len(args):
                if args[i] == "-e":
                    if i + 1 >= len(args):
                        helper("g")
                        return False
                    excel_file = args[i+1]
                    i += 2
                elif args[i] == "-o":
                    if i + 1 >= len(args):
                        helper("g")
                        return False
                    json_file = args[i+1]
                    i += 2
                else:
                    helper("g")
                    return False
            base = "g"
            if excel_file:
                base += "e"
            if json_file:
                base += "o"
            base = base.ljust(3, "_")
            planning_name = "default_plan"
            cmd = f"{base}\xFF{planning_name}\xFF{excel_file}\xFF{json_file}"
            print("Generating...")
            response = caller.send_and_wait(cmd)
            print(response)
            return False
        case "init":
            if len(args) != 2:
                helper()
                return False
            cmd = f"i__\xFF{args[1]}"
            caller.send_and_forget(cmd)
            return False
        case "exit":
            if len(args) != 2:
                helper()
                return False
            cmd = f"x__\xFF{args[1]}"
            caller.send_and_forget(cmd)
            return True
        case "setup":
            if len(args) != 2:
                helper()
                return False
            cmd = f"s__\xFF{args[1]}"
            caller.send_and_forget(cmd)
            return False
        case _:
            helper()
            return False

def interactive_cli():
    backend, thread = start_backend()
    caller = Caller()
    file = None
    while True:
        args = split(input("> "))
        if not thread.is_alive():
            print("Backend crashed")
            break
        _exit = iparse(args, caller)
        if _exit:
            break

def main():
    if nlen(args, 2):
        parse(args[1:], Caller())
    else:
        pass

if __name__ == "__main__":
    main()
