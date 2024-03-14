from typing import Dict, List


def find_terminal_to_common_routes(route_terminal: Dict[str, str]) -> Dict[str, List[str]]:
    terminal_to_routes = {}
    for route, terminal in route_terminal.items():
        if terminal not in terminal_to_routes:
            terminal_to_routes[terminal] = []
        terminal_to_routes[terminal].append(route)
    return terminal_to_routes


if __name__ == '__main__':
    route_terminal = {'0': '0', '1': '1', '2': '0'}
    terminal_to_routes = find_terminal_to_common_routes(route_terminal)
