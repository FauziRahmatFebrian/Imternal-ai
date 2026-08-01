def choose_path(sensitive: bool) -> str:
    if sensitive:
        return "local_direct"
    return "router"
