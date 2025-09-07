# Dumbledore's Office 🧙‍♂️


## Table of Contents

  - Introduction
  - Project Overview
  - Features
  - Design Patterns
  - Testing
  - Contributors


## Introduction ⚡️


Welcome to Dumbledore's Office - an interactive virtual space that brings to life one of the most iconic locations from the Harry Potter universe. This project was developed as part of McGill University's COMP 303: Software Design course.


In this virtual world, players can experience fundamental elements of the wizarding world through thoughtfully designed interactions and atmospheric details. The office captures the essence of Hogwarts with carefully crafted magical elements, dynamic objects, and character interactions powered by AI.


## Project Overview


Dumbledore's Office serves as both an educational and immersive environment where players can:


  - Participate in a Sorting Ceremony to determine their Hogwarts house
  - Interact with magical portraits of notable wizarding world characters
  - Discover and read magical books from the bookshelf
  - Witness Fawkes the phoenix burn and regenerate
  - Explore magical memories through the Pensieve


The room adapts to the player's assigned house, and every interactive element deepens the connection to the wizarding world.


## Features


### Sorting Hat Ceremony


Players begin their journey with a mandatory Sorting Ceremony. The Sorting Hat asks a series of character-defining questions and assigns players to one of the four Hogwarts houses: Gryffindor, Hufflepuff, Ravenclaw, or Slytherin. Once assigned, the room adapts to the player's house, changing the central rug's color and emblem.


### Interactive Magical Portraits


Four magical portraits adorn the office walls, featuring Dumbledore, Hermione, Professor Snape, and Peeves the ghost. Players can engage in dynamic conversations with these characters through a chat interface powered by an AI language model. Each portrait has a unique personality and offers insights into the wizarding world.


### Magical Bookshelf


A dark wooden bookshelf contains various magical texts. Players can select books that magically float from the shelf, providing personalized descriptions and lore about the wizarding world.


### Dumbledore's Pensieve


The Pensieve allows players to explore vivid descriptions of iconic moments from the wizarding world. Players can ask questions about these memories to learn more about their significance and context.


### Fawkes the Phoenix


Dumbledore's prized phoenix perches near his desk. When players interact with Fawkes, they can witness his dramatic rebirth in flames, a key element of phoenix lore.


### Dynamic Environment


The room features floating candles, a house-themed rug, and other atmospheric elements that create an immersive magical experience. The environment responds to player actions, with interactive objects glowing when approached.


## Design Patterns


The project implements several key design patterns to ensure clean, maintainable code:


### 1. Strategy Pattern


Implemented through the ConversationStrategy abstract base class and its character-specific subclasses. This pattern defines a family of algorithms for generating character-appropriate dialogue responses. Each character (Dumbledore, Hermione, Snape, Peeves) and the Pensieve has its own conversation strategy that determines its personality and response style. Additionally, each strategy has house-specific variants (Gryffindor, Hufflepuff, Ravenclaw, Slytherin) that adapt the dialogue tone based on the player's assigned house.


The ChatBot class uses these strategies to generate contextually appropriate responses by combining:


  - Character-specific opening messages defined in each strategy
  - House-specific tone adaptations
  - Common dialogue constraints (length limits, formatting)


This approach allows for consistent interaction mechanics while providing unique dialogue experiences tailored to both the character and the player's house affiliation.


### 2. Observer Pattern


Implemented through a dual observer system to track different aspects of the game state:


**Position Observers (PositionObserver interface):**


  - Interactive elements like portraits, the bookshelf, phoenix, and sorting hat implement this interface
  - Observer objects maintain a list of active positions where they should respond   to player presence
  - When a player moves to a new position, DumbledoresOffice notifies all position observers
  - Objects display text bubbles and become interactive when the player is within their active range
  - Includes default implementation that shows/hides text bubbles and displays introductory messages


**House Observers (HouseObserver interface):**


  - Room elements that change based on the player's house assignment (like the rug and portraits)
  - When the Sorting Hat assigns a house, DumbledoresOffice notifies all house observers
  - The rug changes color and pattern to match the assigned house
  - Chat objects (portraits and pensieve) update their conversation strategies to provide house-specific dialogue


The DumbledoresOffice class acts as the central subject that maintains collections of both observer types and handles notification when state changes occur. This separation of concerns allows objects to respond appropriately to different types of state changes while centralizing the notification logic.


### 3. Singleton Pattern


Implemented in two key classes to ensure consistent state management and efficient resource utilization:


**ChatBot Singleton:**

  - Uses a private static __instance field to store the single instance
  - Overrides __new__ to return the existing instance when already created
  - Provides a static get_instance() method as the global access point
  - Manages API key and LLM communication centrally, preventing duplicate connections
  - All dialogue generation is routed through this single instance, ensuring consistent communication patterns


**DumbledoresOffice Singleton:**

   - Similarly implements the Singleton pattern with a private __instance field and get_instance() method
  - Serves as the central state manager for the entire game environment
   - Maintains the current player, house assignment, and observer collections
   - Provides global access to room state for all interactive objects
   - Acts as the central subject in the Observer pattern, notifying observers of state changes


This pattern ensures that these critical resources are instantiated only once, providing consistent behavior, centralized state management, and efficient resource utilization - particularly important for the ChatBot's API calls, which could be costly if duplicated.


### 4. Flyweight Pattern


Implemented in the Book and Bookshelf classes to optimize memory usage and reduce costly API calls:


**Book as Flyweight:**


  - Books maintain a static flyweightStore list that caches previously created Book instances
  - The static get_book(title) method acts as a factory method for retrieving or creating books
  - When a player requests a book through the bookshelf, the method first checks if the book exists in the cache
  - If found, the existing book instance is returned without requiring another API call
  - If not found, only then is a new book created with a custom description generated via the ChatBot API


**Shared vs. Unique State:**


  - Shared intrinsic state: title and description (stored in the flyweight)
  - Unique extrinsic state: position (randomly assigned each time a book is placed in the world)
  - Image representation (randomly selected from 5 variants)




**Client-Side Management:**


  - The Bookshelf acts as the client of the Flyweight pattern
  - It requests books through Book.get_book(title) without needing to know if a book is new or cached
  - Then adds the returned book to the game grid at its assigned position


This pattern significantly improves performance by:


  - Eliminating redundant API calls when the same book is requested multiple times
  - Reducing memory usage by sharing common book data
  - Separating the intrinsic state (book content) from extrinsic state (position in the world)



## Test Coverage


Tests are organized to mirror the project structure, with one test file per project class. Key testing areas include (but not limited to):



**Comprehensive testing of all implemented design patterns:**


   - **Singleton Pattern:** Tests for ChatBot and DumbledoresOffice verifying single instance behavior
  - **Flyweight Pattern:** Thorough testing of Book caching and reuse in the flyweightStore
  - **Observer Pattern:** Tests for notification mechanisms when player position or house changes
  - **Strategy Pattern:** Tests for proper dialogue generation based on character and house


**Comprehensive Fixtures:**


  - Makes extensive use of pytest fixtures for clean, independent tests
  - Mocks external dependencies (API calls, randomization)
  - Isolates components for true unit testing
  - Tracks method calls to verify correct object interactions
  - Reset game state between tests for isolation

Each test follows the Arrange-Act-Assert pattern and focuses on a single aspect of functionality to ensure clear, maintainable test cases.


## Contributors


  - Allison Meikle
  - Filip Snítil
  - Murad Novruzov


---

*This project was created for educational purposes as part of McGill University's COMP 303: Software Design course. It draws inspiration from the Harry Potter series created by J.K. Rowling. We acknowledge the ongoing public discussions regarding statements made by the author, particularly concerning gender identity, and encourage an informed understanding of these discussions.*
