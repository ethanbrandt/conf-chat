import socket
import time
import threading
import argparse

from user_data import USER_DATA # this is the "secure database"

peer_sockets = []
peer_addrs = set()
peers = {}
peer_lock = threading.Lock()

def handle_peer(conn, addr, username):
	print(f"Connected to {addr}")
	conn.sendall(f"USERNAME {username}".encode('utf-8'))
	try:
		first = conn.recv(1024).decode('utf-8')
		if not first.startswith("USERNAME "):
			print(f"Invalid initial message from {addr}: {first}")
			conn.close()
			return
		
		remote_username = first.split()[1]

		with peer_lock:
			peers[addr] = remote_username
		
		print(f"{addr} identified as user: {remote_username}")

	except Exception as e:
		print(f"Error during initial message with {addr}: {e}")
		conn.close()
		return

	try:
		while True:
			data = conn.recv(1024)
			if not data:
				break
			msg = data.decode('utf-8')

			print(f"[{peers[addr]}] {msg}")
	except Exception as e:
		print(f"Error handling peer (probably a disconnect) {addr}: {e}")
	finally:
		with peer_lock:
			peer_sockets.remove(conn)
		conn.close()

def listener_thread(port, username):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	s.bind(('0.0.0.0', port))
	s.listen()
	print(f"LISTENING ON PORT {port}")
	while True:
		conn, addr = s.accept()
		with peer_lock:
			peer_sockets.append(conn)
		threading.Thread(target=handle_peer, args=(conn, addr, username), daemon=True).start()

def connect_to_peer(ip, port, username):
	with peer_lock:
		if (ip, port) in peer_addrs:
			return
	
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		s.connect((ip, port))

		with peer_lock:
			peer_sockets.append(s)
			peer_addrs.add((ip, port))
		threading.Thread(target=handle_peer, args=(s, (ip, port), username), daemon=True).start()
	except Exception as e:
		print(f"Failed to connect to peer {ip}:{port} - {e}")
		s.close()

def sender_loop():
	print("/q to exit")
	while True:
		msg = input()

		if msg == "/q":
			print("EXITING PROGRAM")
			break

		msg_data = (msg).encode('utf-8')
		with peer_lock:
			for p in peer_sockets:
				p.sendall(msg_data)

def discovery_broadcast_thread(listen_port, username):
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
	while True:
		msg = f"DISCOVER {username} {listen_port}"
		s.sendto(msg.encode('utf-8'), ('<broadcast>', 5000))
		time.sleep(3)

def discovery_listener_thread(username):
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	s.bind(('', 5000))
	print(f"LISTENING FOR DISCOVERY MESSAGES ON PORT 5000")
	while True:
		try:
			data, addr = s.recvfrom(1024)
		except Exception as e:
			print(f"Error receiving discovery message: {e}")
			continue
		
		try:
			text = data.decode('utf-8').strip()
		except Exception as e:
			print(f"Error decoding discovery message: {e}")
			continue

		if not text.startswith("DISCOVER"):
			continue

		_, remote_username, remote_port = text.split()
		
		if (username <= remote_username):
			continue
		
		connect_to_peer(addr[0], int(remote_port), username)

# MAIN STUFF
arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("--port", type=int, required=True)
arg_parser.add_argument("--username", type=str, required=True)
arg_parser.add_argument("--password", type=str, required=True)
args = arg_parser.parse_args()

if (args.username in USER_DATA and USER_DATA[args.username] == args.password):
	print("Logged in as " + args.username)
else:
	print("Invalid username or password")
	exit()

threading.Thread(target=listener_thread, args=(args.port, args.username), daemon=True).start() # fun fact, args is a tuple so I have to add a comma at the end (what an awful language quirk,)
threading.Thread(target=discovery_broadcast_thread, args=(args.port, args.username), daemon=True).start()
threading.Thread(target=discovery_listener_thread, args=(args.username,), daemon=True).start()

sender_loop()