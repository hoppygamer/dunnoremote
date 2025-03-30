import tkinter as tk
from tkinter import ttk
import random
import string
import socket
import threading
import pyautogui
import json
import pyperclip
import cv2
import numpy as np

def generate_random_string(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))

random_user = generate_random_string()
random_password = generate_random_string()

server_socket = None
running = True
connections = []

def handle_client(client_socket):
    global running
    client_socket.send(b"enter username: ")
    username = client_socket.recv(1024).decode().strip()
    client_socket.send(b"enter password: ")
    password = client_socket.recv(1024).decode().strip()

    if username == random_user and password == random_password:
        client_socket.send(b"access granted\n")
        while running:
            try:
                screen = pyautogui.screenshot()
                screen_np = np.array(screen)
                _, encoded_image = cv2.imencode('.jpg', cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR))
                client_socket.send(encoded_image.tobytes() + b"ENDIMG")

                data = client_socket.recv(1024).decode()
                if not data:
                    break

                command = json.loads(data)
                command_type = command.get('type')

                if command_type == 'mouse_move':
                    pyautogui.moveTo(command['x'], command['y'])
                elif command_type == 'mouse_click':
                    pyautogui.click()
                elif command_type == 'key_press':
                    pyautogui.write(command['key'])
                elif command_type == 'key_combo':
                    pyautogui.hotkey(*command['keys'])
                elif command_type == 'clipboard_get':
                    clipboard_content = pyperclip.paste()
                    client_socket.send(json.dumps({"type": "clipboard_content", "content": clipboard_content}).encode())
                elif command_type == 'clipboard_set':
                    clipboard_content = command.get('content', '')
                    pyperclip.copy(clipboard_content)
            except Exception:
                break
    else:
        client_socket.send(b"access denied\n")
    client_socket.close()

def start_server():
    global server_socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 65432))
    server_socket.listen(1)

    while running:
        try:
            client_socket, _ = server_socket.accept()
            connections.append(client_socket)
            threading.Thread(target=handle_client, args=(client_socket,), daemon=True).start()
        except Exception:
            break

def main_app():
    def open_connection():
        threading.Thread(target=start_server, daemon=True).start()
        connect_label.config(
            text=f"ur user: {random_user}\nur password: {random_password}",
            foreground="green"
        )

    def stop_connection():
        global running
        running = False
        for conn in connections:
            conn.close()
        if server_socket:
            server_socket.close()
        main_window.destroy()

    main_window = tk.Tk()
    main_window.title("dunnoremote")
    main_window.geometry("400x300")
    main_window.resizable(False, False)

    connect_label = ttk.Label(
        main_window, text=f"ur user: {random_user}\nur password: {random_password}"
    )
    connect_label.pack(pady=20)

    connect_button = ttk.Button(main_window, text="start server", command=open_connection)
    connect_button.pack(pady=10)

    stop_button = ttk.Button(main_window, text="stop server", command=stop_connection)
    stop_button.pack(pady=10)

    main_window.mainloop()

if __name__ == "__main__":
    main_app()
