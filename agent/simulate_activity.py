from pynput.keyboard import Key, Controller
import time

keyboard = Controller()

print("Simulating typing...")
time.sleep(2) # Wait for listener to start
for char in "Hello World":
    keyboard.press(char)
    keyboard.release(char)
    time.sleep(0.1)

keyboard.press(Key.space)
keyboard.release(Key.space)

print("Typing complete.")
