# Dumbledore's Office (Virtual World Project)
This project is an interactive room design for COMP 303 (Software Design), McGill University, Winter 2025. It contributes to a shared class-wide virtual world by implementing a themed space (Dumbledore’s Office) where players can explore, interact with magical objects, and trigger events. The proposal and implementation emphasize both front-end interactivity (navigable tiles, decor, and interactive objects such as enchanted books and artifacts) and back-end logic (puzzle mechanics, NPC dialogue, and environment state changes). The design leverages four object-oriented design patterns, with Singleton and Strategy concretely implemented to manage global game state and flexible NPC/interaction behaviors, and Observer and Command applied to synchronize room changes and encapsulate user-triggered actions. This assignment demonstrates skills in software architecture, interactive simulation design, application of design patterns to game logic, and integration of back-end logic with front-end interactivity in a collaborative codebase.

## Project Structure 
- `303MUD`: Base code for the game, written by the course instructor and provided to all students.
- `COMP303_Project`: Our group repository with all of the project code.
  - Contains a README.md with more specific information about our project, the interactions available, and the design patterns used in the implementation. 

## Project Usage
The game can be played either on a local server (single-player) or on a remote server (multi-player). The following steps need to be done in the terminal **from the dumbledores-office' directory**. Make sure you are running the game in an environment where the following packages are installed: `python-dotenv`, `requests`, `websocket-client`, `pygame`, and `Pillow`.

1. In order to interact with the chatbots throughout the room, you will need to [create an OpenRouter API key](https://openrouter.ai/docs/api-reference/authentication, and save it in '/dumbledores-office/COMP303_Project/.env'.
2. To launch the game server, run the following command: `python3 -m 303MUD.client_local`.
3. Once the game launches, use the arrow keys to move towards the house with the purple roof on the bottom left. Walk up to the door and press the up arrow to enter the house.
5. Once inside the house, you can explore our world however you like! 
