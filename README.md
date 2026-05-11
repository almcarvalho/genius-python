# Genius Game Automation using Arduino and Python

## Overview

This project demonstrates the automation of a classic **Genius (Simon Says)** game using:

- Arduino Uno
- Python
- Computer Vision concepts
- Serial communication
- Relay-based button actuation

The objective was to challenge the computer to play the physical game automatically by recognizing the visual sequences and reproducing the correct actions electronically.

---

## Original Genius Game

Genius game with Arduino using buttons, LEDs, and sounds.

<img width="508" height="637" alt="Genius Game" src="https://github.com/user-attachments/assets/10a41336-2bd7-410a-bb55-1f4103dfd3d9" />

---

## Project Motivation

> “While I was opening it to fix it, I decided to challenge myself and make the computer play this game.”

This project became an experimental platform for exploring:

---

## Arduino Automation Layer

Instead of pressing the buttons manually, the **Arduino Uno** performs the interactions electronically.

The board receives commands through the serial port and activates relays connected to the physical buttons of the Genius game.

<img width="498" height="652" alt="Arduino Automation" src="https://github.com/user-attachments/assets/c04a8489-9a92-40da-b30d-9741444f2dce" />

---

## Python Recognition System

The Python application is responsible for:

- Recognizing the game sequences
- Processing visual patterns
- Sending commands to Arduino
- Automating gameplay

<img width="590" height="637" alt="Python Recognition" src="https://github.com/user-attachments/assets/b7900e3e-7dda-452f-9be9-248fa64a7cd1" />

---

## System Architecture

### Python Layer

Responsible for:

- Sequence recognition
- Image/video processing
- Decision-making
- Serial communication

### Arduino Layer

Responsible for:

- Relay activation
- Physical button control
- Hardware interaction
- Real-time execution

---

## Technologies Used

### Software

- Python
- Serial Communication
- Computer Vision Concepts

### Hardware

- Arduino Uno
- Relays
- LEDs
- Physical Genius Game

---

## Educational and Research Value

This project demonstrates practical applications involving:

- Embedded systems
- Hardware automation
- Real-time interaction
- Intelligent systems
- Human-machine interfaces

It can serve as an introductory or experimental project for students interested in:

- Robotics
- IoT
- Computer Engineering
- Artificial Intelligence
- Automation Systems

---

## Future Improvements

Possible future enhancements include:

- Deep Learning sequence recognition
- Wireless communication
- ESP32 integration
- Camera-based detection
- Faster response systems
- Autonomous adaptive gameplay

---
