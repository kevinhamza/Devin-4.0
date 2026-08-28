# servers/ai_conversation_server.py

import socket
import threading
import time
from config import global_settings, ai_config
from transformers import pipeline

# Initialize NLP model pipeline
nlp_pipeline = pipeline("conversational", model=ai_config.NLP_MODEL_NAME)

# Function to handle client conversation
def handle_client_connection(client_socket):
    try:
        while True:
            message = client_socket.recv(global_settings.BUFFER_SIZE).decode('utf-8')
            if not message:
                break

            # Process the received message through the NLP model
            response = nlp_pipeline(message)[0]['generated_text']
            client_socket.send(response.encode('utf-8'))

    except Exception as e:
        print(f"Error handling client connection: {e}")
    finally:
        client_socket.close()

# Function to start the AI conversation server
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((global_settings.HOST, global_settings.PORT))
    server.listen(global_settings.MAX_CONNECTIONS)
    print(f"AI Conversation Server started on {global_settings.HOST}:{global_settings.PORT}")

    while True:
        client_socket, client_address = server.accept()
        print(f"Connection established with {client_address}")
        client_handler = threading.Thread(target=handle_client_connection, args=(client_socket,))
        client_handler.start()

# Entry point for the AI Conversation server
if __name__ == "__main__":
    start_server()
